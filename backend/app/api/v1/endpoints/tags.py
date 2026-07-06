from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Tag, User
from app.schemas import TagCreate, TagRead, TagUpdate
from app.services.crud import CRUDService

router = APIRouter(prefix="/tags", tags=["tags"])
service = CRUDService[Tag, TagCreate, TagUpdate](Tag)


@router.get("", response_model=list[TagRead])
async def list_tags(
    tag_group: str | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Tag]:
    return list(
        await service.list(
            db,
            skip=skip,
            limit=limit,
            filters={"tag_group": tag_group},
            order_by=[Tag.tag_group.asc(), Tag.label.asc(), Tag.id.asc()],
        )
    )


@router.get("/{tag_id}", response_model=TagRead)
async def get_tag(tag_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Tag:
    tag = await service.get(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Tag:
    return await service.create(db, payload)


@router.patch("/{tag_id}", response_model=TagRead)
async def update_tag(tag_id: UUID, payload: TagUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Tag:
    tag = await service.get(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return await service.update(db, tag, payload)
