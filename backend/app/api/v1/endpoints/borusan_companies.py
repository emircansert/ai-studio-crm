from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import BorusanCompany, User
from app.schemas import BorusanCompanyCreate, BorusanCompanyRead, BorusanCompanyUpdate
from app.services.crud import CRUDService

router = APIRouter(prefix="/borusan-companies", tags=["borusan-companies"])
service = CRUDService[BorusanCompany, BorusanCompanyCreate, BorusanCompanyUpdate](BorusanCompany)


@router.get("", response_model=list[BorusanCompanyRead])
async def list_borusan_companies(
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[BorusanCompany]:
    return list(
        await service.list(
            db,
            skip=skip,
            limit=limit,
            filters={"is_active": is_active},
            order_by=[BorusanCompany.code.asc(), BorusanCompany.id.asc()],
        )
    )


@router.get("/{company_id}", response_model=BorusanCompanyRead)
async def get_borusan_company(company_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> BorusanCompany:
    company = await service.get(db, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borusan company not found")
    return company


@router.post("", response_model=BorusanCompanyRead, status_code=status.HTTP_201_CREATED)
async def create_borusan_company(payload: BorusanCompanyCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> BorusanCompany:
    return await service.create(db, payload)


@router.patch("/{company_id}", response_model=BorusanCompanyRead)
async def update_borusan_company(company_id: UUID, payload: BorusanCompanyUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> BorusanCompany:
    company = await service.get(db, company_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borusan company not found")
    return await service.update(db, company, payload)
