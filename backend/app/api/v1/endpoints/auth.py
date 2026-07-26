from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models import User
from app.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/config")
async def auth_config() -> dict[str, Any]:
    """Public, non-sensitive auth configuration for the login page.

    Authentication is Microsoft Entra ID only: the application stores no
    passwords and exposes no local sign-in endpoint.
    """
    return {"auth_mode": "entra"}


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
