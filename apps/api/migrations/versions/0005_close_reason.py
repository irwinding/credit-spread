"""close reason tags

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("spreads", sa.Column("close_reason", sa.String(32), nullable=True))
    op.add_column("option_legs", sa.Column("close_reason", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("option_legs", "close_reason")
    op.drop_column("spreads", "close_reason")
