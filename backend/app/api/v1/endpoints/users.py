from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, true
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.core.section_access import get_user_section_access_map, section_definitions_payload
from app.db.session import get_db
from app.models import User
from app.schemas import CurrentUserSectionAccessResponse, Message, UserPasswordChange
from app.services.audit import write_audit_log

router = APIRouter(prefix="/users", tags=["users"])


def _active_user_payload(user: User) -> dict[str, object]:
    email = user.email or ""
    return {
        "id": user.id,
        "full_name": user.full_name or email or "CRM User",
        "email": email,
        "role": user.role or "USER",
        "is_active": bool(user.is_active),
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.get("/me/section-access", response_model=CurrentUserSectionAccessResponse)
async def get_my_section_access(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    return {
        "sections": section_definitions_payload(),
        "access": get_user_section_access_map(db, current_user),
    }


@router.patch("/me/change-password", response_model=Message)
async def change_my_password(
    payload: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Message:
    if settings.is_entra_auth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords are managed by Microsoft Entra ID. Local password changes are disabled.",
        )
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if verify_password(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different from the current password")

    current_user.password_hash = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    await write_audit_log(
        db,
        action="USER_PASSWORD_CHANGED",
        entity_type="USER",
        entity_id=current_user.id,
        actor_user_id=current_user.id,
        commit=True,
    )
    return Message(detail="Password changed successfully")


@router.get("/active")
async def list_active_users(
    q: str | None = None,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict[str, object]]:
    stmt = select(User).where(User.is_active == true())
    if q:
        q_like = f"%{q}%"
        stmt = stmt.where(or_(User.full_name.ilike(q_like), User.email.ilike(q_like)))
    users = db.execute(
        stmt.order_by(User.full_name.asc(), User.email.asc(), User.id.asc()).limit(limit)
    ).scalars().all()
    return [_active_user_payload(user) for user in users]
