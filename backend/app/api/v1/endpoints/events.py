from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import Event, User
from app.schemas import ArchiveRequest, EventCreate, EventRead, EventUpdate
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.champion_score import write_champion_activity
from app.services.contributions import write_user_contribution
from app.services.crud import CRUDService

router = APIRouter(prefix="/events", tags=["events"])
service = CRUDService[Event, EventCreate, EventUpdate](Event)


@router.get("", response_model=list[EventRead])
async def list_events(
    ai_program_relevance: str | None = None,
    value_creation_potential: str | None = None,
    geography_text: str | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Event]:
    return list(
        await service.list(
            db,
            skip=skip,
            limit=limit,
            filters={
                "ai_program_relevance": ai_program_relevance,
                "value_creation_potential": value_creation_potential,
                "geography_text": geography_text,
            },
            order_by=[Event.starts_on.desc(), Event.created_at.desc(), Event.id.desc()],
            include_archived=include_archived and current_user.role == "ADMIN",
        )
    )


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Event:
    event = await service.get(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Event:
    data = payload.model_dump(exclude_unset=True)
    data["created_by_user_id"] = current_user.id
    data["updated_by_user_id"] = current_user.id
    event = Event(**data)
    db.add(event)
    db.commit()
    db.refresh(event)
    await write_audit_log(
        db,
        action="EVENT_CREATED",
        entity_type="EVENT",
        entity_id=event.id,
        actor_user_id=current_user.id,
        after_data=EventRead.model_validate(event).model_dump(mode="json"),
        commit=True,
    )
    await write_user_contribution(
        db,
        user_id=current_user.id,
        contribution_type="EVENT_CREATED",
        entity_type="EVENT",
        entity_id=event.id,
        metadata_json={"name": event.name},
        commit=True,
    )
    await write_champion_activity(
        db,
        user_id=current_user.id,
        category="ECOSYSTEM_LIBRARY",
        activity_type="EVENT_ADDED",
        related_entity_type="EVENT",
        related_entity_id=event.id,
        notes=event.name,
        created_by_user_id=current_user.id,
        commit=True,
    )
    return event


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: UUID,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Event:
    event = await service.get(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    before = EventRead.model_validate(event).model_dump(mode="json")
    data = payload.model_dump(exclude_unset=True)
    data["updated_by_user_id"] = current_user.id
    for field_name, value in data.items():
        setattr(event, field_name, value)
    db.add(event)
    db.commit()
    db.refresh(event)
    await write_audit_log(
        db,
        action="EVENT_UPDATED",
        entity_type="EVENT",
        entity_id=event.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=EventRead.model_validate(event).model_dump(mode="json"),
        commit=True,
    )
    return event


@router.put("/{event_id}", response_model=EventRead)
async def put_event(
    event_id: UUID,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Event:
    return await update_event(event_id, payload, db, current_user)


@router.patch("/{event_id}/archive", response_model=EventRead)
async def archive_event(
    event_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Event:
    return await archive_record(
        db,
        await service.get(db, event_id),
        entity_type="EVENT",
        entity_id=event_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.patch("/{event_id}/unarchive", response_model=EventRead)
async def unarchive_event(
    event_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Event:
    return await unarchive_record(
        db,
        await service.get(db, event_id),
        entity_type="EVENT",
        entity_id=event_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
