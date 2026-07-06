"""Add manual CRM contribution tracking fields.

Revision ID: 20260427_0004
Revises: 20260427_0003
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260427_0004"
down_revision: str | None = "20260427_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def uuid_column(name: str) -> sa.Column:
    return sa.Column(name, sa.Uuid(as_uuid=True), nullable=True)


def upgrade() -> None:
    for table_name in ["organizations", "contacts", "opportunities", "events"]:
        op.add_column(table_name, uuid_column("created_by_user_id"))
        op.add_column(table_name, uuid_column("updated_by_user_id"))
        op.create_index(f"ix_{table_name}_created_by_user_id", table_name, ["created_by_user_id"])
        op.create_index(f"ix_{table_name}_updated_by_user_id", table_name, ["updated_by_user_id"])
        op.create_foreign_key(
            f"fk_{table_name}_created_by_user_id_users",
            table_name,
            "users",
            ["created_by_user_id"],
            ["id"],
        )
        op.create_foreign_key(
            f"fk_{table_name}_updated_by_user_id_users",
            table_name,
            "users",
            ["updated_by_user_id"],
            ["id"],
        )


def downgrade() -> None:
    for table_name in ["events", "opportunities", "contacts", "organizations"]:
        op.drop_constraint(f"fk_{table_name}_updated_by_user_id_users", table_name, type_="foreignkey")
        op.drop_constraint(f"fk_{table_name}_created_by_user_id_users", table_name, type_="foreignkey")
        op.drop_index(f"ix_{table_name}_updated_by_user_id", table_name=table_name)
        op.drop_index(f"ix_{table_name}_created_by_user_id", table_name=table_name)
        op.drop_column(table_name, "updated_by_user_id")
        op.drop_column(table_name, "created_by_user_id")
