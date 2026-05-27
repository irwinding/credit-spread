"""unique option_symbol on option_legs

A leg's stable identity is its option_symbol (the moomoo contract code), not
moomoo's position_id which rotates across sessions. Keying on position_id let
the snapshotter insert a fresh leg whenever the id changed, producing duplicate
spreads. This migration deduplicates existing legs (and the orphaned auto
spreads they belonged to) and enforces uniqueness at the DB level.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-27

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Collapse duplicate legs to the earliest row per contract. The earliest
    #    leg is the one carrying the longer snapshot history. Deleting the
    #    extras cascades their leg_snapshots (FK ON DELETE CASCADE).
    conn.execute(
        text(
            """
            DELETE FROM option_legs
            WHERE id NOT IN (
                SELECT MIN(id) FROM option_legs GROUP BY option_symbol
            )
            """
        )
    )

    # 2. Drop auto spreads left with no legs once the duplicate legs are gone.
    #    Cascades their spread_snapshots. User-locked/manual spreads are spared.
    conn.execute(
        text(
            """
            DELETE FROM spreads s
            WHERE s.detection_mode = 'AUTO'
              AND s.user_locked = false
              AND NOT EXISTS (
                  SELECT 1 FROM option_legs l WHERE l.spread_id = s.id
              )
            """
        )
    )

    # 3. Enforce the contract-level identity going forward.
    op.create_unique_constraint(
        "uq_option_legs_option_symbol", "option_legs", ["option_symbol"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_option_legs_option_symbol", "option_legs", type_="unique"
    )
