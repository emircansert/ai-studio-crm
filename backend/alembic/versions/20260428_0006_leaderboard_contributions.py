"""Add manual user contribution tracking.

Revision ID: 20260428_0006
Revises: 20260428_0005
Create Date: 2026-04-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260428_0006"
down_revision: str | None = "20260428_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def uuid_column(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, sa.Uuid(as_uuid=True), nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "user_contributions",
        uuid_column("id"),
        uuid_column("user_id"),
        sa.Column("contribution_type", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        uuid_column("entity_id", nullable=True),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_contributions_user_id", "user_contributions", ["user_id"])
    op.create_index("ix_user_contributions_contribution_type", "user_contributions", ["contribution_type"])
    op.create_index("ix_user_contributions_entity_type", "user_contributions", ["entity_type"])
    op.create_index("ix_user_contributions_entity_id", "user_contributions", ["entity_id"])
    op.create_index("ix_user_contributions_source", "user_contributions", ["source"])
    op.create_index("ix_user_contributions_occurred_at", "user_contributions", ["occurred_at"])
    op.create_index(
        "ix_user_contributions_user_source_time",
        "user_contributions",
        ["user_id", "source", "occurred_at"],
    )
    op.create_index(
        "ix_user_contributions_type_source_time",
        "user_contributions",
        ["contribution_type", "source", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("user_contributions")
