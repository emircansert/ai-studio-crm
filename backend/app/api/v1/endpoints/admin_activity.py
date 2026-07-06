from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import CrmActivityEvent, User
from app.schemas import CrmActivityEventRead

router = APIRouter(prefix="/admin/activity", tags=["admin-activity"])


@router.get("", response_model=list[CrmActivityEventRead])
async def list_crm_activity(
    q: str | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[CrmActivityEvent]:
    stmt = select(CrmActivityEvent)
    if action:
        stmt = stmt.where(CrmActivityEvent.action == action)
    if entity_type:
        stmt = stmt.where(CrmActivityEvent.entity_type == entity_type)
    if q:
        q_like = f"%{q}%"
        stmt = stmt.where(
            or_(
                CrmActivityEvent.title.ilike(q_like),
                CrmActivityEvent.summary.ilike(q_like),
                CrmActivityEvent.action.ilike(q_like),
                CrmActivityEvent.entity_type.ilike(q_like),
            )
        )
    return list(
        db.execute(stmt.order_by(CrmActivityEvent.created_at.desc(), CrmActivityEvent.id.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
