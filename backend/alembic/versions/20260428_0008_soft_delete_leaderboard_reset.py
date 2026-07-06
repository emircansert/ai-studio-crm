"""Add soft archive fields and leaderboard contribution exclusion.

Revision ID: 20260428_0008
Revises: 20260428_0007
Create Date: 2026-04-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260428_0008"
down_revision: str | None = "20260428_0007"
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
        op.add_column(table_name, sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()))
        op.add_column(table_name, sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table_name, sa.Column("archived_by_user_id", sa.Uuid(as_uuid=True), nullable=True))
        op.add_column(table_name, sa.Column("archive_reason", sa.Text(), nullable=True))
        op.create_index(f"ix_{table_name}_is_archived", table_name, ["is_archived"])
        op.create_index(f"ix_{table_name}_archived_by_user_id", table_name, ["archived_by_user_id"])
        op.create_foreign_key(
            f"fk_{table_name}_archived_by_user_id_users",
            table_name,
            "users",
            ["archived_by_user_id"],
            ["id"],
        )

    op.add_column("user_contributions", sa.Column("is_excluded", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("user_contributions", sa.Column("excluded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_contributions", sa.Column("excluded_by_user_id", sa.Uuid(as_uuid=True), nullable=True))
    op.add_column("user_contributions", sa.Column("exclusion_reason", sa.Text(), nullable=True))
    op.create_index("ix_user_contributions_is_excluded", "user_contributions", ["is_excluded"])
    op.create_index("ix_user_contributions_excluded_by_user_id", "user_contributions", ["excluded_by_user_id"])
    op.create_foreign_key(
        "fk_user_contributions_excluded_by_user_id_users",
        "user_contributions",
        "users",
        ["excluded_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_user_contributions_excluded_by_user_id_users", "user_contributions", type_="foreignkey")
    op.drop_index("ix_user_contributions_excluded_by_user_id", table_name="user_contributions")
    op.drop_index("ix_user_contributions_is_excluded", table_name="user_contributions")
    op.drop_column("user_contributions", "exclusion_reason")
    op.drop_column("user_contributions", "excluded_by_user_id")
    op.drop_column("user_contributions", "excluded_at")
    op.drop_column("user_contributions", "is_excluded")

    for table_name in reversed(ARCHIVE_TABLES):
        op.drop_constraint(f"fk_{table_name}_archived_by_user_id_users", table_name, type_="foreignkey")
        op.drop_index(f"ix_{table_name}_archived_by_user_id", table_name=table_name)
        op.drop_index(f"ix_{table_name}_is_archived", table_name=table_name)
        op.drop_column(table_name, "archive_reason")
        op.drop_column(table_name, "archived_by_user_id")
        op.drop_column(table_name, "archived_at")
        op.drop_column(table_name, "is_archived")
