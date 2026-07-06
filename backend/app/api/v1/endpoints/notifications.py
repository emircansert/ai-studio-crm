from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import false, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Notification, User
from app.schemas import NotificationRead, NotificationUnreadCount

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        stmt = stmt.where(Notification.is_read == false())
    return list(
        db.execute(stmt.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCount:
    count = int(
        db.execute(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == current_user.id,
                Notification.is_read == false(),
            )
        ).scalar_one()
    )
    return NotificationUnreadCount(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.add(notification)
        db.commit()
        db.refresh(notification)
    return notification


@router.patch("/read-all", response_model=NotificationUnreadCount)
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationUnreadCount:
    rows = db.execute(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read == false(),
        )
    ).scalars().all()
    now = datetime.now(timezone.utc)
    for notification in rows:
        notification.is_read = True
        notification.read_at = now
        db.add(notification)
    db.commit()
    return NotificationUnreadCount(unread_count=0)
