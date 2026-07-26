"""Re-key user_section_access by UPN (Entra ID User Principal Name).

Backfills user_upn from the linked user's lower-cased email, which is the UPN
under Microsoft Entra ID for accounts whose CRM email matches their corporate
sign-in. Rows that cannot be mapped make the migration fail loudly rather than
silently dropping permission assignments.

Revision ID: 20260707_0019
Revises: 20260706_0018
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "20260707_0019"
down_revision: str | None = "20260706_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user_section_access", sa.Column("user_upn", sa.String(length=320), nullable=True))

    op.execute(
        """
        UPDATE usa
        SET user_upn = LOWER(u.email)
        FROM user_section_access usa
        INNER JOIN users u ON u.id = usa.user_id
        """
    )

    if not context.is_offline_mode():
        connection = op.get_bind()
        unmapped = connection.execute(
            sa.text("SELECT COUNT(*) FROM user_section_access WHERE user_upn IS NULL")
        ).scalar()
        if unmapped:
            raise RuntimeError(
                f"{unmapped} user_section_access rows could not be mapped to a UPN. "
                "Resolve these manually before re-running the migration; no data was dropped."
            )

    # SQL Server requires dropping dependent constraints/indexes before the column.
    op.drop_constraint("uq_user_section_access_user_section", "user_section_access", type_="unique")
    op.drop_index("ix_user_section_access_user_id", table_name="user_section_access")
    op.drop_constraint("fk_user_section_access_user_id_users", "user_section_access", type_="foreignkey")
    op.drop_column("user_section_access", "user_id")

    op.alter_column("user_section_access", "user_upn", existing_type=sa.String(length=320), nullable=False)
    op.create_unique_constraint(
        "uq_user_section_access_upn_section", "user_section_access", ["user_upn", "section_key"]
    )
    op.create_index("ix_user_section_access_user_upn", "user_section_access", ["user_upn"])


def downgrade() -> None:
    op.add_column("user_section_access", sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True))
    op.execute(
        """
        UPDATE usa
        SET user_id = u.id
        FROM user_section_access usa
        INNER JOIN users u ON LOWER(u.email) = usa.user_upn
        """
    )
    # Rows whose UPN no longer matches a local user cannot be restored to id keys.
    op.execute("DELETE FROM user_section_access WHERE user_id IS NULL")
    op.drop_index("ix_user_section_access_user_upn", table_name="user_section_access")
    op.drop_constraint("uq_user_section_access_upn_section", "user_section_access", type_="unique")
    op.drop_column("user_section_access", "user_upn")
    op.alter_column("user_section_access", "user_id", existing_type=sa.Uuid(as_uuid=True), nullable=False)
    op.create_foreign_key(
        "fk_user_section_access_user_id_users", "user_section_access", "users", ["user_id"], ["id"]
    )
    op.create_index("ix_user_section_access_user_id", "user_section_access", ["user_id"])
    op.create_unique_constraint(
        "uq_user_section_access_user_section", "user_section_access", ["user_id", "section_key"]
    )
