"""Add per-user sidebar section access.

Revision ID: 20260705_0014
Revises: 20260510_0013
Create Date: 2026-07-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260705_0014"
down_revision: str | None = "20260510_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_section_access",
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("section_key", sa.String(length=80), nullable=False),
        sa.Column("access_level", sa.String(length=20), nullable=False),
        sa.Column("granted_by_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["granted_by_user_id"], ["users.id"], name="fk_user_section_access_granted_by_user_id_users"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_section_access_user_id_users"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "section_key", name="uq_user_section_access_user_section"),
    )
    op.create_index("ix_user_section_access_user_id", "user_section_access", ["user_id"])
    op.create_index("ix_user_section_access_section_key", "user_section_access", ["section_key"])
    op.create_index("ix_user_section_access_granted_by_user_id", "user_section_access", ["granted_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_section_access_granted_by_user_id", table_name="user_section_access")
    op.drop_index("ix_user_section_access_section_key", table_name="user_section_access")
    op.drop_index("ix_user_section_access_user_id", table_name="user_section_access")
    op.drop_table("user_section_access")
