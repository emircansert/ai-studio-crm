from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import Contact, User
from app.schemas import ArchiveRequest, ContactCreate, ContactRead, ContactUpdate
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.champion_score import write_champion_activity
from app.services.contributions import write_user_contribution
from app.services.crud import CRUDService

router = APIRouter(prefix="/contacts", tags=["contacts"])
service = CRUDService[Contact, ContactCreate, ContactUpdate](Contact)


@router.get("", response_model=list[ContactRead])
async def list_contacts(
    organization_id: UUID | None = None,
    email: str | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Contact]:
    return list(
        await service.list(
            db,
            skip=skip,
            limit=limit,
            filters={"organization_id": organization_id, "email": email},
            order_by=[Contact.full_name.asc(), Contact.email.asc(), Contact.id.asc()],
            include_archived=include_archived and current_user.role == "ADMIN",
        )
    )


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(contact_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Contact:
    contact = await service.get(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Contact:
    data = payload.model_dump(exclude_unset=True)
    data["created_by_user_id"] = current_user.id
    data["updated_by_user_id"] = current_user.id
    contact = Contact(**data)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    await write_audit_log(
        db,
        action="CONTACT_CREATED",
        entity_type="CONTACT",
        entity_id=contact.id,
        actor_user_id=current_user.id,
        after_data=ContactRead.model_validate(contact).model_dump(mode="json"),
        commit=True,
    )
    await write_user_contribution(
        db,
        user_id=current_user.id,
        contribution_type="CONTACT_CREATED",
        entity_type="CONTACT",
        entity_id=contact.id,
        metadata_json={"organization_id": str(contact.organization_id)},
        commit=True,
    )
    await write_champion_activity(
        db,
        user_id=current_user.id,
        category="ECOSYSTEM_LIBRARY",
        activity_type="CONTACT_ADDED",
        related_entity_type="CONTACT",
        related_entity_id=contact.id,
        notes=contact.full_name or contact.email,
        created_by_user_id=current_user.id,
        commit=True,
    )
    return contact


async def _update_contact(contact_id: UUID, payload: ContactUpdate, db: Session, current_user: User) -> Contact:
    contact = await service.get(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    before = ContactRead.model_validate(contact).model_dump(mode="json")
    data = payload.model_dump(exclude_unset=True)
    data["updated_by_user_id"] = current_user.id
    for field_name, value in data.items():
        setattr(contact, field_name, value)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    await write_audit_log(
        db,
        action="CONTACT_UPDATED",
        entity_type="CONTACT",
        entity_id=contact.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=ContactRead.model_validate(contact).model_dump(mode="json"),
        commit=True,
    )
    return contact


@router.patch("/{contact_id}", response_model=ContactRead)
async def patch_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Contact:
    return await _update_contact(contact_id, payload, db, current_user)


@router.put("/{contact_id}", response_model=ContactRead)
async def put_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Contact:
    return await _update_contact(contact_id, payload, db, current_user)


@router.patch("/{contact_id}/archive", response_model=ContactRead)
async def archive_contact(
    contact_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Contact:
    return await archive_record(
        db,
        await service.get(db, contact_id),
        entity_type="CONTACT",
        entity_id=contact_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.patch("/{contact_id}/unarchive", response_model=ContactRead)
async def unarchive_contact(
    contact_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Contact:
    return await unarchive_record(
        db,
        await service.get(db, contact_id),
        entity_type="CONTACT",
        entity_id=contact_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    contact = await service.get(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    await archive_record(
        db,
        contact,
        entity_type="CONTACT",
        entity_id=contact_id,
        actor=current_user,
        reason="Archived via legacy DELETE endpoint",
    )
