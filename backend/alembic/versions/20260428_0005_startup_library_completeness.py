"""Add startup library category and vertical fields.

Revision ID: 20260428_0005
Revises: 20260427_0004
Create Date: 2026-04-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260428_0005"
down_revision: str | None = "20260427_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("category_code", sa.String(length=120), nullable=True))
    op.add_column("organizations", sa.Column("category_label", sa.String(length=255), nullable=True))
    op.add_column("organizations", sa.Column("vertical_text", sa.String(length=255), nullable=True))
    op.create_index("ix_organizations_category_code", "organizations", ["category_code"])
    op.create_index("ix_organizations_category_label", "organizations", ["category_label"])
    op.create_index("ix_organizations_vertical_text", "organizations", ["vertical_text"])


def downgrade() -> None:
    op.drop_index("ix_organizations_vertical_text", table_name="organizations")
    op.drop_index("ix_organizations_category_label", table_name="organizations")
    op.drop_index("ix_organizations_category_code", table_name="organizations")
    op.drop_column("organizations", "vertical_text")
    op.drop_column("organizations", "category_label")
    op.drop_column("organizations", "category_code")
