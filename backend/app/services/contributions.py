from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import UserContribution

MANUAL_SOURCE = "MANUAL"

CONTRIBUTION_POINTS = {
    "ORGANIZATION_CREATED": 10,
    "CONTACT_CREATED": 3,
    "NOTE_CREATED": 2,
    "BORUSAN_FIT_CREATED": 3,
    "OPPORTUNITY_CREATED": 8,
    "USE_CASE_CREATED": 8,
    "EVENT_CREATED": 5,
    "AI_TOOL_CREATED": 5,
    "ORGANIZATION_UPDATED": 1,
    "FOLLOW_UP_COMPLETED": 2,
}


def contribution_points(contribution_type: str) -> int:
    return CONTRIBUTION_POINTS.get(contribution_type, 0)


async def write_user_contribution(
    db: Session,
    *,
    user_id: UUID | None,
    contribution_type: str,
    entity_type: str,
    entity_id: UUID | None,
    source: str = MANUAL_SOURCE,
    metadata_json: dict[str, Any] | None = None,
    points: int | None = None,
    commit: bool = False,
) -> UserContribution | None:
    if user_id is None or source != MANUAL_SOURCE:
        return None
    contribution = UserContribution(
        user_id=user_id,
        contribution_type=contribution_type,
        entity_type=entity_type,
        entity_id=entity_id,
        points=contribution_points(contribution_type) if points is None else points,
        source=source,
        occurred_at=datetime.now(timezone.utc),
        metadata_json=metadata_json,
        created_at=datetime.now(timezone.utc),
    )
    db.add(contribution)
    if commit:
        db.commit()
        db.refresh(contribution)
    return contribution
