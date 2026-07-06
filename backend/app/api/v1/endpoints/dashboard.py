from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from datetime import date

from app.models import BorusanCompany, Event, FollowUpAction, ImportBatch, Opportunity, Organization, OrganizationBorusanFit, OrganizationDocument, User
from app.services.champion_score import champion_leaderboard, champion_user_position
from app.services.soft_delete import archived, not_archived

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    def count_for(stmt: Any) -> int:
        try:
            return int(db.execute(stmt).scalar_one())
        except SQLAlchemyError:
            db.rollback()
            return 0

    latest_import = (
        db.execute(select(ImportBatch).order_by(ImportBatch.created_at.desc(), ImportBatch.id.desc()).limit(1))
        .scalars()
        .first()
    )
    fit_rows = db.execute(
        select(BorusanCompany.code, BorusanCompany.english_name, BorusanCompany.name, func.count(OrganizationBorusanFit.id))
        .join(OrganizationBorusanFit, OrganizationBorusanFit.borusan_company_id == BorusanCompany.id)
        .where(not_archived(OrganizationBorusanFit.is_archived))
        .group_by(BorusanCompany.code, BorusanCompany.english_name, BorusanCompany.name)
        .order_by(func.count(OrganizationBorusanFit.id).desc(), BorusanCompany.code.asc())
    ).all()
    champion_rows = champion_leaderboard(db, period="last_30_days", limit=1).get("items", [])
    my_champion = champion_user_position(db, user=current_user, period="last_30_days")

    return {
        "total_organizations": count_for(select(func.count()).select_from(Organization).where(not_archived(Organization.is_archived))),
        "total_startups": count_for(
            select(func.count()).select_from(Organization).where(Organization.organization_type == "STARTUP", not_archived(Organization.is_archived))
        ),
        "total_vendors": count_for(
            select(func.count()).select_from(Organization).where(Organization.organization_type == "VENDOR", not_archived(Organization.is_archived))
        ),
        "total_opportunities": count_for(select(func.count()).select_from(Opportunity).where(not_archived(Opportunity.is_archived))),
        "total_events": count_for(select(func.count()).select_from(Event).where(not_archived(Event.is_archived))),
        "open_follow_ups": count_for(
            select(func.count()).select_from(FollowUpAction).where(FollowUpAction.status == "OPEN", not_archived(FollowUpAction.is_archived))
        ),
        "overdue_follow_ups": count_for(
            select(func.count())
            .select_from(FollowUpAction)
            .where(FollowUpAction.status == "OPEN", FollowUpAction.due_date < date.today(), not_archived(FollowUpAction.is_archived))
        ),
        "total_startup_decks": count_for(
            select(func.count()).select_from(OrganizationDocument).where(not_archived(OrganizationDocument.is_archived))
        ),
        "total_network_institutions": count_for(
            select(func.count()).select_from(Organization).where(Organization.organization_type == "NETWORK_INSTITUTION", not_archived(Organization.is_archived))
        ),
        "archived_organizations": count_for(select(func.count()).select_from(Organization).where(archived(Organization.is_archived))),
        "archived_opportunities": count_for(select(func.count()).select_from(Opportunity).where(archived(Opportunity.is_archived))),
        "archived_events": count_for(select(func.count()).select_from(Event).where(archived(Event.is_archived))),
        "active_imported_batches": count_for(
            select(func.count()).select_from(ImportBatch).where(ImportBatch.status != "COMMITTED")
        ),
        "latest_import_status": latest_import.status if latest_import else None,
        "latest_import_filename": latest_import.original_filename if latest_import else None,
        "top_borusan_company_fit_counts": [
            {"code": code, "name": english_name or name, "count": count} for code, english_name, name, count in fit_rows
        ],
        "top_champion": champion_rows[0] if champion_rows else None,
        "my_champion_score": my_champion,
    }
