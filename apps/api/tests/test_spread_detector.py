from datetime import date
from decimal import Decimal

from src.spread_detector import LegInput, detect_spreads


def leg(
    pos_id: str,
    underlying: str,
    opt: str,
    strike: float,
    qty: int,
    expiry: date = date(2026, 6, 19),
    entry_price: float | None = None,
) -> LegInput:
    return LegInput(
        moomoo_position_id=pos_id,
        underlying=underlying,
        option_symbol=f"{underlying}{expiry:%y%m%d}{opt}{int(strike)}",
        option_type=opt,
        strike=Decimal(str(strike)),
        expiry=expiry,
        quantity=qty,
        entry_price=Decimal(str(entry_price)) if entry_price is not None else None,
    )


def test_detects_bull_put_spread():
    legs = [
        leg("p1", "SPY", "PUT", 100, -1, entry_price=2.50),
        leg("p2", "SPY", "PUT", 95, 1, entry_price=1.20),
    ]
    spreads = detect_spreads(legs)
    assert len(spreads) == 1
    s = spreads[0]
    assert s.spread_type == "BULL_PUT"
    assert s.underlying == "SPY"
    assert s.short_strike == Decimal("100")
    assert s.long_strike == Decimal("95")
    assert s.width == Decimal("5")
    assert s.quantity == 1
    # net credit in dollars = (2.50 - 1.20) * 100 * 1 contract = 130
    assert s.net_credit == Decimal("130.00")
    assert {leg.moomoo_position_id for leg in s.legs} == {"p1", "p2"}


def test_detects_bear_call_spread():
    legs = [
        leg("c1", "SPY", "CALL", 110, -2, entry_price=3.00),
        leg("c2", "SPY", "CALL", 115, 2, entry_price=1.80),
    ]
    spreads = detect_spreads(legs)
    assert len(spreads) == 1
    s = spreads[0]
    assert s.spread_type == "BEAR_CALL"
    assert s.short_strike == Decimal("110")
    assert s.long_strike == Decimal("115")
    assert s.width == Decimal("5")
    assert s.quantity == 2
    # (3.00 - 1.80) * 100 * 2 contracts = 240
    assert s.net_credit == Decimal("240.00")


def test_detects_multiple_independent_spreads():
    legs = [
        leg("a", "SPY", "PUT", 100, -1),
        leg("b", "SPY", "PUT", 95, 1),
        leg("c", "QQQ", "CALL", 400, -1),
        leg("d", "QQQ", "CALL", 405, 1),
    ]
    spreads = detect_spreads(legs)
    assert len(spreads) == 2
    types = {s.spread_type for s in spreads}
    assert types == {"BULL_PUT", "BEAR_CALL"}


def test_unpaired_leg_is_not_grouped():
    legs = [
        leg("p1", "SPY", "PUT", 100, -1),
        leg("p2", "SPY", "PUT", 95, 1),
        leg("p3", "SPY", "PUT", 90, 1),  # naked long, no matching short
    ]
    spreads = detect_spreads(legs)
    assert len(spreads) == 1
    grouped_ids = {leg.moomoo_position_id for leg in spreads[0].legs}
    assert "p3" not in grouped_ids


def test_pairs_use_adjacent_strikes():
    # Two short puts at 100 and 105, two long puts at 95 and 100 should pair tightest.
    legs = [
        leg("s100", "SPY", "PUT", 100, -1),
        leg("s105", "SPY", "PUT", 105, -1),
        leg("l95", "SPY", "PUT", 95, 1),
        leg("l100", "SPY", "PUT", 100, 1),
    ]
    spreads = detect_spreads(legs)
    assert len(spreads) == 2
    widths = sorted(s.width for s in spreads)
    assert widths == [Decimal("5"), Decimal("5")]


def test_quantity_must_match_to_pair():
    legs = [
        leg("s", "SPY", "PUT", 100, -2),
        leg("l", "SPY", "PUT", 95, 1),  # wrong qty
    ]
    spreads = detect_spreads(legs)
    assert spreads == []


def test_different_expiry_not_paired():
    legs = [
        leg("a", "SPY", "PUT", 100, -1, expiry=date(2026, 6, 19)),
        leg("b", "SPY", "PUT", 95, 1, expiry=date(2026, 7, 17)),
    ]
    assert detect_spreads(legs) == []


def test_user_locked_legs_excluded_from_auto_pairing():
    # Pre-locked spread holds p1+p2; auto-detect must not regroup them.
    locked_leg_ids = {"p1", "p2"}
    legs = [
        leg("p1", "SPY", "PUT", 100, -1),
        leg("p2", "SPY", "PUT", 95, 1),
        leg("p3", "SPY", "PUT", 90, -1),
        leg("p4", "SPY", "PUT", 85, 1),
    ]
    spreads = detect_spreads(legs, locked_leg_ids=locked_leg_ids)
    assert len(spreads) == 1
    grouped = {leg.moomoo_position_id for leg in spreads[0].legs}
    assert grouped == {"p3", "p4"}


def test_classifies_unusual_structure_as_other():
    # Same-side same-expiry pair, e.g. two longs — not a credit spread.
    legs = [
        leg("a", "SPY", "PUT", 100, 1),
        leg("b", "SPY", "PUT", 95, 1),
    ]
    spreads = detect_spreads(legs)
    assert spreads == []  # no opposite-signed pair, nothing to group
