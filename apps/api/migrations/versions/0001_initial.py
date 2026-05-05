"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "spreads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("underlying", sa.String(16), nullable=False),
        sa.Column("expiry", sa.Date(), nullable=False),
        sa.Column("spread_type", sa.String(16), nullable=False),
        sa.Column("short_strike", sa.Numeric(14, 4)),
        sa.Column("long_strike", sa.Numeric(14, 4)),
        sa.Column("width", sa.Numeric(14, 4)),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("net_credit", sa.Numeric(14, 4)),
        sa.Column("opened_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("detection_mode", sa.String(8), nullable=False, server_default="AUTO"),
        sa.Column("user_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_spreads_underlying_expiry", "spreads", ["underlying", "expiry"])

    op.create_table(
        "option_legs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("moomoo_position_id", sa.String(64), nullable=False, unique=True),
        sa.Column("underlying", sa.String(16), nullable=False),
        sa.Column("option_symbol", sa.String(64), nullable=False),
        sa.Column("option_type", sa.String(4), nullable=False),
        sa.Column("strike", sa.Numeric(14, 4), nullable=False),
        sa.Column("expiry", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("entry_price", sa.Numeric(14, 4)),
        sa.Column("entry_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "spread_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("spreads.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_option_legs_underlying_expiry", "option_legs", ["underlying", "expiry"])

    op.create_table(
        "spread_snapshots",
        sa.Column(
            "spread_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("spreads.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("ts", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("spread_mark", sa.Numeric(14, 4), nullable=False),
        sa.Column("pnl_unrealised", sa.Numeric(14, 4), nullable=False),
        sa.Column("underlying_price", sa.Numeric(14, 4), nullable=False),
        sa.UniqueConstraint("spread_id", "ts", name="uq_spread_snapshots_spread_ts"),
    )


def downgrade() -> None:
    op.drop_table("spread_snapshots")
    op.drop_index("ix_option_legs_underlying_expiry", table_name="option_legs")
    op.drop_table("option_legs")
    op.drop_index("ix_spreads_underlying_expiry", table_name="spreads")
    op.drop_table("spreads")
