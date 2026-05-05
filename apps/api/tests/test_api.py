"""End-to-end API tests using SQLite + fake moomoo client (no OpenD needed)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db import Base, get_db
from src.main import app
from src.moomoo_client import Quote, RawLeg


class FakeMoomooClient:
    def __init__(self):
        self.legs: list[RawLeg] = []
        self.quotes: dict[str, Quote] = {}
        self.underlying_prices: dict[str, Decimal] = {}

    def list_option_positions(self) -> list[RawLeg]:
        return list(self.legs)

    def get_quote(self, code: str) -> Quote:
        return self.quotes[code]

    def get_underlying_price(self, ticker: str, market: str = "US") -> Decimal:
        return self.underlying_prices[ticker]


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    fake = FakeMoomooClient()
    app.state.moomoo_client = fake

    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db

    # Don't trigger the lifespan (would start the scheduler / connect to OpenD).
    c = TestClient(app)
    c.fake = fake  # type: ignore[attr-defined]
    yield c

    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_empty_spreads_list(client):
    r = client.get("/spreads")
    assert r.status_code == 200
    assert r.json() == []


def test_snapshot_creates_spread_and_history(client):
    fake = client.fake
    fake.legs = [
        RawLeg(
            moomoo_position_id="p_short",
            underlying="SPY",
            option_symbol="US.SPY260619P00100000",
            option_type="PUT",
            strike=Decimal("100"),
            expiry=date(2026, 6, 19),
            quantity=-1,
            entry_price=Decimal("2.50"),
            entry_at=None,
        ),
        RawLeg(
            moomoo_position_id="p_long",
            underlying="SPY",
            option_symbol="US.SPY260619P00095000",
            option_type="PUT",
            strike=Decimal("95"),
            expiry=date(2026, 6, 19),
            quantity=1,
            entry_price=Decimal("1.20"),
            entry_at=None,
        ),
    ]
    fake.quotes = {
        "US.SPY260619P00100000": Quote(
            "US.SPY260619P00100000", Decimal("0.40"), Decimal("0.50"), Decimal("0.45")
        ),
        "US.SPY260619P00095000": Quote(
            "US.SPY260619P00095000", Decimal("0.10"), Decimal("0.20"), Decimal("0.15")
        ),
    }
    fake.underlying_prices = {"SPY": Decimal("110.50")}

    r = client.post("/snapshot/run")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rows_written"] == 1

    spreads = client.get("/spreads").json()
    assert len(spreads) == 1
    s = spreads[0]
    assert s["spread_type"] == "BULL_PUT"
    assert s["underlying"] == "SPY"
    assert Decimal(s["short_strike"]) == Decimal("100")
    assert Decimal(s["long_strike"]) == Decimal("95")
    # (2.50 - 1.20) * 100 * 1 contract = 130
    assert Decimal(s["net_credit"]) == Decimal("130.00")

    sid = s["id"]
    history = client.get(f"/spreads/{sid}/history").json()
    assert len(history["points"]) == 1
    p = history["points"][0]
    # spread_mark = -(qty_short*mid_short + qty_long*mid_long) = -(-1*0.45 + 1*0.15) = 0.30
    assert Decimal(p["spread_mark"]) == Decimal("0.30")
    # pnl = ((-1)*(0.45-2.50) + (1)*(0.15-1.20)) * 100 = (2.05 + -1.05) * 100 = 100
    assert Decimal(p["pnl_unrealised"]) == Decimal("100.00")
    assert Decimal(p["underlying_price"]) == Decimal("110.50")


def test_legs_endpoint(client):
    fake = client.fake
    fake.legs = [
        RawLeg(
            moomoo_position_id="solo",
            underlying="QQQ",
            option_symbol="US.QQQ260619P00400000",
            option_type="PUT",
            strike=Decimal("400"),
            expiry=date(2026, 6, 19),
            quantity=-1,
            entry_price=Decimal("3.00"),
            entry_at=None,
        ),
    ]
    fake.quotes = {
        "US.QQQ260619P00400000": Quote(
            "US.QQQ260619P00400000", Decimal("2.90"), Decimal("3.00"), Decimal("2.95")
        ),
    }
    fake.underlying_prices = {"QQQ": Decimal("450.00")}

    client.post("/snapshot/run")
    legs = client.get("/legs").json()
    assert len(legs) == 1
    assert legs[0]["moomoo_position_id"] == "solo"

    ungrouped = client.get("/legs?ungrouped_only=true").json()
    assert len(ungrouped) == 1


def test_user_locked_spread_persists_through_snapshot(client):
    fake = client.fake
    fake.legs = [
        RawLeg(
            moomoo_position_id="x_short",
            underlying="SPY",
            option_symbol="US.SPY260619P00100000",
            option_type="PUT",
            strike=Decimal("100"),
            expiry=date(2026, 6, 19),
            quantity=-1,
            entry_price=Decimal("2.50"),
            entry_at=None,
        ),
        RawLeg(
            moomoo_position_id="x_long",
            underlying="SPY",
            option_symbol="US.SPY260619P00095000",
            option_type="PUT",
            strike=Decimal("95"),
            expiry=date(2026, 6, 19),
            quantity=1,
            entry_price=Decimal("1.20"),
            entry_at=None,
        ),
    ]
    fake.quotes = {
        "US.SPY260619P00100000": Quote(
            "US.SPY260619P00100000", Decimal("0.40"), Decimal("0.50"), Decimal("0.45")
        ),
        "US.SPY260619P00095000": Quote(
            "US.SPY260619P00095000", Decimal("0.10"), Decimal("0.20"), Decimal("0.15")
        ),
    }
    fake.underlying_prices = {"SPY": Decimal("110")}

    client.post("/snapshot/run")
    spreads = client.get("/spreads").json()
    assert len(spreads) == 1
    auto_id = spreads[0]["id"]

    r = client.patch(f"/spreads/{auto_id}", json={"user_locked": True})
    assert r.status_code == 200, r.text
    assert r.json()["user_locked"] is True

    client.post("/snapshot/run")
    spreads_after = client.get("/spreads").json()
    assert len(spreads_after) == 1
    assert spreads_after[0]["id"] == auto_id
