"""Add YZ Champion Program productization tables.

Revision ID: 20260508_0012
Revises: 20260508_0011
Create Date: 2026-05-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260508_0012"
down_revision: str | None = "20260508_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "use_case_proposals",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("borusan_company_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("business_unit_text", sa.String(length=255), nullable=True),
        sa.Column("proposer_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("related_organization_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("problem_area", sa.Text(), nullable=True),
        sa.Column("proposed_solution", sa.Text(), nullable=True),
        sa.Column("expected_impact", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="IDEA"),
        sa.Column("stage", sa.String(length=40), nullable=False, server_default="IDEA"),
        sa.Column("priority", sa.String(length=40), nullable=False, server_default="MEDIUM"),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["archived_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["borusan_company_id"], ["borusan_companies.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["proposer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_use_case_proposals_title", "use_case_proposals", ["title"])
    op.create_index("ix_use_case_proposals_borusan_company_id", "use_case_proposals", ["borusan_company_id"])
    op.create_index("ix_use_case_proposals_business_unit_text", "use_case_proposals", ["business_unit_text"])
    op.create_index("ix_use_case_proposals_proposer_user_id", "use_case_proposals", ["proposer_user_id"])
    op.create_index("ix_use_case_proposals_related_organization_id", "use_case_proposals", ["related_organization_id"])
    op.create_index("ix_use_case_proposals_status", "use_case_proposals", ["status"])
    op.create_index("ix_use_case_proposals_stage", "use_case_proposals", ["stage"])
    op.create_index("ix_use_case_proposals_priority", "use_case_proposals", ["priority"])
    op.create_index("ix_use_case_proposals_created_by_user_id", "use_case_proposals", ["created_by_user_id"])
    op.create_index("ix_use_case_proposals_archived_by_user_id", "use_case_proposals", ["archived_by_user_id"])

    op.create_table(
        "program_activities",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("activity_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("activity_date", sa.Date(), nullable=True),
        sa.Column("location_text", sa.String(length=255), nullable=True),
        sa.Column("owner_team", sa.String(length=255), nullable=True),
        sa.Column("tracking_owner", sa.String(length=255), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["archived_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_program_activities_activity_type", "program_activities", ["activity_type"])
    op.create_index("ix_program_activities_title", "program_activities", ["title"])
    op.create_index("ix_program_activities_activity_date", "program_activities", ["activity_date"])
    op.create_index("ix_program_activities_created_by_user_id", "program_activities", ["created_by_user_id"])
    op.create_index("ix_program_activities_archived_by_user_id", "program_activities", ["archived_by_user_id"])

    op.create_table(
        "program_activity_participants",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("program_activity_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=True),
        sa.Column("attendance_status", sa.String(length=40), nullable=True),
        sa.Column("completion_status", sa.String(length=40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["program_activity_id"], ["program_activities.id"]),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_program_activity_participants_program_activity_id", "program_activity_participants", ["program_activity_id"])
    op.create_index("ix_program_activity_participants_user_id", "program_activity_participants", ["user_id"])
    op.create_index("ix_program_activity_participants_role", "program_activity_participants", ["role"])
    op.create_index("ix_program_activity_participants_attendance_status", "program_activity_participants", ["attendance_status"])
    op.create_index("ix_program_activity_participants_completion_status", "program_activity_participants", ["completion_status"])
    op.create_index("ix_program_activity_participants_recorded_by_user_id", "program_activity_participants", ["recorded_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_program_activity_participants_recorded_by_user_id", table_name="program_activity_participants")
    op.drop_index("ix_program_activity_participants_completion_status", table_name="program_activity_participants")
    op.drop_index("ix_program_activity_participants_attendance_status", table_name="program_activity_participants")
    op.drop_index("ix_program_activity_participants_role", table_name="program_activity_participants")
    op.drop_index("ix_program_activity_participants_user_id", table_name="program_activity_participants")
    op.drop_index("ix_program_activity_participants_program_activity_id", table_name="program_activity_participants")
    op.drop_table("program_activity_participants")
    op.drop_index("ix_program_activities_archived_by_user_id", table_name="program_activities")
    op.drop_index("ix_program_activities_created_by_user_id", table_name="program_activities")
    op.drop_index("ix_program_activities_activity_date", table_name="program_activities")
    op.drop_index("ix_program_activities_title", table_name="program_activities")
    op.drop_index("ix_program_activities_activity_type", table_name="program_activities")
    op.drop_table("program_activities")
    op.drop_index("ix_use_case_proposals_archived_by_user_id", table_name="use_case_proposals")
    op.drop_index("ix_use_case_proposals_created_by_user_id", table_name="use_case_proposals")
    op.drop_index("ix_use_case_proposals_priority", table_name="use_case_proposals")
    op.drop_index("ix_use_case_proposals_stage", table_name="use_case_proposals")
    op.drop_index("ix_use_case_proposals_status", table_name="use_case_proposals")
    op.drop_index("ix_use_case_proposals_related_organization_id", table_name="use_case_proposals")
    op.drop_index("ix_use_case_proposals_proposer_user_id", table_name="use_case_proposals")
    op.drop_index("ix_use_case_proposals_business_unit_text", table_name="use_case_proposals")
    op.drop_index("ix_use_case_proposals_borusan_company_id", table_name="use_case_proposals")
    op.drop_index("ix_use_case_proposals_title", table_name="use_case_proposals")
    op.drop_table("use_case_proposals")
