"""add client_entry_id to diary_entries

Revision ID: 7a91c2e4f630
Revises: 2dfde99ccbf3
Create Date: 2026-11-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a91c2e4f630"
down_revision: Union[str, None] = "2dfde99ccbf3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "diary_entries",
        sa.Column("client_entry_id", sa.String(length=36), nullable=True),
    )

    op.create_unique_constraint(
        "uq_diary_entries_user_client_entry",
        "diary_entries",
        ["user_id", "client_entry_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_diary_entries_user_client_entry",
        "diary_entries",
        type_="unique",
    )

    op.drop_column("diary_entries", "client_entry_id")