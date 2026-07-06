from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import ChampionActivity, User
from app.schemas import ArchiveRequest, ChampionActivityCreate, ChampionActivityRead, ChampionActivityUpdate
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.soft_delete import not_archived

router = APIRouter(prefix="/admin/champion-activities", tags=["admin-champion-activities"])


def _user_payload(db: Session, user_id: UUID | None) -> dict[str, Any] | None:
    if not user_id:
        return None
    user = db.get(User, user_id)
    if user is None:
        return {"id": user_id, "full_name": None, "email": None}
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}


def _activity_payload(db: Session, activity: ChampionActivity) -> dict[str, Any]:
    data = ChampionActivityRead.model_validate(activity).model_dump(mode="json")
    data["user"] = _user_payload(db, activity.user_id)
    data["created_by_user"] = _user_payload(db, activity.created_by_user_id)
    return data


@router.get("")
async def list_champion_activities(
    user_id: UUID | None = None,
    category: str | None = None,
    activity_type: str | None = None,
    source: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    from_date: date | None = None,
    to_date: date | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    stmt = select(ChampionActivity)
    if not include_archived:
        stmt = stmt.where(not_archived(ChampionActivity.is_archived))
    if user_id:
        stmt = stmt.where(ChampionActivity.user_id == user_id)
    if category:
        stmt = stmt.where(ChampionActivity.category == category)
    if activity_type:
        stmt = stmt.where(ChampionActivity.activity_type == activity_type)
    if source:
        stmt = stmt.where(ChampionActivity.source == source)
    if status_filter:
        stmt = stmt.where(ChampionActivity.status == status_filter)
    if from_date:
        stmt = stmt.where(ChampionActivity.activity_date >= datetime.combine(from_date, time.min))
    if to_date:
        stmt = stmt.where(ChampionActivity.activity_date <= datetime.combine(to_date, time.max))

    rows = db.execute(
        stmt.order_by(ChampionActivity.activity_date.desc(), ChampionActivity.created_at.desc(), ChampionActivity.id.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()
    return {
        "items": [_activity_payload(db, row) for row in rows],
        "limit": limit,
        "offset": skip,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_champion_activity(
    payload: ChampionActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    data = payload.model_dump(exclude_unset=True)
    data["source"] = data.get("source") or "ADMIN_RECORDED"
    data["status"] = data.get("status") or "ACTIVE"
    data["quantity"] = max(int(data.get("quantity") or 1), 1)
    data["created_by_user_id"] = current_user.id
    activity = ChampionActivity(**data)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    response = _activity_payload(db, activity)
    await write_audit_log(
        db,
        action="CHAMPION_ACTIVITY_CREATED",
        entity_type="CHAMPION_ACTIVITY",
        entity_id=activity.id,
        actor_user_id=current_user.id,
        after_data=response,
        commit=True,
    )
    return response


@router.put("/{activity_id}")
async def update_champion_activity(
    activity_id: UUID,
    payload: ChampionActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    activity = db.get(ChampionActivity, activity_id)
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Champion activity not found")
    before = _activity_payload(db, activity)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        if field_name == "quantity" and value is not None:
            value = max(int(value), 1)
        setattr(activity, field_name, value)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    after = _activity_payload(db, activity)
    await write_audit_log(
        db,
        action="CHAMPION_ACTIVITY_UPDATED",
        entity_type="CHAMPION_ACTIVITY",
        entity_id=activity.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=after,
        commit=True,
    )
    return after


@router.patch("/{activity_id}/archive")
async def archive_champion_activity(
    activity_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    activity = await archive_record(
        db,
        db.get(ChampionActivity, activity_id),
        entity_type="CHAMPION_ACTIVITY",
        entity_id=activity_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _activity_payload(db, activity)


@router.patch("/{activity_id}/unarchive")
async def unarchive_champion_activity(
    activity_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    activity = await unarchive_record(
        db,
        db.get(ChampionActivity, activity_id),
        entity_type="CHAMPION_ACTIVITY",
        entity_id=activity_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _activity_payload(db, activity)
