"""Add YZ Champion Program activities.

Revision ID: 20260508_0011
Revises: 20260508_0010
Create Date: 2026-05-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260508_0011"
down_revision: str | None = "20260508_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "champion_activities",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("activity_type", sa.String(length=120), nullable=False),
        sa.Column("related_entity_type", sa.String(length=80), nullable=True),
        sa.Column("related_entity_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("activity_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source", sa.String(length=80), nullable=False, server_default="AUTO_CRM"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="ACTIVE"),
        sa.Column("evidence_url", sa.String(length=1024), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["archived_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_champion_activities_user_id", "champion_activities", ["user_id"])
    op.create_index("ix_champion_activities_category", "champion_activities", ["category"])
    op.create_index("ix_champion_activities_activity_type", "champion_activities", ["activity_type"])
    op.create_index("ix_champion_activities_related_entity_type", "champion_activities", ["related_entity_type"])
    op.create_index("ix_champion_activities_related_entity_id", "champion_activities", ["related_entity_id"])
    op.create_index("ix_champion_activities_activity_date", "champion_activities", ["activity_date"])
    op.create_index("ix_champion_activities_source", "champion_activities", ["source"])
    op.create_index("ix_champion_activities_status", "champion_activities", ["status"])
    op.create_index("ix_champion_activities_created_by_user_id", "champion_activities", ["created_by_user_id"])
    op.create_index("ix_champion_activities_archived_by_user_id", "champion_activities", ["archived_by_user_id"])
    op.create_index(
        "ix_champion_activities_user_category_date",
        "champion_activities",
        ["user_id", "category", "activity_date"],
    )
    op.create_index(
        "ix_champion_activities_type_source_date",
        "champion_activities",
        ["activity_type", "source", "activity_date"],
    )
    op.create_index(
        "ix_champion_activities_related",
        "champion_activities",
        ["related_entity_type", "related_entity_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_champion_activities_related", table_name="champion_activities")
    op.drop_index("ix_champion_activities_type_source_date", table_name="champion_activities")
    op.drop_index("ix_champion_activities_user_category_date", table_name="champion_activities")
    op.drop_index("ix_champion_activities_archived_by_user_id", table_name="champion_activities")
    op.drop_index("ix_champion_activities_created_by_user_id", table_name="champion_activities")
    op.drop_index("ix_champion_activities_status", table_name="champion_activities")
    op.drop_index("ix_champion_activities_source", table_name="champion_activities")
    op.drop_index("ix_champion_activities_activity_date", table_name="champion_activities")
    op.drop_index("ix_champion_activities_related_entity_id", table_name="champion_activities")
    op.drop_index("ix_champion_activities_related_entity_type", table_name="champion_activities")
    op.drop_index("ix_champion_activities_activity_type", table_name="champion_activities")
    op.drop_index("ix_champion_activities_category", table_name="champion_activities")
    op.drop_index("ix_champion_activities_user_id", table_name="champion_activities")
    op.drop_table("champion_activities")
