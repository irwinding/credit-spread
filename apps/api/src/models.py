from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)

# SQLite needs INTEGER PK for autoincrement; Postgres gets a real BIGSERIAL.
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Spread(Base):
    __tablename__ = "spreads"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    underlying: Mapped[str] = mapped_column(String(16), nullable=False)
    expiry: Mapped[date] = mapped_column(Date, nullable=False)
    spread_type: Mapped[str] = mapped_column(String(16), nullable=False)  # BULL_PUT/BEAR_CALL/OTHER
    short_strike: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    long_strike: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    width: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    quantity: Mapped[int] = mapped_column(default=1)
    net_credit: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    stop_loss_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    detection_mode: Mapped[str] = mapped_column(String(8), default="AUTO")  # AUTO|MANUAL
    user_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    legs: Mapped[list[OptionLeg]] = relationship(back_populates="spread")
    snapshots: Mapped[list[SpreadSnapshot]] = relationship(
        back_populates="spread", cascade="all, delete-orphan"
    )


class OptionLeg(Base):
    __tablename__ = "option_legs"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    moomoo_position_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    underlying: Mapped[str] = mapped_column(String(16), nullable=False)
    option_symbol: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    option_type: Mapped[str] = mapped_column(String(4), nullable=False)  # CALL|PUT
    strike: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    expiry: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)  # signed
    entry_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    entry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    spread_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("spreads.id", ondelete="SET NULL")
    )
    spread: Mapped[Spread | None] = relationship(back_populates="legs")


class LegSnapshot(Base):
    __tablename__ = "leg_snapshots"

    leg_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("option_legs.id", ondelete="CASCADE"), primary_key=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    bid: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    ask: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    mid: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)


class SpreadSnapshot(Base):
    __tablename__ = "spread_snapshots"
    __table_args__ = (UniqueConstraint("spread_id", "ts"),)

    spread_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("spreads.id", ondelete="CASCADE"), primary_key=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    spread_mark: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    pnl_unrealised: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    underlying_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)

    spread: Mapped[Spread] = relationship(back_populates="snapshots")
