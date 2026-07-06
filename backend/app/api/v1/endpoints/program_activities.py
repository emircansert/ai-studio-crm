from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import ProgramActivity, ProgramActivityParticipant, User
from app.schemas import (
    ArchiveRequest,
    ProgramActivityCreate,
    ProgramActivityParticipantCreate,
    ProgramActivityParticipantRead,
    ProgramActivityParticipantUpdate,
    ProgramActivityRead,
    ProgramActivityUpdate,
)
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.champion_score import write_champion_activity
from app.services.soft_delete import not_archived

router = APIRouter()


def _user_payload(db: Session, user_id: UUID | None) -> dict[str, Any] | None:
    if not user_id:
        return None
    user = db.get(User, user_id)
    if user is None:
        return {"id": user_id, "full_name": None, "email": None}
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}


def _participant_payload(db: Session, participant: ProgramActivityParticipant) -> dict[str, Any]:
    data = ProgramActivityParticipantRead.model_validate(participant).model_dump(mode="json")
    data["user"] = _user_payload(db, participant.user_id)
    data["recorded_by_user"] = _user_payload(db, participant.recorded_by_user_id)
    return data


def _activity_payload(db: Session, activity: ProgramActivity, include_participants: bool = True) -> dict[str, Any]:
    data = ProgramActivityRead.model_validate(activity).model_dump(mode="json")
    data["created_by_user"] = _user_payload(db, activity.created_by_user_id)
    data["participant_count"] = db.scalar(
        select(func.count(ProgramActivityParticipant.id)).where(ProgramActivityParticipant.program_activity_id == activity.id)
    ) or 0
    if include_participants:
        participants = db.execute(
            select(ProgramActivityParticipant)
            .where(ProgramActivityParticipant.program_activity_id == activity.id)
            .order_by(ProgramActivityParticipant.created_at.desc(), ProgramActivityParticipant.id.desc())
        ).scalars().all()
        data["participants"] = [_participant_payload(db, participant) for participant in participants]
    return data


