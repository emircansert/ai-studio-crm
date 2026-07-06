from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.services.soft_delete import not_archived

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


def normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def extract_domain(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    hostname = parsed.hostname
    if not hostname:
        return None
    hostname = hostname.lower()
    return hostname[4:] if hostname.startswith("www.") else hostname


class CRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, db: Session, object_id: UUID) -> ModelType | None:
        return db.get(self.model, object_id)

    async def list(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        order_by: Any | Sequence[Any] | None = None,
        include_archived: bool = False,
    ) -> Sequence[ModelType]:
        stmt: Select[Any] = select(self.model)
        if hasattr(self.model, "is_archived") and not include_archived:
            stmt = stmt.where(not_archived(getattr(self.model, "is_archived")))
        if filters:
            for field_name, value in filters.items():
                if value is None:
                    continue
                stmt = stmt.where(getattr(self.model, field_name) == value)
        ordering = order_by if order_by is not None else self._default_order_by()
        if isinstance(ordering, Sequence) and not isinstance(ordering, str):
            stmt = stmt.order_by(*ordering)
        else:
            stmt = stmt.order_by(ordering)
        stmt = stmt.offset(skip).limit(limit)
        result = db.execute(stmt)
        return result.scalars().all()

    def _default_order_by(self) -> Any:
        if hasattr(self.model, "created_at"):
            return getattr(self.model, "created_at").desc()
        return getattr(self.model, "id")

    async def count(self, db: Session) -> int:
        result = db.execute(select(func.count()).select_from(self.model))
        return int(result.scalar_one())

    async def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        data = obj_in.model_dump(exclude_unset=True)
        if self.model.__name__ == "Organization" and data.get("normalized_name") is None:
            data["normalized_name"] = normalize_name(data["name"])
        if self.model.__name__ == "Organization" and data.get("website_url") and not data.get("website_domain"):
            data["website_domain"] = extract_domain(data["website_url"])
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: Session,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
    ) -> ModelType:
        data = obj_in.model_dump(exclude_unset=True)
        if self.model.__name__ == "Organization" and data.get("name") and not data.get("normalized_name"):
            data["normalized_name"] = normalize_name(data["name"])
        if self.model.__name__ == "Organization" and "website_url" in data and not data.get("website_domain"):
            data["website_domain"] = extract_domain(data.get("website_url"))
        for field_name, value in data.items():
            setattr(db_obj, field_name, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
