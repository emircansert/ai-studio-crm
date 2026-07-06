"""Backfill soft-delete flags for legacy rows.

Revision ID: 20260428_0009
Revises: 20260428_0008
Create Date: 2026-04-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260428_0009"
down_revision: str | None = "20260428_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ARCHIVE_TABLES = [
    "organizations",
    "opportunities",
    "events",
    "contacts",
    "notes",
    "organization_borusan_fit",
    "follow_up_actions",
    "ai_tools",
]


def upgrade() -> None:
    for table_name in ARCHIVE_TABLES:
        op.execute(f"UPDATE {table_name} SET is_archived = 0 WHERE is_archived IS NULL")
    op.execute("UPDATE user_contributions SET is_excluded = 0 WHERE is_excluded IS NULL")


def downgrade() -> None:
    pass
