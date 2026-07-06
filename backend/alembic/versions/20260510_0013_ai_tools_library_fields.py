"""Add AI Tools Library CRM fields.

Revision ID: 20260510_0013
Revises: 20260508_0012
Create Date: 2026-05-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260510_0013"
down_revision: str | None = "20260508_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_tools", sa.Column("vendor_name", sa.String(length=255), nullable=True))
    op.add_column("ai_tools", sa.Column("website_url", sa.String(length=1024), nullable=True))
    op.add_column("ai_tools", sa.Column("primary_use_case", sa.String(length=255), nullable=True))
    op.add_column("ai_tools", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("ai_tools", sa.Column("pricing_model", sa.String(length=80), nullable=True))
    op.add_column("ai_tools", sa.Column("deployment_type", sa.String(length=80), nullable=True))
    op.add_column("ai_tools", sa.Column("data_sensitivity_level", sa.String(length=80), nullable=True))
    op.add_column("ai_tools", sa.Column("status", sa.String(length=80), nullable=False, server_default="Identified"))
    op.add_column("ai_tools", sa.Column("owner_notes", sa.Text(), nullable=True))
    op.add_column("ai_tools", sa.Column("source", sa.String(length=120), nullable=True, server_default="MANUAL"))
    op.add_column("ai_tools", sa.Column("updated_by_user_id", sa.Uuid(as_uuid=True), nullable=True))
    op.create_index("ix_ai_tools_vendor_name", "ai_tools", ["vendor_name"])
    op.create_index("ix_ai_tools_primary_use_case", "ai_tools", ["primary_use_case"])
    op.create_index("ix_ai_tools_pricing_model", "ai_tools", ["pricing_model"])
    op.create_index("ix_ai_tools_deployment_type", "ai_tools", ["deployment_type"])
    op.create_index("ix_ai_tools_data_sensitivity_level", "ai_tools", ["data_sensitivity_level"])
    op.create_index("ix_ai_tools_status", "ai_tools", ["status"])
    op.create_index("ix_ai_tools_source", "ai_tools", ["source"])
    op.create_foreign_key(
        "fk_ai_tools_updated_by_user_id_users",
        "ai_tools",
        "users",
        ["updated_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_tools_updated_by_user_id_users", "ai_tools", type_="foreignkey")
    op.drop_index("ix_ai_tools_source", table_name="ai_tools")
    op.drop_index("ix_ai_tools_status", table_name="ai_tools")
    op.drop_index("ix_ai_tools_data_sensitivity_level", table_name="ai_tools")
    op.drop_index("ix_ai_tools_deployment_type", table_name="ai_tools")
    op.drop_index("ix_ai_tools_pricing_model", table_name="ai_tools")
    op.drop_index("ix_ai_tools_primary_use_case", table_name="ai_tools")
    op.drop_index("ix_ai_tools_vendor_name", table_name="ai_tools")
    op.drop_column("ai_tools", "updated_by_user_id")
    op.drop_column("ai_tools", "source")
    op.drop_column("ai_tools", "owner_notes")
    op.drop_column("ai_tools", "status")
    op.drop_column("ai_tools", "data_sensitivity_level")
    op.drop_column("ai_tools", "deployment_type")
    op.drop_column("ai_tools", "pricing_model")
    op.drop_column("ai_tools", "description")
    op.drop_column("ai_tools", "primary_use_case")
    op.drop_column("ai_tools", "website_url")
    op.drop_column("ai_tools", "vendor_name")
