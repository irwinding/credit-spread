"""Thin wrapper around the moomoo (Futu) OpenAPI.

OpenD must be running locally; we connect over its local socket. The wrapper
hides futu-api's pandas-DataFrame return values and exposes plain dicts /
dataclasses keyed off our internal field names.

futu-api is synchronous; callers that live in async code should use
``asyncio.to_thread`` to keep the event loop unblocked.
"""

from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RawLeg:
    moomoo_position_id: str
    underlying: str
    option_symbol: str   # raw moomoo code, e.g. "US.SPY250620P100000"
    option_type: str     # CALL | PUT
    strike: Decimal
    expiry: date
    quantity: int        # signed (+long, -short)
    entry_price: Decimal | None
    entry_at: datetime | None


@dataclass
class Quote:
    symbol: str
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None

    @property
    def mid(self) -> Decimal | None:
        if self.bid is not None and self.ask is not None:
            return (self.bid + self.ask) / Decimal(2)
        return self.last


# Moomoo option code: <MARKET>.<UNDERLYING><YYMMDD><C|P><STRIKE_x1000>
# Example: US.SPY250620P00100000 (strike 100.000)
_OPT_RE = re.compile(
    r"^(?P<market>[A-Z]+)\.(?P<und>[A-Z]+)(?P<y>\d{2})(?P<m>\d{2})(?P<d>\d{2})"
    r"(?P<cp>[CP])(?P<strike>\d+)$"
)


def parse_option_code(code: str) -> tuple[str, str, date, Decimal]:
    """Return (underlying, option_type, expiry, strike) from a moomoo option code.

    Raises ValueError if the code doesn't look like an option.
    """
    m = _OPT_RE.match(code)
    if not m:
        raise ValueError(f"not an option code: {code}")
    yy, mm, dd = int(m["y"]), int(m["m"]), int(m["d"])
    year = 2000 + yy
    expiry = date(year, mm, dd)
    strike_raw = m["strike"]
    # moomoo encodes strike as 1000x integer
    strike = Decimal(strike_raw) / Decimal(1000)
    opt_type = "CALL" if m["cp"] == "C" else "PUT"
    return m["und"], opt_type, expiry, strike


class MoomooClient:
    """Open/close Futu contexts on demand."""

    def __init__(
        self,
        host: str,
        port: int,
        trade_pwd: str = "",
        security_firm: str = "FUTUSG",
        trd_market: str = "US",
    ):
        self.host = host
        self.port = port
        self.trade_pwd = trade_pwd
        self.security_firm = security_firm
        self.trd_market = trd_market

    @contextmanager
    def quote_ctx(self):
        from futu import OpenQuoteContext

        ctx = OpenQuoteContext(host=self.host, port=self.port)
        try:
            yield ctx
        finally:
            ctx.close()

    @contextmanager
    def trade_ctx(self):
        from futu import OpenSecTradeContext, SecurityFirm, TrdMarket

        firm = getattr(SecurityFirm, self.security_firm, None)
        if firm is None:
            raise RuntimeError(
                f"unknown MOOMOO_SECURITY_FIRM={self.security_firm!r}; "
                "expected one of FUTUSG, FUTUINC, FUTUSECURITIES, FUTUAU, FUTUJP, FUTUCA, FUTUMY"
            )
        market = getattr(TrdMarket, self.trd_market, None)
        if market is None:
            raise RuntimeError(f"unknown MOOMOO_TRD_MARKET={self.trd_market!r}")
        ctx = OpenSecTradeContext(
            filter_trdmarket=market,
            host=self.host,
            port=self.port,
            security_firm=firm,
        )
        try:
            yield ctx
        finally:
            ctx.close()

    def list_option_positions(self) -> list[RawLeg]:
        """Return open option positions, normalised to RawLeg."""
        with self.trade_ctx() as ctx:
            ret, df = ctx.position_list_query()
            if ret != 0:
                raise RuntimeError(f"position_list_query failed: {df}")

        legs: list[RawLeg] = []
        for row in df.to_dict(orient="records"):
            code = row.get("code", "")
            try:
                underlying, opt_type, expiry, strike = parse_option_code(code)
            except ValueError:
                continue  # skip non-option positions

            qty_abs = abs(int(row.get("qty", 0) or 0))
            side = (row.get("position_side") or "").upper()
            qty_signed = qty_abs if side == "LONG" else -qty_abs

            cost = row.get("cost_price")
            entry_price = Decimal(str(cost)) if cost not in (None, "", 0) else None

            legs.append(
                RawLeg(
                    moomoo_position_id=str(row.get("position_id") or code),
                    underlying=underlying,
                    option_symbol=code,
                    option_type=opt_type,
                    strike=strike,
                    expiry=expiry,
                    quantity=qty_signed,
                    entry_price=entry_price,
                    entry_at=_parse_dt(row.get("create_time")),
                )
            )
        return legs

    def get_quote(self, code: str) -> Quote:
        with self.quote_ctx() as ctx:
            ret, df = ctx.get_market_snapshot([code])
            if ret != 0 or df.empty:
                raise RuntimeError(f"get_market_snapshot({code}) failed: {df}")
        row: dict[str, Any] = df.iloc[0].to_dict()
        return Quote(
            symbol=code,
            bid=_dec(row.get("bid_price")),
            ask=_dec(row.get("ask_price")),
            last=_dec(row.get("last_price")),
        )

    def get_underlying_price(self, ticker: str, market: str = "US") -> Decimal:
        code = f"{market}.{ticker}"
        q = self.get_quote(code)
        if q.last is None:
            raise RuntimeError(f"no last price for {code}")
        return q.last


def _dec(x: Any) -> Decimal | None:
    if x is None or x == "" or x == 0:
        return None
    try:
        return Decimal(str(x))
    except Exception:
        return None


def _parse_dt(x: Any) -> datetime | None:
    if not x:
        return None
    try:
        # moomoo timestamps are typically "YYYY-MM-DD HH:MM:SS"
        return datetime.fromisoformat(str(x)).replace(tzinfo=timezone.utc)
    except Exception:
        return None
