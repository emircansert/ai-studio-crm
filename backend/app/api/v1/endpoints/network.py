from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Organization, User
from app.schemas import OrganizationCreate, OrganizationRead, OrganizationUpdate
from app.services.crud import CRUDService

router = APIRouter(prefix="/network", tags=["network"])
service = CRUDService[Organization, OrganizationCreate, OrganizationUpdate](Organization)


@router.get("", response_model=list[OrganizationRead])
async def list_network_institutions(
    organization_subtype: str | None = None,
    geography_text: str | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Organization]:
    return list(
        await service.list(
            db,
            skip=skip,
            limit=limit,
            filters={
                "organization_type": "NETWORK_INSTITUTION",
                "organization_subtype": organization_subtype,
                "geography_text": geography_text,
            },
            order_by=[Organization.name.asc(), Organization.id.asc()],
            include_archived=include_archived and current_user.role == "ADMIN",
        )
    )


@router.get("/{organization_id}", response_model=OrganizationRead)
async def get_network_institution(
    organization_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Organization:
    organization = await service.get(db, organization_id)
    if organization is None or organization.organization_type != "NETWORK_INSTITUTION":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network institution not found")
    return organization


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_network_institution(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Organization:
    payload = payload.model_copy(update={"organization_type": "NETWORK_INSTITUTION"})
    return await service.create(db, payload)


@router.patch("/{organization_id}", response_model=OrganizationRead)
async def update_network_institution(
    organization_id: UUID,
    payload: OrganizationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Organization:
    organization = await service.get(db, organization_id)
    if organization is None or organization.organization_type != "NETWORK_INSTITUTION":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Network institution not found")
    payload = payload.model_copy(update={"organization_type": "NETWORK_INSTITUTION"})
    return await service.update(db, organization, payload)
