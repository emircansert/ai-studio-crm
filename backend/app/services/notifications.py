from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import CrmActivityEvent, Notification


CRM_ACTIVITY_ENTITY_TYPES = {
    "AI_TOOL",
    "CONTACT",
    "EVENT",
    "FOLLOW_UP_ACTION",
    "IMPORT_BATCH",
    "NOTE",
    "OPPORTUNITY",
    "OPPORTUNITY_DOCUMENT",
    "ORGANIZATION",
    "ORGANIZATION_BORUSAN_FIT",
    "ORGANIZATION_DOCUMENT",
    "PROGRAM_ACTIVITY",
    "PROGRAM_ACTIVITY_PARTICIPANT",
    "USE_CASE_PROPOSAL",
    "VENDOR",
    "VENDOR_RATING",
}

CRM_ACTIVITY_ACTIONS = {
    "AI_TOOL_CREATED",
    "AI_TOOL_UPDATED",
    "BORUSAN_FIT_CREATED",
    "BORUSAN_FIT_UPDATED",
    "CONTACT_CREATED",
    "CONTACT_UPDATED",
    "EVENT_CREATED",
    "EVENT_UPDATED",
    "FOLLOW_UP_ASSIGNED",
    "FOLLOW_UP_CANCELLED",
    "FOLLOW_UP_CREATED",
    "FOLLOW_UP_DONE",
    "FOLLOW_UP_UPDATED",
    "IMPORT_UPLOAD_STAGED",
    "NOTE_CREATED",
    "NOTE_UPDATED",
    "OPPORTUNITY_CREATED",
    "OPPORTUNITY_DOCUMENT_UPLOADED",
    "OPPORTUNITY_STAGE_UPDATED",
    "OPPORTUNITY_UPDATED",
    "ORGANIZATION_CREATED",
    "ORGANIZATION_LAST_CONTACT_CHANGED",
    "ORGANIZATION_STATUS_CHANGED",
    "ORGANIZATION_UPDATED",
    "PROGRAM_ACTIVITY_CREATED",
    "PROGRAM_ACTIVITY_PARTICIPANT_CREATED",
    "PROGRAM_ACTIVITY_PARTICIPANT_UPDATED",
    "PROGRAM_ACTIVITY_UPDATED",
    "STARTUP_DECK_UPLOADED",
    "USE_CASE_CREATED",
    "USE_CASE_UPDATED",
    "VENDOR_CREATED",
    "VENDOR_RATING_DELETED",
    "VENDOR_RATING_UPDATED",
    "VENDOR_UPDATED",
}


def _json_safe(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    return json.loads(json.dumps(payload, ensure_ascii=False, default=str))


def _display_name(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    for key in ("name", "title", "original_filename", "email", "full_name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _humanize(value: str) -> str:
    return value.replace("_", " ").title()


def should_write_crm_activity(action: str, entity_type: str) -> bool:
    if action in CRM_ACTIVITY_ACTIONS:
        return True
    if action.endswith("_ARCHIVED") or action.endswith("_UNARCHIVED"):
        return entity_type in CRM_ACTIVITY_ENTITY_TYPES
    return False


def build_activity_title(
    *,
    action: str,
    entity_type: str,
    before_data: dict[str, Any] | None = None,
    after_data: dict[str, Any] | None = None,
) -> tuple[str, str | None]:
    payload = after_data or before_data
    display_name = _display_name(payload)
    action_label = _humanize(action)

    if action == "ORGANIZATION_CREATED":
        org_type = (after_data or {}).get("organization_type")
        noun = "Startup" if org_type == "STARTUP" else "Organization"
        return f"{noun} added{f': {display_name}' if display_name else ''}", None
    if action == "FOLLOW_UP_ASSIGNED":
        return f"Follow-up assigned{f': {display_name}' if display_name else ''}", "A follow-up was assigned to a CRM user."
    if action == "FOLLOW_UP_DONE":
        return f"Follow-up completed{f': {display_name}' if display_name else ''}", None
    if action == "STARTUP_DECK_UPLOADED":
        return f"Startup deck uploaded{f': {display_name}' if display_name else ''}", None
    if display_name:
        return f"{action_label}: {display_name}", None
    return f"{action_label} ({_humanize(entity_type)})", None


async def write_notification(
    db: Session,
    *,
    user_id: UUID | None,
    actor_user_id: UUID | None,
    notification_type: str,
    title: str,
    body: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    commit: bool = False,
) -> Notification | None:
    if user_id is None:
        return None
    notification = Notification(
        user_id=user_id,
        actor_user_id=actor_user_id,
        notification_type=notification_type,
        title=title,
        body=body,
        entity_type=entity_type,
        entity_id=entity_id,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    if commit:
        db.commit()
        db.refresh(notification)
    return notification


async def write_crm_activity_event(
    db: Session,
    *,
    action: str,
    entity_type: str,
    actor_user_id: UUID | None,
    entity_id: UUID | None = None,
    before_data: dict[str, Any] | None = None,
    after_data: dict[str, Any] | None = None,
    commit: bool = False,
) -> CrmActivityEvent | None:
    if not should_write_crm_activity(action, entity_type):
        return None
    title, summary = build_activity_title(
        action=action,
        entity_type=entity_type,
        before_data=before_data,
        after_data=after_data,
    )
    event = CrmActivityEvent(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        title=title,
        summary=summary,
        metadata_json=_json_safe(after_data or before_data),
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    return event
