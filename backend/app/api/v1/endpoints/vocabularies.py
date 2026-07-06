from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Organization, Tag, User

router = APIRouter(prefix="/vocabularies", tags=["vocabularies"])


@router.get("/categories")
async def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    categories: dict[str, dict[str, Any]] = {}

    tag_rows = db.execute(
        select(Tag).where(Tag.tag_group == "CATEGORY").order_by(Tag.label.asc(), Tag.code.asc())
    ).scalars()
    for tag in tag_rows:
        categories[tag.code] = {"code": tag.code, "label": tag.label, "source": "TAG"}

    org_rows = db.execute(
        select(Organization.category_code, Organization.category_label)
        .where(Organization.category_label.is_not(None))
        .order_by(Organization.category_label.asc())
    ).all()
    for code, label in org_rows:
        key = code or label
        if key and key not in categories:
            categories[key] = {"code": code, "label": label, "source": "ORGANIZATION"}

    return sorted(categories.values(), key=lambda item: (item.get("label") or item.get("code") or "").lower())
