"""Initial Backend Phase 1 schema for Microsoft SQL Server.

Revision ID: 20260426_0001
Revises:
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260426_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    ]


def uuid_column(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, sa.Uuid(as_uuid=True), nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "users",
        uuid_column("id"),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "statuses",
        uuid_column("id"),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("status_group", sa.String(length=80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_terminal", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("status_group", "code", name="uq_statuses_status_group_code"),
    )
    op.create_index("ix_statuses_code", "statuses", ["code"])
    op.create_index("ix_statuses_status_group", "statuses", ["status_group"])

    op.create_table(
        "borusan_companies",
        uuid_column("id"),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("english_name", sa.String(length=255), nullable=True),
        sa.Column("legacy_excel_column", sa.String(length=120), nullable=True),
        sa.Column("aliases", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_borusan_companies_code", "borusan_companies", ["code"])

    op.create_table(
        "import_batches",
        uuid_column("id"),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=False),
        uuid_column("uploaded_by_user_id", nullable=True),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("workbook_metadata", sa.JSON(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_batches_file_sha256", "import_batches", ["file_sha256"])
    op.create_index("ix_import_batches_status", "import_batches", ["status"])

    op.create_table(
        "import_sheets",
        uuid_column("id"),
        uuid_column("import_batch_id"),
        sa.Column("sheet_name", sa.String(length=255), nullable=False),
        sa.Column("detected_entity", sa.String(length=120), nullable=True),
        sa.Column("header_row", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_mapping", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_sheets_import_batch_id", "import_sheets", ["import_batch_id"])

    op.create_table(
        "import_rows",
        uuid_column("id"),
        uuid_column("import_sheet_id"),
        sa.Column("excel_row_number", sa.Integer(), nullable=False),
        sa.Column("raw_values", sa.JSON(), nullable=False),
        sa.Column("cleaned_values", sa.JSON(), nullable=True),
        sa.Column("normalized_candidate", sa.JSON(), nullable=True),
        sa.Column("row_hash", sa.String(length=64), nullable=True),
        sa.Column("validation_status", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["import_sheet_id"], ["import_sheets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_rows_import_sheet_id", "import_rows", ["import_sheet_id"])
    op.create_index("ix_import_rows_row_hash", "import_rows", ["row_hash"])
    op.create_index("ix_import_rows_validation_status", "import_rows", ["validation_status"])

    op.create_table(
        "organizations",
        uuid_column("id"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("organization_type", sa.String(length=64), nullable=False),
        sa.Column("organization_subtype", sa.String(length=80), nullable=True),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("website_domain", sa.String(length=255), nullable=True),
        sa.Column("geography_text", sa.String(length=255), nullable=True),
        sa.Column("country_codes", sa.JSON(), nullable=True),
        sa.Column("source_text", sa.String(length=512), nullable=True),
        sa.Column("added_by_text", sa.String(length=255), nullable=True),
        sa.Column("solution_summary", sa.Text(), nullable=True),
        uuid_column("lifecycle_status_id", nullable=True),
        uuid_column("relationship_status_id", nullable=True),
        sa.Column("last_contact_date", sa.Date(), nullable=True),
        uuid_column("raw_import_ref", nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_tags", sa.JSON(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["lifecycle_status_id"], ["statuses.id"]),
        sa.ForeignKeyConstraint(["relationship_status_id"], ["statuses.id"]),
        sa.ForeignKeyConstraint(["raw_import_ref"], ["import_rows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"])
    op.create_index("ix_organizations_normalized_name", "organizations", ["normalized_name"])
    op.create_index("ix_organizations_organization_type", "organizations", ["organization_type"])
    op.create_index("ix_organizations_organization_subtype", "organizations", ["organization_subtype"])
    op.create_index("ix_organizations_website_domain", "organizations", ["website_domain"])
    op.create_index("ix_organizations_geography_text", "organizations", ["geography_text"])
    op.create_index("ix_organizations_source_text", "organizations", ["source_text"])
    op.create_index("ix_organizations_type_status", "organizations", ["organization_type", "lifecycle_status_id"])
    op.create_index("ix_organizations_type_geography", "organizations", ["organization_type", "geography_text"])
    op.create_index("ix_organizations_type_source", "organizations", ["organization_type", "source_text"])

    op.create_table(
        "contacts",
        uuid_column("id"),
        uuid_column("organization_id"),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("contact_source", sa.String(length=80), nullable=False),
        sa.Column("raw_contact_text", sa.Text(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_organization_id", "contacts", ["organization_id"])
    op.create_index("ix_contacts_email", "contacts", ["email"])

    op.create_table(
        "organization_status_history",
        uuid_column("id"),
        uuid_column("organization_id"),
        uuid_column("status_id"),
        uuid_column("changed_by_user_id", nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["status_id"], ["statuses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organization_status_history_organization_id", "organization_status_history", ["organization_id"])

    op.create_table(
        "organization_borusan_fit",
        uuid_column("id"),
        uuid_column("organization_id"),
        uuid_column("borusan_company_id"),
        sa.Column("fit_level", sa.String(length=32), nullable=False),
        sa.Column("fit_reason", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("raw_value", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["borusan_company_id"], ["borusan_companies.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "borusan_company_id", name="uq_org_borusan_fit"),
    )

    op.create_table(
        "tags",
        uuid_column("id"),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("tag_group", sa.String(length=80), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_tags_code", "tags", ["code"])
    op.create_index("ix_tags_tag_group", "tags", ["tag_group"])

    op.create_table(
        "organization_tags",
        uuid_column("organization_id"),
        uuid_column("tag_id"),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("organization_id", "tag_id"),
        sa.UniqueConstraint("organization_id", "tag_id", name="uq_organization_tag"),
    )

    op.create_table(
        "opportunities",
        uuid_column("id"),
        sa.Column("title", sa.String(length=255), nullable=False),
        uuid_column("organization_id"),
        uuid_column("borusan_company_id"),
        sa.Column("opportunity_type", sa.String(length=80), nullable=False),
        sa.Column("stage", sa.String(length=80), nullable=False),
        uuid_column("status_id", nullable=True),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("terms_text", sa.Text(), nullable=True),
        sa.Column("value_hypothesis", sa.Text(), nullable=True),
        sa.Column("expected_start_date", sa.Date(), nullable=True),
        sa.Column("expected_end_date", sa.Date(), nullable=True),
        sa.Column("last_contact_date", sa.Date(), nullable=True),
        uuid_column("owner_user_id", nullable=True),
        uuid_column("next_action_id", nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["borusan_company_id"], ["borusan_companies.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["status_id"], ["statuses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunities_title", "opportunities", ["title"])
    op.create_index("ix_opportunities_organization_id", "opportunities", ["organization_id"])
    op.create_index("ix_opportunities_borusan_company_id", "opportunities", ["borusan_company_id"])
    op.create_index("ix_opportunities_stage", "opportunities", ["stage"])

    op.create_table(
        "events",
        uuid_column("id"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("date_text", sa.String(length=255), nullable=True),
        sa.Column("location_text", sa.String(length=255), nullable=False),
        sa.Column("geography_text", sa.String(length=255), nullable=True),
        sa.Column("area_text", sa.String(length=255), nullable=True),
        sa.Column("ai_program_relevance", sa.String(length=32), nullable=False),
        sa.Column("value_creation_potential", sa.String(length=32), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_name", "events", ["name"])
    op.create_index("ix_events_geography_text", "events", ["geography_text"])

    op.create_table(
        "event_tags",
        uuid_column("event_id"),
        uuid_column("tag_id"),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("event_id", "tag_id"),
        sa.UniqueConstraint("event_id", "tag_id", name="uq_event_tag"),
    )

    op.create_table(
        "event_participants",
        uuid_column("id"),
        uuid_column("event_id"),
        sa.Column("participant_role", sa.String(length=120), nullable=False),
        sa.Column("participant_name", sa.String(length=255), nullable=True),
        sa.Column("participant_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_participants_event_id", "event_participants", ["event_id"])

    op.create_table(
        "ai_tools",
        uuid_column("id"),
        sa.Column("name", sa.String(length=255), nullable=False),
        uuid_column("vendor_organization_id", nullable=True),
        sa.Column("category_text", sa.String(length=255), nullable=True),
        sa.Column("solution_summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        uuid_column("added_by_user_id", nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["added_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vendor_organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_tools_name", "ai_tools", ["name"])
    op.create_index("ix_ai_tools_category_text", "ai_tools", ["category_text"])

    op.create_table(
        "notes",
        uuid_column("id"),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        uuid_column("entity_id"),
        sa.Column("note_type", sa.String(length=80), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        uuid_column("created_by_user_id", nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notes_entity_type", "notes", ["entity_type"])
    op.create_index("ix_notes_entity_id", "notes", ["entity_id"])
    op.create_index("ix_notes_entity", "notes", ["entity_type", "entity_id"])

    op.create_table(
        "follow_up_actions",
        uuid_column("id"),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        uuid_column("entity_id"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        uuid_column("assigned_to_user_id", nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_follow_up_actions_entity_type", "follow_up_actions", ["entity_type"])
    op.create_index("ix_follow_up_actions_entity_id", "follow_up_actions", ["entity_id"])
    op.create_index("ix_follow_up_actions_entity", "follow_up_actions", ["entity_type", "entity_id"])

    op.create_table(
        "import_warnings",
        uuid_column("id"),
        uuid_column("import_row_id", nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("field_name", sa.String(length=120), nullable=True),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["import_row_id"], ["import_rows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_warnings_import_row_id", "import_warnings", ["import_row_id"])
    op.create_index("ix_import_warnings_severity", "import_warnings", ["severity"])
    op.create_index("ix_import_warnings_code", "import_warnings", ["code"])

    op.create_table(
        "audit_logs",
        uuid_column("id"),
        uuid_column("actor_user_id", nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        uuid_column("entity_id", nullable=True),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])

    op.create_table(
        "branding_assets",
        uuid_column("id"),
        sa.Column("asset_type", sa.String(length=80), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        uuid_column("uploaded_by_user_id", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_branding_assets_asset_type", "branding_assets", ["asset_type"])
    op.create_index(
        "uq_branding_assets_active_logo",
        "branding_assets",
        ["asset_type"],
        unique=True,
        mssql_where=sa.text("asset_type = 'LOGO' AND is_active = 1"),
    )


def downgrade() -> None:
    for table_name in [
        "branding_assets",
        "audit_logs",
        "import_warnings",
        "follow_up_actions",
        "notes",
        "ai_tools",
        "event_participants",
        "event_tags",
        "events",
        "opportunities",
        "organization_tags",
        "tags",
        "organization_borusan_fit",
        "organization_status_history",
        "contacts",
        "organizations",
        "import_rows",
        "import_sheets",
        "import_batches",
        "borusan_companies",
        "statuses",
        "users",
    ]:
        op.drop_table(table_name)
