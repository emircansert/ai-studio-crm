"""Add Vendor Library tables (vendors + weighted vendor ratings).

Revision ID: 20260705_0015
Revises: 20260705_0014
Create Date: 2026-07-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260705_0015"
down_revision: str | None = "20260705_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category_text", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contact_info", sa.Text(), nullable=True),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="PROSPECT"),
        sa.Column("geography_text", sa.String(length=255), nullable=True),
        sa.Column("last_contact_date", sa.Date(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("archive_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_vendors_created_by_user_id_users"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], name="fk_vendors_updated_by_user_id_users"),
        sa.ForeignKeyConstraint(["archived_by_user_id"], ["users.id"], name="fk_vendors_archived_by_user_id_users"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vendors_name", "vendors", ["name"])
    op.create_index("ix_vendors_category_text", "vendors", ["category_text"])
    op.create_index("ix_vendors_status", "vendors", ["status"])
    op.create_index("ix_vendors_geography_text", "vendors", ["geography_text"])
    op.create_index("ix_vendors_created_by_user_id", "vendors", ["created_by_user_id"])
    op.create_index("ix_vendors_updated_by_user_id", "vendors", ["updated_by_user_id"])
    op.create_index("ix_vendors_archived_by_user_id", "vendors", ["archived_by_user_id"])

    op.create_table(
        "vendor_ratings",
        sa.Column("vendor_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("rater_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=False),
        sa.Column("reliability_score", sa.Integer(), nullable=False),
        sa.Column("pricing_score", sa.Integer(), nullable=False),
        sa.Column("borusan_fit_score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], name="fk_vendor_ratings_vendor_id_vendors", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rater_user_id"], ["users.id"], name="fk_vendor_ratings_rater_user_id_users"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "rater_user_id", name="uq_vendor_rating_vendor_rater"),
    )
    op.create_index("ix_vendor_ratings_vendor_id", "vendor_ratings", ["vendor_id"])
    op.create_index("ix_vendor_ratings_rater_user_id", "vendor_ratings", ["rater_user_id"])


def downgrade() -> None:
    op.drop_index("ix_vendor_ratings_rater_user_id", table_name="vendor_ratings")
    op.drop_index("ix_vendor_ratings_vendor_id", table_name="vendor_ratings")
    op.drop_table("vendor_ratings")
    op.drop_index("ix_vendors_archived_by_user_id", table_name="vendors")
    op.drop_index("ix_vendors_updated_by_user_id", table_name="vendors")
    op.drop_index("ix_vendors_created_by_user_id", table_name="vendors")
    op.drop_index("ix_vendors_geography_text", table_name="vendors")
    op.drop_index("ix_vendors_status", table_name="vendors")
    op.drop_index("ix_vendors_category_text", table_name="vendors")
    op.drop_index("ix_vendors_name", table_name="vendors")
    op.drop_table("vendors")
