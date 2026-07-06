"""Align startup process status labels.

Revision ID: 20260706_0017
Revises: 20260705_0016
Create Date: 2026-07-06
"""

from alembic import op


revision: str = "20260706_0017"
down_revision: str | None = "20260705_0016"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE statuses SET label = '1- Info', sort_order = 10 "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'INFORMATION_RECEIVED'"
    )
    op.execute(
        "UPDATE statuses SET label = '2- Contacted/Positive', sort_order = 20 "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'MEETING_HELD'"
    )
    op.execute(
        "UPDATE statuses SET label = '2- Contacted/Negative', sort_order = 30 "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'NOT_A_FIT'"
    )
    op.execute(
        "UPDATE statuses SET label = '3-Planned for the Future', sort_order = 40 "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'IN_PROGRESS'"
    )
    op.execute(
        "UPDATE statuses SET label = '4-NDA/Contract', sort_order = 50 "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'NDA'"
    )
    op.execute(
        "UPDATE statuses SET label = '5-PoC in Progress', sort_order = 60 "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'POC_IN_PROGRESS'"
    )
    op.execute(
        "UPDATE statuses SET label = '6- PoC Failed', sort_order = 70 "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'POC_FAILED'"
    )
    op.execute(
        "UPDATE statuses SET label = '6- PoC Successful', sort_order = 80 "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'POC_SUCCESSFUL'"
    )
    op.execute(
        "UPDATE statuses SET label = '7- Partnered', sort_order = 90 "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'PARTNERED'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE statuses SET label = 'Information Received' "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'INFORMATION_RECEIVED'"
    )
    op.execute(
        "UPDATE statuses SET label = 'Meeting Held' "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'MEETING_HELD'"
    )
    op.execute(
        "UPDATE statuses SET label = 'Not a Fit' "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'NOT_A_FIT'"
    )
    op.execute(
        "UPDATE statuses SET label = 'In Progress' "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'IN_PROGRESS'"
    )
    op.execute("UPDATE statuses SET label = 'NDA' WHERE status_group = 'COMPANY_STATUS' AND code = 'NDA'")
    op.execute(
        "UPDATE statuses SET label = 'PoC in Progress' "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'POC_IN_PROGRESS'"
    )
    op.execute(
        "UPDATE statuses SET label = 'PoC Failed' "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'POC_FAILED'"
    )
    op.execute(
        "UPDATE statuses SET label = 'PoC Successful' "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'POC_SUCCESSFUL'"
    )
    op.execute(
        "UPDATE statuses SET label = 'Partnered' "
        "WHERE status_group = 'COMPANY_STATUS' AND code = 'PARTNERED'"
    )
