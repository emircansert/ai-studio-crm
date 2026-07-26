"""Drop users.password_hash - authentication is Microsoft Entra ID only.

Per the Information Security requirement that the application work exclusively
through Entra users and hold no internal user credentials, local password
authentication has been removed from the code and the column that stored the
bcrypt hashes is dropped here.

Revision ID: 20260726_0020
Revises: 20260707_0019
Create Date: 2026-07-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260726_0020"
down_revision: str | None = "20260707_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("users", "password_hash")


def downgrade() -> None:
    """Re-add the column so the schema shape can be restored.

    The stored hashes are NOT recoverable: dropping the column destroys them.
    The column is re-created with an empty-string default so existing rows
    satisfy the NOT NULL constraint; no account would be able to authenticate
    with it, and the local auth code no longer exists.
    """
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=False, server_default=""),
    )
    op.alter_column("users", "password_hash", server_default=None)
