from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import false, func, or_, select, true
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import settings
from app.core.identity import SSO_PASSWORD_PLACEHOLDER
from app.core.security import hash_password
from app.core.section_access import (
    default_access_rows_for_user,
    get_user_section_access_map,
    section_definitions_payload,
    validate_section_access_map,
)
from app.db.session import get_db
from app.models import User, UserSectionAccess
from app.schemas import (
    AdminUserCreate,
    AdminUserPasswordReset,
    AdminUserRoleUpdate,
    UserAccessMatrixResponse,
    UserRead,
    UserSectionAccessBulkUpdate,
    UserSectionAccessResponse,
    UserUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _ensure_role(role: str) -> str:
    normalized = role.upper()
    if normalized not in {"ADMIN", "USER"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be ADMIN or USER")
    return normalized


def _active_admin_count(db: Session) -> int:
    return int(
        db.execute(select(func.count()).select_from(User).where(User.role == "ADMIN", User.is_active == true())).scalar_one()
    )


def _prevent_last_admin_loss(db: Session, user: User, *, next_role: str | None = None, next_active: bool | None = None) -> None:
    loses_admin = user.role == "ADMIN" and (next_role == "USER" or next_active is False)
    if loses_admin and _active_admin_count(db) <= 1 and user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the only active admin")


def _user_list_statement(q: str | None, role: str | None, is_active: bool | None):
    stmt = select(User)
    if q:
        q_like = f"%{q}%"
        stmt = stmt.where(or_(User.email.ilike(q_like), User.full_name.ilike(q_like)))
    if role:
        stmt = stmt.where(User.role == _ensure_role(role))
    if is_active is not None:
        stmt = stmt.where(User.is_active == (true() if is_active else false()))
    return stmt.order_by(User.full_name.asc(), User.email.asc(), User.id.asc())


@router.get("", response_model=list[UserRead])
async def list_users(
    q: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[User]:
    return list(db.execute(_user_list_statement(q, role, is_active).offset(skip).limit(limit)).scalars().all())


@router.get("/section-access", response_model=UserAccessMatrixResponse)
async def list_user_section_access(
    q: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, object]:
    users = list(db.execute(_user_list_statement(q, role, is_active).offset(skip).limit(limit)).scalars().all())
    return {
        "sections": section_definitions_payload(),
        "users": [
            {"user": UserRead.model_validate(user), "access": get_user_section_access_map(db, user)}
            for user in users
        ],
    }


@router.get("/{user_id}/section-access", response_model=UserSectionAccessResponse)
async def get_user_section_access(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict[str, object]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"user_id": user.id, "access": get_user_section_access_map(db, user)}


@router.put("/{user_id}/section-access", response_model=UserSectionAccessResponse)
async def update_user_section_access(
    user_id: UUID,
    payload: UserSectionAccessBulkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, object]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    try:
        requested_access = validate_section_access_map(payload.access)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    upn = (user.email or "").strip().lower()
    before = get_user_section_access_map(db, user)
    existing_rows = {
        row.section_key: row
        for row in db.execute(select(UserSectionAccess).where(UserSectionAccess.user_upn == upn)).scalars().all()
    }
    for section_key, access_level in requested_access.items():
        row = existing_rows.get(section_key)
        if row is None:
            row = UserSectionAccess(
                user_upn=upn,
                section_key=section_key,
                access_level=access_level,
                granted_by_user_id=current_user.id,
            )
        else:
            row.access_level = access_level
            row.granted_by_user_id = current_user.id
        db.add(row)
    db.commit()
    after = get_user_section_access_map(db, user)
    await write_audit_log(
        db,
        action="USER_SECTION_ACCESS_UPDATED",
        entity_type="USER",
        entity_id=user.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=after,
        commit=True,
    )
    return {"user_id": user.id, "access": after}


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    if db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    # Under Entra SSO no local credential is ever stored; the account is
    # pre-provisioned (e.g. to grant section access before first sign-in)
    # and authentication happens exclusively against Entra ID.
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        role=_ensure_role(payload.role),
        is_active=True,
        password_hash=SSO_PASSWORD_PLACEHOLDER if settings.is_entra_auth else hash_password(payload.temporary_password),
    )
    db.add(user)
    db.flush()
    for row in default_access_rows_for_user(user, granted_by_user_id=current_user.id):
        db.add(row)
    db.commit()
    db.refresh(user)
    await write_audit_log(
        db,
        action="ADMIN_USER_CREATED",
        entity_type="USER",
        entity_id=user.id,
        actor_user_id=current_user.id,
        after_data=UserRead.model_validate(user).model_dump(mode="json"),
        commit=True,
    )
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    before = UserRead.model_validate(user).model_dump(mode="json")
    data = payload.model_dump(exclude_unset=True, exclude={"password"})
    if "role" in data:
        data["role"] = _ensure_role(data["role"])
        _prevent_last_admin_loss(db, user, next_role=data["role"])
    if "is_active" in data:
        _prevent_last_admin_loss(db, user, next_active=data["is_active"])
    if "email" in data and data["email"]:
        data["email"] = data["email"].lower()
    for field_name, value in data.items():
        setattr(user, field_name, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    await write_audit_log(
        db,
        action="ADMIN_USER_UPDATED",
        entity_type="USER",
        entity_id=user.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=UserRead.model_validate(user).model_dump(mode="json"),
        commit=True,
    )
    return user


@router.patch("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _prevent_last_admin_loss(db, user, next_active=False)
    user.is_active = False
    db.add(user)
    db.commit()
    db.refresh(user)
    await write_audit_log(db, action="ADMIN_USER_DEACTIVATED", entity_type="USER", entity_id=user.id, actor_user_id=current_user.id, commit=True)
    return user


@router.patch("/{user_id}/activate", response_model=UserRead)
async def activate_user(user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    await write_audit_log(db, action="ADMIN_USER_ACTIVATED", entity_type="USER", entity_id=user.id, actor_user_id=current_user.id, commit=True)
    return user


@router.patch("/{user_id}/role", response_model=UserRead)
async def change_role(
    user_id: UUID,
    payload: AdminUserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    next_role = _ensure_role(payload.role)
    _prevent_last_admin_loss(db, user, next_role=next_role)
    before = {"role": user.role}
    user.role = next_role
    db.add(user)
    db.commit()
    db.refresh(user)
    await write_audit_log(
        db,
        action="ADMIN_USER_ROLE_CHANGED",
        entity_type="USER",
        entity_id=user.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data={"role": user.role},
        commit=True,
    )
    return user


@router.patch("/{user_id}/reset-password", response_model=UserRead)
async def reset_password(
    user_id: UUID,
    payload: AdminUserPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    if settings.is_entra_auth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords are managed by Microsoft Entra ID. Local password resets are disabled.",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = hash_password(payload.temporary_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    await write_audit_log(
        db,
        action="ADMIN_USER_PASSWORD_RESET",
        entity_type="USER",
        entity_id=user.id,
        actor_user_id=current_user.id,
        commit=True,
    )
    return user
