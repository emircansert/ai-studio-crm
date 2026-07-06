from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Status, User
from app.schemas import StatusCreate, StatusRead, StatusUpdate
from app.services.crud import CRUDService

router = APIRouter(prefix="/statuses", tags=["statuses"])
service = CRUDService[Status, StatusCreate, StatusUpdate](Status)


@router.get("", response_model=list[StatusRead])
async def list_statuses(
    status_group: str | None = None,
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Status]:
    return list(
        await service.list(
            db,
            skip=skip,
            limit=limit,
            filters={"status_group": status_group},
            order_by=[Status.status_group.asc(), Status.sort_order.asc(), Status.code.asc(), Status.id.asc()],
        )
    )


@router.get("/{status_id}", response_model=StatusRead)
async def get_status(status_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Status:
    status_obj = await service.get(db, status_id)
    if status_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status not found")
    return status_obj


@router.post("", response_model=StatusRead, status_code=status.HTTP_201_CREATED)
async def create_status(payload: StatusCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Status:
    return await service.create(db, payload)


@router.patch("/{status_id}", response_model=StatusRead)
async def update_status(status_id: UUID, payload: StatusUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Status:
    status_obj = await service.get(db, status_id)
    if status_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status not found")
    return await service.update(db, status_obj, payload)
