"""Add admin readiness fields and follow-up completion tracking.

Revision ID: 20260428_0007
Revises: 20260428_0006
Create Date: 2026-04-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260428_0007"
down_revision: str | None = "20260428_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def uuid_column(name: str) -> sa.Column:
    return sa.Column(name, sa.Uuid(as_uuid=True), nullable=True)


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("follow_up_actions", uuid_column("created_by_user_id"))
    op.add_column("follow_up_actions", uuid_column("completed_by_user_id"))
    op.add_column("follow_up_actions", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_follow_up_actions_created_by_user_id", "follow_up_actions", ["created_by_user_id"])
    op.create_index("ix_follow_up_actions_completed_by_user_id", "follow_up_actions", ["completed_by_user_id"])
    op.create_foreign_key(
        "fk_follow_up_actions_created_by_user_id_users",
        "follow_up_actions",
        "users",
        ["created_by_user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_follow_up_actions_completed_by_user_id_users",
        "follow_up_actions",
        "users",
        ["completed_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_follow_up_actions_completed_by_user_id_users", "follow_up_actions", type_="foreignkey")
    op.drop_constraint("fk_follow_up_actions_created_by_user_id_users", "follow_up_actions", type_="foreignkey")
    op.drop_index("ix_follow_up_actions_completed_by_user_id", table_name="follow_up_actions")
    op.drop_index("ix_follow_up_actions_created_by_user_id", table_name="follow_up_actions")
    op.drop_column("follow_up_actions", "completed_at")
    op.drop_column("follow_up_actions", "completed_by_user_id")
    op.drop_column("follow_up_actions", "created_by_user_id")
    op.drop_column("users", "last_login_at")
