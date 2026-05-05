"""Pydantic response schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class LegOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    moomoo_position_id: str
    underlying: str
    option_symbol: str
    option_type: str
    strike: Decimal
    expiry: date
    quantity: int
    entry_price: Decimal | None
    spread_id: uuid.UUID | None
    last_mark: Decimal | None = None
    last_bid: Decimal | None = None
    last_ask: Decimal | None = None
    last_mark_ts: datetime | None = None


class LegSnapshotPoint(BaseModel):
    ts: datetime
    bid: Decimal | None
    ask: Decimal | None
    mid: Decimal


class LegHistory(BaseModel):
    leg_id: int
    points: list[LegSnapshotPoint]


class SpreadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    underlying: str
    expiry: date
    spread_type: str
    short_strike: Decimal | None
    long_strike: Decimal | None
    width: Decimal | None
    quantity: int
    net_credit: Decimal | None
    stop_loss_pct: Decimal | None
    opened_at: datetime | None
    closed_at: datetime | None
    detection_mode: str
    user_locked: bool
    legs: list[LegOut] = []
    last_pnl: Decimal | None = None
    last_spread_mark: Decimal | None = None
    last_underlying_price: Decimal | None = None
    last_snapshot_at: datetime | None = None
    stop_loss_breached: bool = False


class SnapshotPoint(BaseModel):
    ts: datetime
    spread_mark: Decimal
    pnl_unrealised: Decimal
    underlying_price: Decimal


class SpreadHistory(BaseModel):
    spread_id: uuid.UUID
    points: list[SnapshotPoint]


class SpreadCreate(BaseModel):
    leg_position_ids: list[str]


class SpreadPatch(BaseModel):
    leg_position_ids: list[str] | None = None
    user_locked: bool | None = None
    stop_loss_pct: Decimal | None = None


class SnapshotResult(BaseModel):
    rows_written: int
    ts: datetime


class SnapshotStatus(BaseModel):
    next_run_at: datetime | None
    last_snapshot_at: datetime | None
    server_time: datetime
