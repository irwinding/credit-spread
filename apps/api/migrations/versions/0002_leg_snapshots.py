"""leg snapshots

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leg_snapshots",
        sa.Column(
            "leg_id",
            sa.BigInteger(),
            sa.ForeignKey("option_legs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("ts", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("bid", sa.Numeric(14, 4)),
        sa.Column("ask", sa.Numeric(14, 4)),
        sa.Column("mid", sa.Numeric(14, 4), nullable=False),
    )
    op.create_index("ix_leg_snapshots_leg_ts", "leg_snapshots", ["leg_id", "ts"])


def downgrade() -> None:
    op.drop_index("ix_leg_snapshots_leg_ts", table_name="leg_snapshots")
    op.drop_table("leg_snapshots")
