from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User, UserContribution
from app.services.champion_score import CHAMPION_RULES, champion_leaderboard, champion_user_detail, champion_user_position
from app.services.soft_delete import not_excluded

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

PERIODS = {
    "all_time": None,
    "last_30_days": timedelta(days=30),
    "last_7_days": timedelta(days=7),
}

METRIC_TO_FIELD = {
    "points": "total_points",
    "organizations": "organizations_created",
    "notes": "notes_created",
    "contacts": "contacts_created",
    "opportunities": "opportunities_created",
}

CONTRIBUTION_FIELDS = {
    "ORGANIZATION_CREATED": "organizations_created",
    "CONTACT_CREATED": "contacts_created",
    "NOTE_CREATED": "notes_created",
    "BORUSAN_FIT_CREATED": "borusan_fits_created",
    "OPPORTUNITY_CREATED": "opportunities_created",
    "USE_CASE_CREATED": "use_cases_created",
    "EVENT_CREATED": "events_created",
    "AI_TOOL_CREATED": "ai_tools_created",
    "ORGANIZATION_UPDATED": "updates_count",
    "FOLLOW_UP_COMPLETED": "follow_ups_completed",
}


def _period_start(period: str) -> datetime | None:
    delta = PERIODS.get(period)
    if delta is None:
        return None
    return datetime.now(timezone.utc) - delta


def _base_rows(db: Session, period: str) -> list[dict[str, Any]]:
    stmt = select(UserContribution).where(UserContribution.source == "MANUAL", not_excluded(UserContribution.is_excluded))
    start = _period_start(period)
    if start:
        stmt = stmt.where(UserContribution.occurred_at >= start)
    contributions = db.execute(stmt.order_by(UserContribution.occurred_at.desc())).scalars().all()

    rows_by_user: dict[UUID, dict[str, Any]] = {}
    for contribution in contributions:
        user = db.get(User, contribution.user_id)
        if user is None:
            continue
        row = rows_by_user.setdefault(
            user.id,
            {
                "rank": 0,
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "total_points": 0,
                "organizations_created": 0,
                "contacts_created": 0,
                "notes_created": 0,
                "borusan_fits_created": 0,
                "opportunities_created": 0,
                "use_cases_created": 0,
                "events_created": 0,
                "ai_tools_created": 0,
                "updates_count": 0,
                "follow_ups_completed": 0,
                "last_contribution_at": None,
            },
        )
        row["total_points"] += contribution.points
        field_name = CONTRIBUTION_FIELDS.get(contribution.contribution_type)
        if field_name:
            row[field_name] += 1
        last_at = row["last_contribution_at"]
        if last_at is None or contribution.occurred_at > last_at:
            row["last_contribution_at"] = contribution.occurred_at

    return list(rows_by_user.values())


def _ranked_rows(db: Session, period: str, metric: str) -> list[dict[str, Any]]:
    rows = _base_rows(db, period)
    sort_field = METRIC_TO_FIELD.get(metric, "total_points")
    rows.sort(
        key=lambda row: (
            row.get(sort_field) or 0,
            row["total_points"],
            _timestamp(row["last_contribution_at"]),
        ),
        reverse=True,
    )
    previous_key: tuple[Any, ...] | None = None
    rank = 0
    for index, row in enumerate(rows, start=1):
        current_key = (row.get(sort_field) or 0, row["total_points"])
        if current_key != previous_key:
            rank = index
            previous_key = current_key
        row["rank"] = rank
    return rows


def _timestamp(value: datetime | None) -> float:
    if value is None:
        return 0.0
    return value.timestamp()


@router.get("/champion")
async def get_champion_leaderboard(
    period: str = Query(default="all_time", pattern="^(all_time|last_30_days|last_7_days)$"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    return champion_leaderboard(db, period=period, limit=limit)


@router.get("/champion/me")
async def get_my_champion_score(
    period: str = Query(default="all_time", pattern="^(all_time|last_30_days|last_7_days)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return champion_user_position(db, user=current_user, period=period)


@router.get("/champion/rules")
async def get_champion_score_rules(_: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"items": CHAMPION_RULES}


@router.get("/champion/users/{user_id}")
async def get_champion_user_detail(
    user_id: UUID,
    period: str = Query(default="all_time", pattern="^(all_time|last_30_days|last_7_days)$"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    detail = champion_user_detail(db, user_id=user_id, period=period)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return detail


@router.get("")
async def get_leaderboard(
    period: str = Query(default="all_time", pattern="^(all_time|last_30_days|last_7_days)$"),
    metric: str = Query(default="points", pattern="^(points|organizations|notes|contacts|opportunities)$"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    rows = _ranked_rows(db, period, metric)
    return {
        "period": period,
        "metric": metric,
        "items": rows[:limit],
        "total_users": len(rows),
        "manual_only": True,
    }


@router.get("/me")
async def get_my_leaderboard_position(
    period: str = Query(default="all_time", pattern="^(all_time|last_30_days|last_7_days)$"),
    metric: str = Query(default="points", pattern="^(points|organizations|notes|contacts|opportunities)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    rows = _ranked_rows(db, period, metric)
    for row in rows:
        if row["user_id"] == current_user.id:
            return {"period": period, "metric": metric, **row}
    return {
        "period": period,
        "metric": metric,
        "rank": None,
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "total_points": 0,
        "organizations_created": 0,
        "contacts_created": 0,
        "notes_created": 0,
        "borusan_fits_created": 0,
        "opportunities_created": 0,
        "use_cases_created": 0,
        "events_created": 0,
        "ai_tools_created": 0,
        "updates_count": 0,
        "follow_ups_completed": 0,
        "last_contribution_at": None,
    }
