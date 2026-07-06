"""Add batch-level import warnings for Excel Import Phase 1.

Revision ID: 20260427_0002
Revises: 20260426_0001
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260427_0002"
down_revision: str | None = "20260426_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("import_warnings", sa.Column("import_batch_id", sa.Uuid(as_uuid=True), nullable=True))
    op.create_index("ix_import_warnings_import_batch_id", "import_warnings", ["import_batch_id"])
    op.create_foreign_key(
        "fk_import_warnings_import_batch_id_import_batches",
        "import_warnings",
        "import_batches",
        ["import_batch_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_import_warnings_import_batch_id_import_batches", "import_warnings", type_="foreignkey")
    op.drop_index("ix_import_warnings_import_batch_id", table_name="import_warnings")
    op.drop_column("import_warnings", "import_batch_id")
