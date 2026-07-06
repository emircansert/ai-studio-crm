"""Add organization document uploads.

Revision ID: 20260508_0010
Revises: 20260428_0009
Create Date: 2026-05-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260508_0010"
down_revision: str | None = "20260428_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_documents",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=160), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["archived_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organization_documents_organization_id", "organization_documents", ["organization_id"])
    op.create_index("ix_organization_documents_uploaded_by_user_id", "organization_documents", ["uploaded_by_user_id"])
    op.create_index("ix_organization_documents_document_type", "organization_documents", ["document_type"])
    op.create_index("ix_organization_documents_sha256_hash", "organization_documents", ["sha256_hash"])
    op.create_index("ix_organization_documents_archived_by_user_id", "organization_documents", ["archived_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_organization_documents_archived_by_user_id", table_name="organization_documents")
    op.drop_index("ix_organization_documents_sha256_hash", table_name="organization_documents")
    op.drop_index("ix_organization_documents_document_type", table_name="organization_documents")
    op.drop_index("ix_organization_documents_uploaded_by_user_id", table_name="organization_documents")
    op.drop_index("ix_organization_documents_organization_id", table_name="organization_documents")
    op.drop_table("organization_documents")
