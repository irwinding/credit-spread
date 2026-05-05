from datetime import date
from decimal import Decimal

import pytest

from src.moomoo_client import parse_option_code


def test_parse_put_option():
    und, opt, expiry, strike = parse_option_code("US.SPY250620P00100000")
    assert und == "SPY"
    assert opt == "PUT"
    assert expiry == date(2025, 6, 20)
    assert strike == Decimal("100")


def test_parse_call_option_fractional_strike():
    und, opt, expiry, strike = parse_option_code("US.AAPL260117C00187500")
    assert und == "AAPL"
    assert opt == "CALL"
    assert expiry == date(2026, 1, 17)
    assert strike == Decimal("187.5")


def test_parse_rejects_equity():
    with pytest.raises(ValueError):
        parse_option_code("US.SPY")
