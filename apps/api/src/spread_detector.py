"""Pair raw moomoo option legs into credit spreads.

The detector is intentionally pure (no DB / no IO) so it can be unit-tested in
isolation. Persistence happens in the snapshotter.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class LegInput:
    moomoo_position_id: str
    underlying: str
    option_symbol: str
    option_type: str  # "CALL" | "PUT"
    strike: Decimal
    expiry: date
    quantity: int  # signed (+long, -short)
    entry_price: Decimal | None = None


@dataclass
class DetectedSpread:
    underlying: str
    expiry: date
    spread_type: str  # "BULL_PUT" | "BEAR_CALL" | "OTHER"
    short_strike: Decimal
    long_strike: Decimal
    width: Decimal
    quantity: int  # always positive — number of contracts
    net_credit: Decimal | None
    legs: list[LegInput] = field(default_factory=list)


def detect_spreads(
    legs: list[LegInput],
    locked_leg_ids: set[str] | None = None,
) -> list[DetectedSpread]:
    """Pair short/long legs of equal quantity & adjacent strikes into spreads.

    Legs in `locked_leg_ids` are excluded — they belong to a user-locked spread
    that auto-detection must not touch.
    """
    locked = locked_leg_ids or set()
    pool = [l for l in legs if l.moomoo_position_id not in locked]

    # Group by (underlying, expiry, option_type)
    groups: dict[tuple[str, date, str], list[LegInput]] = defaultdict(list)
    for l in pool:
        groups[(l.underlying, l.expiry, l.option_type)].append(l)

    detected: list[DetectedSpread] = []

    for (underlying, expiry, opt_type), group in groups.items():
        shorts = sorted([l for l in group if l.quantity < 0], key=lambda l: l.strike)
        longs = sorted([l for l in group if l.quantity > 0], key=lambda l: l.strike)

        # Pair greedily by closest strike with matching quantity.
        used_long_idxs: set[int] = set()
        for s in shorts:
            best_i: int | None = None
            best_dist: Decimal | None = None
            for i, l in enumerate(longs):
                if i in used_long_idxs:
                    continue
                if l.quantity != -s.quantity:  # magnitudes & opposite signs must match
                    continue
                dist = abs(l.strike - s.strike)
                if dist == 0:
                    continue  # same strike isn't a vertical spread
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_i = i
            if best_i is None:
                continue
            l = longs[best_i]
            used_long_idxs.add(best_i)

            short_strike = s.strike
            long_strike = l.strike
            width = abs(long_strike - short_strike)
            qty = abs(s.quantity)

            spread_type = _classify(opt_type, short_strike, long_strike)
            net_credit = _compute_net_credit(s.entry_price, l.entry_price, qty)

            detected.append(
                DetectedSpread(
                    underlying=underlying,
                    expiry=expiry,
                    spread_type=spread_type,
                    short_strike=short_strike,
                    long_strike=long_strike,
                    width=width,
                    quantity=qty,
                    net_credit=net_credit,
                    legs=[s, l],
                )
            )

    return detected


def _classify(option_type: str, short_strike: Decimal, long_strike: Decimal) -> str:
    if option_type == "PUT" and short_strike > long_strike:
        return "BULL_PUT"
    if option_type == "CALL" and short_strike < long_strike:
        return "BEAR_CALL"
    return "OTHER"


def _compute_net_credit(
    short_entry: Decimal | None, long_entry: Decimal | None, quantity: int
) -> Decimal | None:
    """Net credit in dollars across the whole position = max profit.

    (short_premium - long_premium) per share × 100 × number of contracts.
    """
    if short_entry is None or long_entry is None:
        return None
    return (short_entry - long_entry) * Decimal(100) * Decimal(quantity)
