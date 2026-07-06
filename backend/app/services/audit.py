import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog
from app.services.notifications import write_crm_activity_event


def _json_safe(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """Coerce UUIDs, datetimes, and other non-JSON types so the audit insert
    can never fail because a caller passed raw ORM values."""
    if payload is None:
        return None
    return json.loads(json.dumps(payload, ensure_ascii=False, default=str))


async def write_audit_log(
    db: Session,
    *,
    action: str,
    entity_type: str,
    actor_user_id: UUID | None = None,
    entity_id: UUID | None = None,
    before_data: dict[str, Any] | None = None,
    after_data: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    commit: bool = False,
) -> AuditLog:
    audit_log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_data=_json_safe(before_data),
        after_data=_json_safe(after_data),
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit_log)
    await write_crm_activity_event(
        db,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        before_data=before_data,
        after_data=after_data,
    )
    if commit:
        db.commit()
        db.refresh(audit_log)
    return audit_log
