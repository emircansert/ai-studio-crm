from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import Note, User
from app.schemas import ArchiveRequest, NoteRead, NoteUpdate
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.crud import CRUDService

router = APIRouter(prefix="/notes", tags=["notes"])
service = CRUDService[Note, NoteUpdate, NoteUpdate](Note)


@router.put("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: UUID,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Note:
    note = await service.get(db, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    before = NoteRead.model_validate(note).model_dump(mode="json")
    for field_name, value in payload.model_dump(exclude_unset=True, exclude={"created_by_user_id"}).items():
        setattr(note, field_name, value)
    db.add(note)
    db.commit()
    db.refresh(note)
    await write_audit_log(
        db,
        action="NOTE_UPDATED",
        entity_type="NOTE",
        entity_id=note.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=NoteRead.model_validate(note).model_dump(mode="json"),
        commit=True,
    )
    return note


@router.patch("/{note_id}/archive", response_model=NoteRead)
async def archive_note(
    note_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Note:
    return await archive_record(
        db,
        await service.get(db, note_id),
        entity_type="NOTE",
        entity_id=note_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.patch("/{note_id}/unarchive", response_model=NoteRead)
async def unarchive_note(
    note_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Note:
    return await unarchive_record(
        db,
        await service.get(db, note_id),
        entity_type="NOTE",
        entity_id=note_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    note = await service.get(db, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    await archive_record(
        db,
        note,
        entity_type="NOTE",
        entity_id=note_id,
        actor=current_user,
        reason="Archived via legacy DELETE endpoint",
    )
