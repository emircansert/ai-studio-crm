"""Add notifications and CRM activity feed.

Revision ID: 20260706_0018
Revises: 20260706_0017
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa


revision: str = "20260706_0018"
down_revision: str | None = "20260706_0017"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("notification_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_actor_user_id", "notifications", ["actor_user_id"])
    op.create_index("ix_notifications_entity_id", "notifications", ["entity_id"])
    op.create_index("ix_notifications_entity_type", "notifications", ["entity_type"])
    op.create_index("ix_notifications_notification_type", "notifications", ["notification_type"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_user_read_created", "notifications", ["user_id", "is_read", "created_at"])

    op.create_table(
        "crm_activity_events",
        sa.Column("actor_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crm_activity_events_action", "crm_activity_events", ["action"])
    op.create_index("ix_crm_activity_events_actor_created", "crm_activity_events", ["actor_user_id", "created_at"])
    op.create_index("ix_crm_activity_events_actor_user_id", "crm_activity_events", ["actor_user_id"])
    op.create_index("ix_crm_activity_events_created", "crm_activity_events", ["created_at", "id"])
    op.create_index("ix_crm_activity_events_created_at", "crm_activity_events", ["created_at"])
    op.create_index("ix_crm_activity_events_entity_id", "crm_activity_events", ["entity_id"])
    op.create_index("ix_crm_activity_events_entity_type", "crm_activity_events", ["entity_type"])


def downgrade() -> None:
    op.drop_index("ix_crm_activity_events_entity_type", table_name="crm_activity_events")
    op.drop_index("ix_crm_activity_events_entity_id", table_name="crm_activity_events")
    op.drop_index("ix_crm_activity_events_created_at", table_name="crm_activity_events")
    op.drop_index("ix_crm_activity_events_created", table_name="crm_activity_events")
    op.drop_index("ix_crm_activity_events_actor_user_id", table_name="crm_activity_events")
    op.drop_index("ix_crm_activity_events_actor_created", table_name="crm_activity_events")
    op.drop_index("ix_crm_activity_events_action", table_name="crm_activity_events")
    op.drop_table("crm_activity_events")

    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_notification_type", table_name="notifications")
    op.drop_index("ix_notifications_entity_type", table_name="notifications")
    op.drop_index("ix_notifications_entity_id", table_name="notifications")
    op.drop_index("ix_notifications_actor_user_id", table_name="notifications")
    op.drop_table("notifications")
