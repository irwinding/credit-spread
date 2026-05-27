"""Snapshot job: pull positions from moomoo, group into spreads, persist marks."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import LegSnapshot, OptionLeg, Spread, SpreadSnapshot
from .moomoo_client import MoomooClient, Quote, RawLeg
from .spread_detector import LegInput, detect_spreads

logger = logging.getLogger(__name__)


def run_snapshot(db: Session, client: MoomooClient) -> int:
    """One snapshot iteration. Returns count of spread rows written."""
    raw_legs = client.list_option_positions()
    _upsert_legs(db, raw_legs)
    db.flush()

    locked_leg_ids = _locked_position_ids(db)

    leg_inputs = [
        LegInput(
            moomoo_position_id=l.moomoo_position_id,
            underlying=l.underlying,
            option_symbol=l.option_symbol,
            option_type=l.option_type,
            strike=l.strike,
            expiry=l.expiry,
            quantity=l.quantity,
            entry_price=l.entry_price,
        )
        for l in raw_legs
    ]
    detected = detect_spreads(leg_inputs, locked_leg_ids=locked_leg_ids)
    _upsert_auto_spreads(db, detected)
    db.flush()

    rows_written = 0
    ts = datetime.now(timezone.utc)

    open_spreads = db.scalars(select(Spread).where(Spread.closed_at.is_(None))).all()

    # Fetch each unique option symbol once per run.
    quote_cache: dict[str, Quote] = {}
    for spread in open_spreads:
        for leg in spread.legs:
            if leg.option_symbol in quote_cache:
                continue
            try:
                quote_cache[leg.option_symbol] = client.get_quote(leg.option_symbol)
            except Exception as exc:  # noqa: BLE001
                logger.warning("get_quote failed for %s: %s", leg.option_symbol, exc)

    # Persist per-leg snapshots from the cached quotes.
    for spread in open_spreads:
        for leg in spread.legs:
            q = quote_cache.get(leg.option_symbol)
            if q is None or q.mid is None:
                continue
            db.merge(
                LegSnapshot(
                    leg_id=leg.id,
                    ts=ts,
                    bid=q.bid,
                    ask=q.ask,
                    mid=q.mid,
                )
            )

    for spread in open_spreads:
        if not spread.legs:
            continue
        try:
            mark, pnl, und_price = _compute_marks(client, spread, quote_cache)
        except Exception as exc:  # noqa: BLE001
            logger.warning("snapshot failed for spread %s: %s", spread.id, exc)
            continue

        db.merge(
            SpreadSnapshot(
                spread_id=spread.id,
                ts=ts,
                spread_mark=mark,
                pnl_unrealised=pnl,
                underlying_price=und_price,
            )
        )
        rows_written += 1

    db.commit()
    logger.info("snapshot wrote %d rows at %s", rows_written, ts.isoformat())
    return rows_written


# ----- helpers -----

def _upsert_legs(db: Session, raw_legs: list[RawLeg]) -> None:
    # A leg's stable identity is its option_symbol (the moomoo contract code). An
    # account nets to a single position per contract, whereas moomoo's
    # position_id is NOT stable across sessions — matching on it would create a
    # fresh leg (and a duplicate spread) every time the id rotates.
    for r in raw_legs:
        existing = db.scalar(
            select(OptionLeg).where(OptionLeg.option_symbol == r.option_symbol)
        )
        if existing is None:
            db.add(
                OptionLeg(
                    moomoo_position_id=r.moomoo_position_id,
                    underlying=r.underlying,
                    option_symbol=r.option_symbol,
                    option_type=r.option_type,
                    strike=r.strike,
                    expiry=r.expiry,
                    quantity=r.quantity,
                    entry_price=r.entry_price,
                    entry_at=r.entry_at,
                )
            )
        else:
            existing.moomoo_position_id = r.moomoo_position_id
            existing.quantity = r.quantity
            existing.closed_at = None
            if existing.entry_price is None and r.entry_price is not None:
                existing.entry_price = r.entry_price


def _locked_position_ids(db: Session) -> set[str]:
    rows = db.execute(
        select(OptionLeg.moomoo_position_id)
        .join(Spread, Spread.id == OptionLeg.spread_id)
        .where(Spread.user_locked.is_(True))
    ).all()
    return {r[0] for r in rows}


def _upsert_auto_spreads(db: Session, detected) -> None:
    """Reconcile auto-detected spreads against existing AUTO rows.

    For each detected grouping, find an existing non-locked spread that owns
    the same set of leg position_ids; create one if missing.
    """
    for d in detected:
        leg_ids = {l.moomoo_position_id for l in d.legs}
        leg_objs = (
            db.scalars(
                select(OptionLeg).where(OptionLeg.moomoo_position_id.in_(leg_ids))
            ).all()
        )
        existing_spread_ids = {l.spread_id for l in leg_objs if l.spread_id is not None}
        spread = None
        for sid in existing_spread_ids:
            s = db.get(Spread, sid)
            if s is not None and not s.user_locked:
                spread = s
                break

        if spread is None:
            spread = Spread(
                underlying=d.underlying,
                expiry=d.expiry,
                spread_type=d.spread_type,
                short_strike=d.short_strike,
                long_strike=d.long_strike,
                width=d.width,
                quantity=d.quantity,
                net_credit=d.net_credit,
                opened_at=datetime.now(timezone.utc),
                detection_mode="AUTO",
                user_locked=False,
            )
            db.add(spread)
            db.flush()
        else:
            spread.spread_type = d.spread_type
            spread.short_strike = d.short_strike
            spread.long_strike = d.long_strike
            spread.width = d.width
            spread.quantity = d.quantity
            if spread.net_credit is None:
                spread.net_credit = d.net_credit

        for leg in leg_objs:
            leg.spread_id = spread.id


def _compute_marks(
    client: MoomooClient,
    spread: Spread,
    quote_cache: dict[str, Quote] | None = None,
) -> tuple[Decimal, Decimal, Decimal]:
    """Return (spread_mark, pnl_unrealised, underlying_price).

    spread_mark = sum(-qty_signed * mid)            -- cost to close
    pnl         = sum(qty_signed * (mid - entry)) * 100   -- dollars
    """
    cache = quote_cache or {}
    total_value_per_share = Decimal(0)
    total_pnl_per_share = Decimal(0)
    for leg in spread.legs:
        q = cache.get(leg.option_symbol) or client.get_quote(leg.option_symbol)
        mid = q.mid
        if mid is None:
            raise RuntimeError(f"no mid for {leg.option_symbol}")
        total_value_per_share += Decimal(leg.quantity) * mid
        if leg.entry_price is not None:
            total_pnl_per_share += Decimal(leg.quantity) * (mid - leg.entry_price)

    spread_mark = -total_value_per_share  # debit to close
    pnl_dollars = total_pnl_per_share * Decimal(100)
    und_price = client.get_underlying_price(spread.underlying)
    return spread_mark, pnl_dollars, und_price
