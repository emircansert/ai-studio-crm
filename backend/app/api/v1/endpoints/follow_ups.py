from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import FollowUpAction, User
from app.schemas import ArchiveRequest, FollowUpActionCreate, FollowUpActionRead, FollowUpActionUpdate
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.champion_score import write_champion_activity
from app.services.contributions import write_user_contribution
from app.services.crud import CRUDService
from app.services.notifications import write_notification
from app.services.soft_delete import not_archived

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])
service = CRUDService[FollowUpAction, FollowUpActionCreate, FollowUpActionUpdate](FollowUpAction)


@router.get("", response_model=list[FollowUpActionRead])
async def list_follow_ups(
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    assigned_to_user_id: UUID | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FollowUpAction]:
    stmt = select(FollowUpAction)
    if not include_archived or current_user.role != "ADMIN":
        stmt = stmt.where(not_archived(FollowUpAction.is_archived))
    if entity_type:
        stmt = stmt.where(FollowUpAction.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(FollowUpAction.entity_id == entity_id)
    if status_filter:
        stmt = stmt.where(FollowUpAction.status == status_filter)
    if assigned_to_user_id:
        stmt = stmt.where(FollowUpAction.assigned_to_user_id == assigned_to_user_id)
    return list(
        db.execute(stmt.order_by(FollowUpAction.due_date.asc(), FollowUpAction.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )


@router.get("/{follow_up_id}", response_model=FollowUpActionRead)
async def get_follow_up(
    follow_up_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FollowUpAction:
    follow_up = await service.get(db, follow_up_id)
    if follow_up is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")
    return follow_up


@router.post("", response_model=FollowUpActionRead, status_code=status.HTTP_201_CREATED)
async def create_follow_up(
    payload: FollowUpActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpAction:
    data = payload.model_dump(exclude_unset=True)
    data["created_by_user_id"] = current_user.id
    follow_up = FollowUpAction(**data)
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    await write_audit_log(
        db,
        action="FOLLOW_UP_CREATED",
        entity_type="FOLLOW_UP_ACTION",
        entity_id=follow_up.id,
        actor_user_id=current_user.id,
        after_data=FollowUpActionRead.model_validate(follow_up).model_dump(mode="json"),
        commit=True,
    )
    if follow_up.assigned_to_user_id:
        await write_audit_log(
            db,
            action="FOLLOW_UP_ASSIGNED",
            entity_type="FOLLOW_UP_ACTION",
            entity_id=follow_up.id,
            actor_user_id=current_user.id,
            after_data={
                "assigned_to_user_id": str(follow_up.assigned_to_user_id),
                "entity_type": follow_up.entity_type,
                "entity_id": str(follow_up.entity_id),
                "title": follow_up.title,
            },
            commit=True,
        )
        await write_notification(
            db,
            user_id=follow_up.assigned_to_user_id,
            actor_user_id=current_user.id,
            notification_type="FOLLOW_UP_ASSIGNED",
            title=f"Follow-up assigned: {follow_up.title}",
            body=f"{current_user.full_name} assigned you a follow-up.",
            entity_type="FOLLOW_UP_ACTION",
            entity_id=follow_up.id,
            commit=True,
        )
    return follow_up


@router.put("/{follow_up_id}", response_model=FollowUpActionRead)
async def update_follow_up(
    follow_up_id: UUID,
    payload: FollowUpActionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpAction:
    follow_up = await service.get(db, follow_up_id)
    if follow_up is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")
    before = FollowUpActionRead.model_validate(follow_up).model_dump(mode="json")
    previous_assignee_id = follow_up.assigned_to_user_id
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(follow_up, field_name, value)
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    await write_audit_log(
        db,
        action="FOLLOW_UP_UPDATED",
        entity_type="FOLLOW_UP_ACTION",
        entity_id=follow_up.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=FollowUpActionRead.model_validate(follow_up).model_dump(mode="json"),
        commit=True,
    )
    if follow_up.assigned_to_user_id and follow_up.assigned_to_user_id != previous_assignee_id:
        await write_audit_log(
            db,
            action="FOLLOW_UP_ASSIGNED",
            entity_type="FOLLOW_UP_ACTION",
            entity_id=follow_up.id,
            actor_user_id=current_user.id,
            after_data={
                "assigned_to_user_id": str(follow_up.assigned_to_user_id),
                "entity_type": follow_up.entity_type,
                "entity_id": str(follow_up.entity_id),
                "title": follow_up.title,
            },
            commit=True,
        )
        await write_notification(
            db,
            user_id=follow_up.assigned_to_user_id,
            actor_user_id=current_user.id,
            notification_type="FOLLOW_UP_ASSIGNED",
            title=f"Follow-up assigned: {follow_up.title}",
            body=f"{current_user.full_name} assigned you a follow-up.",
            entity_type="FOLLOW_UP_ACTION",
            entity_id=follow_up.id,
            commit=True,
        )
    return follow_up


async def _set_follow_up_status(
    follow_up_id: UUID,
    next_status: str,
    db: Session,
    current_user: User,
) -> FollowUpAction:
    follow_up = await service.get(db, follow_up_id)
    if follow_up is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")
    before_status = follow_up.status
    follow_up.status = next_status
    if next_status == "DONE":
        follow_up.completed_by_user_id = current_user.id
        follow_up.completed_at = datetime.now(timezone.utc)
    db.add(follow_up)
    await write_audit_log(
        db,
        action=f"FOLLOW_UP_{next_status}",
        entity_type="FOLLOW_UP_ACTION",
        entity_id=follow_up.id,
        actor_user_id=current_user.id,
        before_data={"status": before_status},
        after_data={"status": next_status},
    )
    if next_status == "DONE" and before_status != "DONE":
        await write_user_contribution(
            db,
            user_id=current_user.id,
            contribution_type="FOLLOW_UP_COMPLETED",
            entity_type="FOLLOW_UP_ACTION",
            entity_id=follow_up.id,
            points=2,
            metadata_json={"title": follow_up.title},
        )
        await write_champion_activity(
            db,
            user_id=current_user.id,
            category="STARTUP_SCOUTING",
            activity_type="FOLLOW_UP_COMPLETED",
            related_entity_type="FOLLOW_UP",
            related_entity_id=follow_up.id,
            notes=follow_up.title,
            created_by_user_id=current_user.id,
        )
    db.commit()
    db.refresh(follow_up)
    return follow_up


@router.patch("/{follow_up_id}/complete", response_model=FollowUpActionRead)
async def complete_follow_up(
    follow_up_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpAction:
    return await _set_follow_up_status(follow_up_id, "DONE", db, current_user)


@router.patch("/{follow_up_id}/cancel", response_model=FollowUpActionRead)
async def cancel_follow_up(
    follow_up_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpAction:
    return await _set_follow_up_status(follow_up_id, "CANCELLED", db, current_user)


@router.patch("/{follow_up_id}/archive", response_model=FollowUpActionRead)
async def archive_follow_up(
    follow_up_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> FollowUpAction:
    return await archive_record(
        db,
        await service.get(db, follow_up_id),
        entity_type="FOLLOW_UP_ACTION",
        entity_id=follow_up_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.patch("/{follow_up_id}/unarchive", response_model=FollowUpActionRead)
async def unarchive_follow_up(
    follow_up_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> FollowUpAction:
    return await unarchive_record(
        db,
        await service.get(db, follow_up_id),
        entity_type="FOLLOW_UP_ACTION",
        entity_id=follow_up_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
