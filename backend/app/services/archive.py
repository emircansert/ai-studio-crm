from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.services.audit import write_audit_log


async def archive_record(
    db: Session,
    record: Any | None,
    *,
    entity_type: str,
    entity_id: UUID,
    actor: User,
    reason: str | None = None,
    commit: bool = True,
) -> Any:
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_type.replace('_', ' ').title()} not found")
    before = _archive_payload(record)
    record.is_archived = True
    record.archived_at = datetime.now(timezone.utc)
    record.archived_by_user_id = actor.id
    record.archive_reason = reason
    db.add(record)
    await write_audit_log(
        db,
        action=f"{entity_type}_ARCHIVED",
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor.id,
        before_data=before,
        after_data={**_archive_payload(record), "reason": reason},
    )
    if commit:
        db.commit()
        db.refresh(record)
    return record


async def unarchive_record(
    db: Session,
    record: Any | None,
    *,
    entity_type: str,
    entity_id: UUID,
    actor: User,
    reason: str | None = None,
    commit: bool = True,
) -> Any:
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_type.replace('_', ' ').title()} not found")
    before = _archive_payload(record)
    record.is_archived = False
    record.archived_at = None
    record.archived_by_user_id = None
    record.archive_reason = None
    db.add(record)
    await write_audit_log(
        db,
        action=f"{entity_type}_UNARCHIVED",
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor.id,
        before_data=before,
        after_data={**_archive_payload(record), "reason": reason},
    )
    if commit:
        db.commit()
        db.refresh(record)
    return record


def _archive_payload(record: Any) -> dict[str, Any]:
    return {
        "is_archived": bool(getattr(record, "is_archived", False)),
        "archived_at": getattr(record, "archived_at", None).isoformat()
        if getattr(record, "archived_at", None)
        else None,
        "archived_by_user_id": str(getattr(record, "archived_by_user_id", None))
        if getattr(record, "archived_by_user_id", None)
        else None,
        "archive_reason": getattr(record, "archive_reason", None),
    }
