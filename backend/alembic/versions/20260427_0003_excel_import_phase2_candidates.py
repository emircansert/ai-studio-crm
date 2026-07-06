"""Add generic import candidates for Excel Import Phase 2.

Revision ID: 20260427_0003
Revises: 20260427_0002
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260427_0003"
down_revision: str | None = "20260427_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    ]


def uuid_column(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, sa.Uuid(as_uuid=True), nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "import_candidates",
        uuid_column("id"),
        uuid_column("import_batch_id"),
        uuid_column("import_row_id", nullable=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("action_type", sa.String(length=40), nullable=False),
        sa.Column("match_entity_type", sa.String(length=80), nullable=True),
        uuid_column("match_entity_id", nullable=True),
        sa.Column("candidate_data", sa.JSON(), nullable=False),
        sa.Column("raw_source", sa.JSON(), nullable=True),
        sa.Column("validation_status", sa.String(length=40), nullable=False),
        sa.Column("decision_status", sa.String(length=40), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["import_row_id"], ["import_rows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_candidates_import_batch_id", "import_candidates", ["import_batch_id"])
    op.create_index("ix_import_candidates_import_row_id", "import_candidates", ["import_row_id"])
    op.create_index("ix_import_candidates_entity_type", "import_candidates", ["entity_type"])
    op.create_index("ix_import_candidates_action_type", "import_candidates", ["action_type"])
    op.create_index("ix_import_candidates_match_entity_id", "import_candidates", ["match_entity_id"])
    op.create_index("ix_import_candidates_validation_status", "import_candidates", ["validation_status"])
    op.create_index("ix_import_candidates_decision_status", "import_candidates", ["decision_status"])


def downgrade() -> None:
    op.drop_table("import_candidates")
