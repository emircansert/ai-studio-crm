from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.identity import IdentityError, resolve_user_from_token
from app.db.session import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # The section-access middleware already resolved and validated the same
    # bearer token for section-gated paths. Reuse that result instead of
    # querying for the user a second time. merge(load=False) binds the
    # already-loaded instance to this request's session without a SELECT, so
    # downstream mutation paths (e.g. db.add(current_user)) still work.
    cached_user = getattr(request.state, "section_user", None)
    cached_token = getattr(request.state, "section_user_token", None)
    if cached_user is not None and cached_token == credentials.credentials:
        return db.merge(cached_user, load=False)

    try:
        return resolve_user_from_token(db, credentials.credentials)
    except IdentityError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        ) from exc


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user
