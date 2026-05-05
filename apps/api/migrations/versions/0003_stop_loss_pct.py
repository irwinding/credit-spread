"""stop loss percent on spreads

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "spreads",
        sa.Column("stop_loss_pct", sa.Numeric(8, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("spreads", "stop_loss_pct")
