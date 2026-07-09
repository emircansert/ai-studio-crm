from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, UserSectionAccess

ACCESS_HIDDEN = "HIDDEN"
ACCESS_VIEW = "VIEW"
ACCESS_FULL = "FULL"
ACCESS_LEVELS = {ACCESS_HIDDEN, ACCESS_VIEW, ACCESS_FULL}
READ_METHODS = {"GET", "HEAD", "OPTIONS"}


@dataclass(frozen=True)
class SectionDefinition:
    key: str
    label: str
    api_prefixes: tuple[str, ...]
    admin_only: bool = False


SECTION_DEFINITIONS: tuple[SectionDefinition, ...] = (
    SectionDefinition("STARTUP_LIBRARY", "Startup Library", ("/api/v1/organizations", "/api/v1/contacts", "/api/v1/notes")),
    SectionDefinition("USE_CASES", "Use Cases", ("/api/v1/use-cases",)),
    SectionDefinition("POC_PIPELINE", "PoC Pipeline", ("/api/v1/opportunities",)),
    SectionDefinition("EVENTS_LIBRARY", "Events Library", ("/api/v1/events", "/api/v1/program-activities")),
    SectionDefinition("AI_TOOLS_LIBRARY", "AI Tools Library", ("/api/v1/ai-tools",)),
    SectionDefinition("NETWORK_LIBRARY", "Network Library", ("/api/v1/network",)),
    SectionDefinition("VENDOR_LIBRARY", "Vendor Library", ("/api/v1/vendors",)),
    SectionDefinition("FOLLOW_UPS", "Follow-ups", ("/api/v1/follow-ups",)),
    SectionDefinition("LEADERBOARD", "Leaderboard", ("/api/v1/leaderboard",)),
    SectionDefinition("CHAMPION_PROGRAM", "Champion Program", ("/api/v1/admin/champion-activities",), admin_only=True),
    SectionDefinition("ADMIN_OVERVIEW", "Admin Overview", (), admin_only=True),
    SectionDefinition("LEADERBOARD_ADMIN", "Leaderboard Admin", ("/api/v1/admin/leaderboard",), admin_only=True),
)

SECTION_BY_KEY = {section.key: section for section in SECTION_DEFINITIONS}
SORTED_API_PREFIXES = sorted(
    ((prefix, section) for section in SECTION_DEFINITIONS for prefix in section.api_prefixes),
    key=lambda item: len(item[0]),
    reverse=True,
)


def normalize_access_level(value: str | None) -> str:
    normalized = (value or ACCESS_HIDDEN).upper()
    if normalized not in ACCESS_LEVELS:
        raise ValueError(f"Invalid section access level: {value}")
    return normalized


def section_definitions_payload() -> list[dict[str, object]]:
    return [
        {"key": section.key, "label": section.label, "admin_only": section.admin_only}
        for section in SECTION_DEFINITIONS
    ]


def default_access_for_user(user: User) -> str:
    return ACCESS_FULL if user.role == "ADMIN" else ACCESS_HIDDEN


def required_access_for_method(method: str) -> str:
    return ACCESS_VIEW if method.upper() in READ_METHODS else ACCESS_FULL


def access_allows(actual_level: str, required_level: str) -> bool:
    actual = normalize_access_level(actual_level)
    required = normalize_access_level(required_level)
    if required == ACCESS_HIDDEN:
        return True
    if required == ACCESS_VIEW:
        return actual in {ACCESS_VIEW, ACCESS_FULL}
    return actual == ACCESS_FULL


def match_section_for_path(path: str) -> SectionDefinition | None:
    for prefix, section in SORTED_API_PREFIXES:
        if path == prefix or path.startswith(f"{prefix}/"):
            return section
    return None


def user_upn(user: User) -> str:
    """The permission key for a user: their UPN (email under local auth)."""
    return (user.email or "").strip().lower()


def resolve_user_section_access(db: Session, user: User, section_key: str) -> str:
    if section_key not in SECTION_BY_KEY:
        return ACCESS_HIDDEN
    access = db.execute(
        select(UserSectionAccess.access_level).where(
            UserSectionAccess.user_upn == user_upn(user),
            UserSectionAccess.section_key == section_key,
        )
    ).scalar_one_or_none()
    return normalize_access_level(access) if access else default_access_for_user(user)


def get_user_section_access_map(db: Session, user: User) -> dict[str, str]:
    rows = db.execute(
        select(UserSectionAccess.section_key, UserSectionAccess.access_level).where(
            UserSectionAccess.user_upn == user_upn(user)
        )
    ).all()
    explicit = {section_key: normalize_access_level(access_level) for section_key, access_level in rows}
    fallback = default_access_for_user(user)
    return {section.key: explicit.get(section.key, fallback) for section in SECTION_DEFINITIONS}


def validate_section_access_map(access: dict[str, str]) -> dict[str, str]:
    unknown = sorted(set(access) - set(SECTION_BY_KEY))
    if unknown:
        raise ValueError(f"Unknown section keys: {', '.join(unknown)}")
    return {section_key: normalize_access_level(level) for section_key, level in access.items()}


def default_access_rows_for_user(user: User, *, granted_by_user_id: object | None = None) -> Iterable[UserSectionAccess]:
    level = default_access_for_user(user)
    return (
        UserSectionAccess(
            user_upn=user_upn(user),
            section_key=section.key,
            access_level=level,
            granted_by_user_id=granted_by_user_id,
        )
        for section in SECTION_DEFINITIONS
    )
