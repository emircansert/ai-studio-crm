"""Add PoC Kanban stages and opportunity document storage.

Revision ID: 20260705_0016
Revises: 20260705_0015
Create Date: 2026-07-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260705_0016"
down_revision: str | None = "20260705_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("opportunities", sa.Column("stage_migration_note", sa.Text(), nullable=True))

    op.execute(
        """
        UPDATE opportunities
        SET stage_migration_note = CONCAT('Original stage "', stage, '" could not be confidently mapped to the PoC funnel; defaulted to IDEA.')
        WHERE UPPER(REPLACE(REPLACE(LTRIM(RTRIM(stage)), ' ', '_'), '-', '_')) NOT IN (
            'IDEA',
            'SCOUTING',
            'DISCOVERY',
            'DISCUSSIONS_ONGOING',
            'EVALUATION',
            'SHORTLIST',
            'SHORT_LIST',
            'SHORT_LISTING',
            'POC_PLANNED',
            'POC_ACTIVE',
            'POC',
            'PILOT',
            'COMPLETED',
            'ON_HOLD',
            'CANCELLED',
            'POST_POC'
        )
        """
    )
    op.execute(
        """
        UPDATE opportunities
        SET stage = CASE UPPER(REPLACE(REPLACE(LTRIM(RTRIM(stage)), ' ', '_'), '-', '_'))
            WHEN 'IDEA' THEN 'IDEA'
            WHEN 'SCOUTING' THEN 'SCOUTING'
            WHEN 'DISCOVERY' THEN 'SCOUTING'
            WHEN 'DISCUSSIONS_ONGOING' THEN 'SCOUTING'
            WHEN 'EVALUATION' THEN 'SHORT_LISTING'
            WHEN 'SHORTLIST' THEN 'SHORT_LISTING'
            WHEN 'SHORT_LIST' THEN 'SHORT_LISTING'
            WHEN 'SHORT_LISTING' THEN 'SHORT_LISTING'
            WHEN 'POC_PLANNED' THEN 'POC'
            WHEN 'POC_ACTIVE' THEN 'POC'
            WHEN 'POC' THEN 'POC'
            WHEN 'PILOT' THEN 'POC'
            WHEN 'COMPLETED' THEN 'POST_POC'
            WHEN 'ON_HOLD' THEN 'POST_POC'
            WHEN 'CANCELLED' THEN 'POST_POC'
            WHEN 'POST_POC' THEN 'POST_POC'
            ELSE 'IDEA'
        END
        """
    )

    op.create_table(
        "opportunity_documents",
        sa.Column("opportunity_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("document_type", sa.String(length=80), nullable=False, server_default="POC_DOCUMENT"),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=160), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], name="fk_opportunity_documents_opportunity_id_opportunities"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], name="fk_opportunity_documents_uploaded_by_user_id_users"),
        sa.ForeignKeyConstraint(["archived_by_user_id"], ["users.id"], name="fk_opportunity_documents_archived_by_user_id_users"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunity_documents_opportunity_id", "opportunity_documents", ["opportunity_id"])
    op.create_index("ix_opportunity_documents_uploaded_by_user_id", "opportunity_documents", ["uploaded_by_user_id"])
    op.create_index("ix_opportunity_documents_archived_by_user_id", "opportunity_documents", ["archived_by_user_id"])
    op.create_index("ix_opportunity_documents_document_type", "opportunity_documents", ["document_type"])
    op.create_index("ix_opportunity_documents_sha256_hash", "opportunity_documents", ["sha256_hash"])


def downgrade() -> None:
    op.drop_index("ix_opportunity_documents_sha256_hash", table_name="opportunity_documents")
    op.drop_index("ix_opportunity_documents_document_type", table_name="opportunity_documents")
    op.drop_index("ix_opportunity_documents_archived_by_user_id", table_name="opportunity_documents")
    op.drop_index("ix_opportunity_documents_uploaded_by_user_id", table_name="opportunity_documents")
    op.drop_index("ix_opportunity_documents_opportunity_id", table_name="opportunity_documents")
    op.drop_table("opportunity_documents")
    op.drop_column("opportunities", "stage_migration_note")