@router.get("")
async def list_program_activities(
    q: str | None = None,
    activity_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    stmt = select(ProgramActivity)
    if not include_archived or current_user.role != "ADMIN":
        stmt = stmt.where(not_archived(ProgramActivity.is_archived))
    if activity_type and activity_type.upper() != "ALL":
        stmt = stmt.where(ProgramActivity.activity_type == activity_type.upper())
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                ProgramActivity.title.ilike(pattern),
                ProgramActivity.description.ilike(pattern),
                ProgramActivity.location_text.ilike(pattern),
                ProgramActivity.owner_team.ilike(pattern),
                ProgramActivity.tracking_owner.ilike(pattern),
            )
        )
    if date_from:
        stmt = stmt.where(ProgramActivity.activity_date >= date_from)
    if date_to:
        stmt = stmt.where(ProgramActivity.activity_date <= date_to)
    rows = db.execute(
        stmt.order_by(ProgramActivity.activity_date.desc(), ProgramActivity.created_at.desc(), ProgramActivity.id.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()
    return {"items": [_activity_payload(db, row, include_participants=False) for row in rows], "limit": limit, "offset": skip}


@router.get("/{activity_id}")
async def get_program_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    activity = db.get(ProgramActivity, activity_id)
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program activity not found")
    return _activity_payload(db, activity)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_program_activity(
    payload: ProgramActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    data = payload.model_dump(exclude_unset=True)
    data["created_by_user_id"] = current_user.id
    activity = ProgramActivity(**data)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    response = _activity_payload(db, activity)
    await write_audit_log(
        db,
        action="PROGRAM_ACTIVITY_CREATED",
        entity_type="PROGRAM_ACTIVITY",
        entity_id=activity.id,
        actor_user_id=current_user.id,
        after_data=response,
        commit=True,
    )
    return response


@router.put("/{activity_id}")
async def update_program_activity(
    activity_id: UUID,
    payload: ProgramActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    activity = db.get(ProgramActivity, activity_id)
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program activity not found")
    before = _activity_payload(db, activity)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(activity, field_name, value)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    response = _activity_payload(db, activity)
    await write_audit_log(
        db,
        action="PROGRAM_ACTIVITY_UPDATED",
        entity_type="PROGRAM_ACTIVITY",
        entity_id=activity.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=response,
        commit=True,
    )
    return response


@router.post("/{activity_id}/participants", status_code=status.HTTP_201_CREATED)
async def create_program_activity_participant(
    activity_id: UUID,
    payload: ProgramActivityParticipantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    activity = db.get(ProgramActivity, activity_id)
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program activity not found")
    data = payload.model_dump(exclude_unset=True)
    data.pop("program_activity_id", None)
    participant = ProgramActivityParticipant(program_activity_id=activity_id, recorded_by_user_id=current_user.id, **data)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    await _sync_participant_score(db, activity, participant, current_user)
    response = _participant_payload(db, participant)
    await write_audit_log(
        db,
        action="PROGRAM_ACTIVITY_PARTICIPANT_CREATED",
        entity_type="PROGRAM_ACTIVITY_PARTICIPANT",
        entity_id=participant.id,
        actor_user_id=current_user.id,
        after_data=response,
        commit=True,
    )
    return response


@router.put("/{activity_id}/participants/{participant_id}")
async def update_program_activity_participant(
    activity_id: UUID,
    participant_id: UUID,
    payload: ProgramActivityParticipantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    activity = db.get(ProgramActivity, activity_id)
    participant = db.get(ProgramActivityParticipant, participant_id)
    if activity is None or participant is None or participant.program_activity_id != activity_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program activity participant not found")
    before = _participant_payload(db, participant)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(participant, field_name, value)
    participant.recorded_by_user_id = current_user.id
    db.add(participant)
    db.commit()
    db.refresh(participant)
    await _sync_participant_score(db, activity, participant, current_user)
    response = _participant_payload(db, participant)
    await write_audit_log(
        db,
        action="PROGRAM_ACTIVITY_PARTICIPANT_UPDATED",
        entity_type="PROGRAM_ACTIVITY_PARTICIPANT",
        entity_id=participant.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=response,
        commit=True,
    )
    return response


async def _sync_participant_score(
    db: Session,
    activity: ProgramActivity,
    participant: ProgramActivityParticipant,
    current_user: User,
) -> None:
    activity_date = None
    if activity.activity_date:
        activity_date = datetime.combine(activity.activity_date, time(hour=12))
    if activity.activity_type == "EVENT" and participant.attendance_status == "ATTENDED":
        await write_champion_activity(
            db,
            user_id=participant.user_id,
            category="COMMUNICATION_EVENT",
            activity_type="EVENT_PARTICIPATION",
            related_entity_type="PROGRAM_ACTIVITY_PARTICIPANT",
            related_entity_id=participant.id,
            activity_date=activity_date,
            source="ADMIN_RECORDED",
            status="ACTIVE",
            notes=activity.title,
            created_by_user_id=current_user.id,
            commit=True,
        )
    if activity.activity_type == "TRAINING" and participant.completion_status == "COMPLETED":
        await write_champion_activity(
            db,
            user_id=participant.user_id,
            category="TRAINING",
            activity_type="TRAINING_COMPLETED",
            related_entity_type="PROGRAM_ACTIVITY_PARTICIPANT",
            related_entity_id=participant.id,
            activity_date=activity_date,
            source="ADMIN_RECORDED",
            status="ACTIVE",
            notes=activity.title,
            created_by_user_id=current_user.id,
            commit=True,
        )


@router.patch("/{activity_id}/archive")
async def archive_program_activity(
    activity_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    record = await archive_record(
        db,
        db.get(ProgramActivity, activity_id),
        entity_type="PROGRAM_ACTIVITY",
        entity_id=activity_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _activity_payload(db, record)


@router.patch("/{activity_id}/unarchive")
async def unarchive_program_activity(
    activity_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    record = await unarchive_record(
        db,
        db.get(ProgramActivity, activity_id),
        entity_type="PROGRAM_ACTIVITY",
        entity_id=activity_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _activity_payload(db, record)
