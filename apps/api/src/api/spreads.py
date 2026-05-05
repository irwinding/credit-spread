from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import LegSnapshot, OptionLeg, Spread, SpreadSnapshot
from ..schemas import SnapshotPoint, SpreadCreate, SpreadHistory, SpreadOut, SpreadPatch

router = APIRouter(prefix="/spreads", tags=["spreads"])


def _attach_latest_snapshot(db: Session, spreads: list[Spread]) -> None:
    if not spreads:
        return
    sids = [s.id for s in spreads]
    rows = db.scalars(
        select(SpreadSnapshot)
        .where(SpreadSnapshot.spread_id.in_(sids))
        .order_by(SpreadSnapshot.spread_id.asc(), SpreadSnapshot.ts.desc())
    ).all()
    latest_by_sid: dict = {}
    for r in rows:
        if r.spread_id not in latest_by_sid:
            latest_by_sid[r.spread_id] = r
    for spread in spreads:
        r = latest_by_sid.get(spread.id)
        if r is not None:
            spread.last_pnl = r.pnl_unrealised  # type: ignore[attr-defined]
            spread.last_spread_mark = r.spread_mark  # type: ignore[attr-defined]
            spread.last_underlying_price = r.underlying_price  # type: ignore[attr-defined]
            spread.last_snapshot_at = r.ts  # type: ignore[attr-defined]
        spread.stop_loss_breached = _is_breached(  # type: ignore[attr-defined]
            getattr(spread, "last_pnl", None), spread.net_credit, spread.stop_loss_pct
        )


def _is_breached(
    last_pnl: Decimal | None,
    net_credit: Decimal | None,
    stop_loss_pct: Decimal | None,
) -> bool:
    if last_pnl is None or net_credit is None or stop_loss_pct is None:
        return False
    threshold = -(stop_loss_pct / Decimal(100)) * net_credit
    return last_pnl <= threshold


def _attach_latest_marks(db: Session, spreads: list[Spread]) -> None:
    leg_ids = [leg.id for s in spreads for leg in s.legs]
    if not leg_ids:
        return
    latest_by_leg: dict[int, LegSnapshot] = {}
    rows = db.scalars(
        select(LegSnapshot)
        .where(LegSnapshot.leg_id.in_(leg_ids))
        .order_by(LegSnapshot.leg_id.asc(), LegSnapshot.ts.desc())
    ).all()
    for r in rows:
        if r.leg_id not in latest_by_leg:
            latest_by_leg[r.leg_id] = r
    for spread in spreads:
        for leg in spread.legs:
            r = latest_by_leg.get(leg.id)
            if r is not None:
                leg.last_mark = r.mid  # type: ignore[attr-defined]
                leg.last_bid = r.bid  # type: ignore[attr-defined]
                leg.last_ask = r.ask  # type: ignore[attr-defined]
                leg.last_mark_ts = r.ts  # type: ignore[attr-defined]


@router.get("", response_model=list[SpreadOut])
def list_spreads(include_closed: bool = False, db: Session = Depends(get_db)):
    stmt = select(Spread).options(selectinload(Spread.legs)).order_by(Spread.opened_at.desc())
    if not include_closed:
        stmt = stmt.where(Spread.closed_at.is_(None))
    spreads = list(db.scalars(stmt).all())
    _attach_latest_marks(db, spreads)
    _attach_latest_snapshot(db, spreads)
    return spreads


@router.get("/{spread_id}", response_model=SpreadOut)
def get_spread(spread_id: uuid.UUID, db: Session = Depends(get_db)):
    spread = db.scalars(
        select(Spread).options(selectinload(Spread.legs)).where(Spread.id == spread_id)
    ).first()
    if spread is None:
        raise HTTPException(404, "spread not found")
    _attach_latest_marks(db, [spread])
    _attach_latest_snapshot(db, [spread])
    return spread


@router.get("/{spread_id}/history", response_model=SpreadHistory)
def get_history(spread_id: uuid.UUID, db: Session = Depends(get_db)):
    if not db.get(Spread, spread_id):
        raise HTTPException(404, "spread not found")
    rows = db.scalars(
        select(SpreadSnapshot)
        .where(SpreadSnapshot.spread_id == spread_id)
        .order_by(SpreadSnapshot.ts.asc())
    ).all()
    return SpreadHistory(
        spread_id=spread_id,
        points=[
            SnapshotPoint(
                ts=r.ts,
                spread_mark=r.spread_mark,
                pnl_unrealised=r.pnl_unrealised,
                underlying_price=r.underlying_price,
            )
            for r in rows
        ],
    )


@router.post("", response_model=SpreadOut, status_code=201)
def create_manual_spread(payload: SpreadCreate, db: Session = Depends(get_db)):
    legs = db.scalars(
        select(OptionLeg).where(OptionLeg.moomoo_position_id.in_(payload.leg_position_ids))
    ).all()
    if len(legs) != len(payload.leg_position_ids):
        raise HTTPException(400, "one or more leg position_ids not found")
    if not legs:
        raise HTTPException(400, "no legs supplied")

    underlying = legs[0].underlying
    expiry = legs[0].expiry
    if any(l.underlying != underlying or l.expiry != expiry for l in legs):
        raise HTTPException(400, "manual spread legs must share underlying and expiry")

    shorts = [l for l in legs if l.quantity < 0]
    longs = [l for l in legs if l.quantity > 0]
    short_strike = shorts[0].strike if shorts else None
    long_strike = longs[0].strike if longs else None
    width = (
        abs(long_strike - short_strike) if short_strike is not None and long_strike is not None
        else None
    )

    spread = Spread(
        underlying=underlying,
        expiry=expiry,
        spread_type="OTHER",
        short_strike=short_strike,
        long_strike=long_strike,
        width=width,
        quantity=abs(min((l.quantity for l in legs), key=abs, default=1)),
        opened_at=datetime.now(timezone.utc),
        detection_mode="MANUAL",
        user_locked=True,
    )
    db.add(spread)
    db.flush()

    for leg in legs:
        leg.spread_id = spread.id

    db.commit()
    db.refresh(spread)
    return spread


@router.patch("/{spread_id}", response_model=SpreadOut)
def patch_spread(spread_id: uuid.UUID, payload: SpreadPatch, db: Session = Depends(get_db)):
    spread = db.scalars(
        select(Spread).options(selectinload(Spread.legs)).where(Spread.id == spread_id)
    ).first()
    if spread is None:
        raise HTTPException(404, "spread not found")

    if payload.leg_position_ids is not None:
        for leg in list(spread.legs):
            leg.spread_id = None
        new_legs = db.scalars(
            select(OptionLeg).where(OptionLeg.moomoo_position_id.in_(payload.leg_position_ids))
        ).all()
        if len(new_legs) != len(payload.leg_position_ids):
            raise HTTPException(400, "one or more leg position_ids not found")
        for leg in new_legs:
            leg.spread_id = spread.id
        spread.detection_mode = "MANUAL"
        spread.user_locked = True

    if payload.user_locked is not None:
        spread.user_locked = payload.user_locked

    if "stop_loss_pct" in payload.model_fields_set:
        spread.stop_loss_pct = payload.stop_loss_pct

    db.commit()
    db.refresh(spread)
    return spread
