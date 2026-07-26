"""Single source of truth for resolving the authenticated user from a bearer token.

Both the FastAPI dependency (app.api.deps.get_current_user) and the section-access
middleware (app.main) MUST use this function so that authentication and the Phase 4
permission system can never disagree about who is calling.

Authentication is exclusively Microsoft Entra ID. The frontend signs in with MSAL
and sends the resulting OIDC ID token as the Bearer credential; this module
validates it and maps it to a CRM user. The application stores no passwords and
has no local credential path.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.entra import EntraAuthError, entra_validator, extract_display_name, extract_upn
from app.models import User

LAST_LOGIN_REFRESH = timedelta(minutes=15)


class IdentityError(Exception):
    def __init__(self, message: str, *, error_code: str = "INVALID_TOKEN") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


def _resolve_entra(db: Session, token: str) -> User:
    try:
        claims = entra_validator.validate(token)
        upn = extract_upn(claims)
    except EntraAuthError as exc:
        raise IdentityError(str(exc)) from exc

    user = db.execute(select(User).where(User.email == upn)).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if user is None:
        # Just-in-time provisioning on first Entra sign-in. Role is USER unless
        # the UPN is in the bootstrap admin list; section access starts at the
        # non-admin default (everything hidden) until an admin grants it.
        user = User(
            email=upn,
            full_name=extract_display_name(claims, upn),
            role="ADMIN" if upn in settings.entra_admin_upns else "USER",
            is_active=True,
            last_login_at=now,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    if not user.is_active:
        raise IdentityError(
            "This account is deactivated in the CRM. Contact an administrator.",
            error_code="INACTIVE_OR_MISSING_USER",
        )

    # Promote bootstrap admins even if the row pre-existed the cutover.
    changed = False
    if upn in settings.entra_admin_upns and user.role != "ADMIN":
        user.role = "ADMIN"
        changed = True
    last_login = user.last_login_at
    if last_login is not None and last_login.tzinfo is None:
        last_login = last_login.replace(tzinfo=timezone.utc)
    if last_login is None or (now - last_login) > LAST_LOGIN_REFRESH:
        user.last_login_at = now
        changed = True
    if changed:
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def resolve_user_from_token(db: Session, token: str) -> User:
    """Validate the Entra ID token and return the active User, or raise IdentityError."""
    return _resolve_entra(db, token)
