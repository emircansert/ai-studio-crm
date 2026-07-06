from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import ChampionActivity, User, UserContribution
from app.schemas import LeaderboardResetRequest, LeaderboardResetResponse
from app.services.audit import write_audit_log
from app.services.soft_delete import not_archived, not_excluded

router = APIRouter(prefix="/admin/leaderboard", tags=["admin-leaderboard"])


@router.post("/reset", response_model=LeaderboardResetResponse)
async def reset_leaderboard(
    payload: LeaderboardResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> LeaderboardResetResponse:
    scope = payload.scope.lower()
    if scope not in {"all", "user"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scope must be all or user")
    if scope == "user" and payload.user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required when scope=user")
    if not payload.reason.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="reason is required")

    contribution_stmt = select(UserContribution).where(
        UserContribution.source == "MANUAL",
        not_excluded(UserContribution.is_excluded),
    )
    champion_stmt = select(ChampionActivity).where(not_archived(ChampionActivity.is_archived))
    if scope == "user":
        contribution_stmt = contribution_stmt.where(UserContribution.user_id == payload.user_id)
        champion_stmt = champion_stmt.where(ChampionActivity.user_id == payload.user_id)

    contribution_count = int(db.execute(select(func.count()).select_from(contribution_stmt.subquery())).scalar_one())
    champion_count = int(db.execute(select(func.count()).select_from(champion_stmt.subquery())).scalar_one())
    affected_count = contribution_count + champion_count

    if payload.dry_run:
        return LeaderboardResetResponse(
            scope=scope,
            user_id=payload.user_id,
            affected_count=affected_count,
            crm_activity_affected_count=contribution_count,
            champion_activity_affected_count=champion_count,
            dry_run=True,
            reset_applied=False,
        )

    now = datetime.now(timezone.utc)
    contributions = db.execute(contribution_stmt).scalars().all()
    for contribution in contributions:
        contribution.is_excluded = True
        contribution.excluded_at = now
        contribution.excluded_by_user_id = current_user.id
        contribution.exclusion_reason = payload.reason
        db.add(contribution)

    champion_activities = db.execute(champion_stmt).scalars().all()
    for activity in champion_activities:
        activity.is_archived = True
        activity.archived_at = now
        activity.archived_by_user_id = current_user.id
        activity.archive_reason = payload.reason
        db.add(activity)

    await write_audit_log(
        db,
        action="LEADERBOARD_RESET",
        entity_type="LEADERBOARD",
        entity_id=payload.user_id if scope == "user" else None,
        actor_user_id=current_user.id,
        after_data={
            "scope": scope,
            "user_id": str(payload.user_id) if payload.user_id else None,
            "affected_count": affected_count,
            "crm_activity_affected_count": contribution_count,
            "champion_activity_affected_count": champion_count,
            "reason": payload.reason,
        },
    )
    db.commit()

    return LeaderboardResetResponse(
        scope=scope,
        user_id=payload.user_id,
        affected_count=affected_count,
        crm_activity_affected_count=contribution_count,
        champion_activity_affected_count=champion_count,
        dry_run=False,
        reset_applied=True,
    )
