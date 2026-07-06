import re
import unicodedata
import csv
import hashlib
from io import StringIO
from pathlib import Path
from datetime import date, datetime, time, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import (
    BorusanCompany,
    Contact,
    Note,
    Opportunity,
    Organization,
    OrganizationBorusanFit,
    OrganizationDocument,
    OrganizationStatusHistory,
    OrganizationTag,
    FollowUpAction,
    Status,
    Tag,
    User,
)
from app.schemas import (
    ArchiveRequest,
    ContactCreate,
    ContactRead,
    ContactUpdate,
    NoteRead,
    NoteUpdate,
    OrganizationBorusanFitCreate,
    OrganizationBorusanFitRead,
    OrganizationBorusanFitUpdate,
    OrganizationCreate,
    OrganizationDocumentRead,
    OrganizationRead,
    OrganizationUpdate,
)
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.champion_score import write_champion_activity
from app.services.contributions import write_user_contribution
from app.services.crud import CRUDService, extract_domain, normalize_name
from app.services.soft_delete import not_archived

router = APIRouter(prefix="/organizations", tags=["organizations"])
service = CRUDService[Organization, OrganizationCreate, OrganizationUpdate](Organization)

ALLOWED_DECK_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
ALLOWED_DECK_SUFFIXES = {".pdf", ".pptx"}
MAX_DECK_SIZE_BYTES = 50 * 1024 * 1024
DOCUMENT_UPLOAD_DIR = Path(__file__).resolve().parents[5] / "uploads" / "organization_documents"


def _status_payload(status_obj: Status | None) -> dict[str, Any] | None:
    if status_obj is None:
        return None
    return {"id": status_obj.id, "code": status_obj.code, "label": status_obj.label, "status_group": status_obj.status_group}


def _organization_base(db: Session, org: Organization) -> dict[str, Any]:
    created_by_user = _user_payload(db, org.created_by_user_id)
    updated_by_user = _user_payload(db, org.updated_by_user_id)
    return {
        "id": org.id,
        "name": org.name,
        "normalized_name": org.normalized_name,
        "organization_type": org.organization_type,
        "organization_subtype": org.organization_subtype,
        "category_code": org.category_code,
        "category_label": org.category_label,
        "category": {"code": org.category_code, "label": org.category_label} if org.category_code or org.category_label else None,
        "vertical_text": org.vertical_text,
        "website_url": org.website_url,
        "website_domain": org.website_domain,
        "geography_text": org.geography_text,
        "source_text": org.source_text,
        "added_by_text": org.added_by_text,
        "solution_summary": org.solution_summary,
        "lifecycle_status": _status_payload(org.lifecycle_status),
        "relationship_status": _status_payload(org.relationship_status),
        "lifecycle_status_id": org.lifecycle_status_id,
        "relationship_status_id": org.relationship_status_id,
        "last_contact_date": org.last_contact_date,
        "raw_import_ref": org.raw_import_ref,
        "created_by_user_id": org.created_by_user_id,
        "updated_by_user_id": org.updated_by_user_id,
        "created_by_user": created_by_user,
        "updated_by_user": updated_by_user,
        "added_by_display": created_by_user["full_name"] if created_by_user else org.added_by_text,
        "added_at": org.created_at,
        "is_archived": org.is_archived,
        "archived_at": org.archived_at,
        "archived_by_user_id": org.archived_by_user_id,
        "archive_reason": org.archive_reason,
        "created_at": org.created_at,
        "updated_at": org.updated_at,
    }


def _user_payload(db: Session, user_id: UUID | None) -> dict[str, Any] | None:
    if not user_id:
        return None
    user = db.get(User, user_id)
    if user is None:
        return {"id": user_id, "full_name": None, "email": None}
    return {"id": user.id, "full_name": user.full_name, "email": user.email}


def _count_notes(db: Session, org_id: UUID) -> int:
    return int(
        db.execute(
            select(func.count()).select_from(Note).where(Note.entity_type == "ORGANIZATION", Note.entity_id == org_id, not_archived(Note.is_archived))
        ).scalar_one()
    )


def _safe_count(db: Session, stmt: Any) -> int:
    try:
        return int(db.execute(stmt).scalar_one())
    except SQLAlchemyError:
        db.rollback()
        return 0


def _fits(db: Session, org_id: UUID) -> list[dict[str, Any]]:
    result = db.execute(
        select(OrganizationBorusanFit, BorusanCompany)
        .join(BorusanCompany, BorusanCompany.id == OrganizationBorusanFit.borusan_company_id)
        .where(OrganizationBorusanFit.organization_id == org_id, not_archived(OrganizationBorusanFit.is_archived))
        .order_by(BorusanCompany.code.asc())
    )
    return [
        {
            "id": fit.id,
            "borusan_company_id": company.id,
            "borusan_company_code": company.code,
            "borusan_company_name": company.english_name or company.name,
            "fit_level": fit.fit_level,
            "fit_reason": fit.fit_reason,
            "source": fit.source,
            "raw_value": fit.raw_value,
            "is_archived": fit.is_archived,
        }
        for fit, company in result.all()
    ]


def _tags(db: Session, org_id: UUID) -> list[dict[str, Any]]:
    result = db.execute(
        select(Tag, OrganizationTag)
        .join(OrganizationTag, OrganizationTag.tag_id == Tag.id)
        .where(OrganizationTag.organization_id == org_id)
        .order_by(Tag.tag_group.asc(), Tag.label.asc())
    )
    return [
        {"id": tag.id, "code": tag.code, "label": tag.label, "tag_group": tag.tag_group, "source": org_tag.source}
        for tag, org_tag in result.all()
    ]


def _summary(db: Session, org: Organization) -> dict[str, Any]:
    contact_count = int(
        db.execute(select(func.count()).select_from(Contact).where(Contact.organization_id == org.id, not_archived(Contact.is_archived))).scalar_one()
    )
    opportunity_count = int(
        db.execute(select(func.count()).select_from(Opportunity).where(Opportunity.organization_id == org.id, not_archived(Opportunity.is_archived))).scalar_one()
    )
    fits = _fits(db, org.id)
    tags = _tags(db, org.id)
    document_count = _safe_count(
        db,
        select(func.count()).select_from(OrganizationDocument).where(
            OrganizationDocument.organization_id == org.id,
            not_archived(OrganizationDocument.is_archived),
        ),
    )
    open_follow_up_count = _safe_count(
        db,
        select(func.count()).select_from(FollowUpAction).where(
            FollowUpAction.entity_type == "ORGANIZATION",
            FollowUpAction.entity_id == org.id,
            FollowUpAction.status == "OPEN",
            not_archived(FollowUpAction.is_archived),
        ),
    )
    primary_contact = db.execute(
        select(Contact)
        .where(Contact.organization_id == org.id, not_archived(Contact.is_archived))
        .order_by(Contact.full_name.asc(), Contact.email.asc(), Contact.id.asc())
    ).scalars().first()
    latest_note = db.execute(
        select(Note)
        .where(Note.entity_type == "ORGANIZATION", Note.entity_id == org.id, not_archived(Note.is_archived))
        .order_by(Note.occurred_at.desc(), Note.created_at.desc(), Note.id.desc())
    ).scalars().first()
    expertise_text = org.solution_summary or org.vertical_text or ", ".join(tag["label"] for tag in tags[:4])
    return {
        **_organization_base(db, org),
        "borusan_fit_summary": fits,
        "tags_summary": tags,
        "expertise_text": expertise_text,
        "primary_contact": ContactRead.model_validate(primary_contact).model_dump(mode="json") if primary_contact else None,
        "notes_preview": latest_note.body if latest_note else None,
        "contact_count": contact_count,
        "note_count": _count_notes(db, org.id),
        "opportunity_count": opportunity_count,
        "deck_count": document_count,
        "open_follow_up_count": open_follow_up_count,
    }


def _detail(db: Session, org: Organization) -> dict[str, Any]:
    contacts = db.execute(
        select(Contact).where(Contact.organization_id == org.id, not_archived(Contact.is_archived)).order_by(Contact.full_name.asc(), Contact.email.asc())
    ).scalars().all()
    notes = db.execute(
        select(Note)
        .where(Note.entity_type == "ORGANIZATION", Note.entity_id == org.id, not_archived(Note.is_archived))
        .order_by(Note.occurred_at.desc(), Note.created_at.desc())
    ).scalars().all()
    opportunities = db.execute(
        select(Opportunity).where(Opportunity.organization_id == org.id, not_archived(Opportunity.is_archived)).order_by(Opportunity.created_at.desc())
    ).scalars().all()
    return {
        **_summary(db, org),
        "contacts": [ContactRead.model_validate(contact).model_dump(mode="json") for contact in contacts],
        "notes": [NoteRead.model_validate(note).model_dump(mode="json") for note in notes],
        "opportunities": [
            {
                "id": opportunity.id,
                "title": opportunity.title,
                "stage": opportunity.stage,
                "topic": opportunity.topic,
                "borusan_company_id": opportunity.borusan_company_id,
                "status_id": opportunity.status_id,
                "last_contact_date": opportunity.last_contact_date,
                "created_at": opportunity.created_at,
                "updated_at": opportunity.updated_at,
            }
            for opportunity in opportunities
        ],
        "tags": _tags(db, org.id),
        "raw_source_reference": {"import_row_id": org.raw_import_ref} if org.raw_import_ref else None,
    }


def _reject_vendor_type(organization_type: str | None) -> None:
    # Vendors moved to the dedicated Vendor Library (/api/v1/vendors) and must not
    # be created as organizations anymore.
    if (organization_type or "").upper() == "VENDOR":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendors are managed in the Vendor Library. Use /api/v1/vendors instead.",
        )


def _prepare_create(payload: OrganizationCreate, user_id: UUID) -> OrganizationCreate:
    data = payload.model_dump(exclude_unset=True)
    _reject_vendor_type(data.get("organization_type"))
    data["normalized_name"] = data.get("normalized_name") or normalize_name(data["name"])
    data["website_domain"] = data.get("website_domain") or extract_domain(data.get("website_url"))
    if data.get("category_label") and not data.get("category_code"):
        data["category_code"] = _category_code(data["category_label"])
    data["created_by_user_id"] = user_id
    data["updated_by_user_id"] = user_id
    return OrganizationCreate.model_validate(data)


def _prepare_update(payload: OrganizationUpdate, user_id: UUID, db: Session) -> OrganizationUpdate:
    data = payload.model_dump(exclude_unset=True)
    if "organization_type" in data:
        _reject_vendor_type(data.get("organization_type"))
    status_code = data.pop("status_code", None)
    if status_code:
        status_obj = db.execute(
            select(Status).where(Status.status_group == "COMPANY_STATUS", Status.code == status_code)
        ).scalar_one_or_none()
        if status_obj is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown company status code: {status_code}")
        data["lifecycle_status_id"] = status_obj.id
    if "name" in data and not data.get("normalized_name"):
        data["normalized_name"] = normalize_name(data["name"])
    if "website_url" in data and not data.get("website_domain"):
        data["website_domain"] = extract_domain(data.get("website_url"))
    if data.get("category_label") and not data.get("category_code"):
        data["category_code"] = _category_code(data["category_label"])
    data["updated_by_user_id"] = user_id
    return OrganizationUpdate.model_validate(data)


def _category_code(label: str) -> str:
    normalized = unicodedata.normalize("NFKD", label)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", ascii_value.upper()).strip("_")
    return f"CATEGORY_{slug or 'UNCATEGORIZED'}"[:120]


def _ordered(stmt: Any, sort_by: str) -> Any:
    if sort_by == "oldest":
        return stmt.order_by(Organization.created_at.asc(), Organization.id.asc())
    if sort_by == "name_asc":
        return stmt.order_by(Organization.name.asc(), Organization.id.asc())
    if sort_by == "last_contact_desc":
        # SQL Server sorts NULLs first in ASC and last in DESC, so DESC already
        # keeps records without a contact date at the bottom.
        return stmt.order_by(Organization.last_contact_date.desc(), Organization.created_at.desc(), Organization.id.desc())
    if sort_by == "last_contact_asc":
        # SQL Server has no NULLS LAST; use a CASE so records without a contact
        # date stay at the bottom instead of flooding the first page.
        return stmt.order_by(
            case((Organization.last_contact_date.is_(None), 1), else_=0).asc(),
            Organization.last_contact_date.asc(),
            Organization.created_at.asc(),
            Organization.id.asc(),
        )
    return stmt.order_by(Organization.created_at.desc(), Organization.id.desc())


@router.get("")
async def list_organizations(
    q: str | None = None,
    organization_type: str | None = None,
    organization_subtype: str | None = None,
    category: str | None = None,
    vertical: str | None = None,
    expertise: str | None = None,
    contact_person: str | None = None,
    notes: str | None = None,
    borusan_company_code: str | None = None,
    status_code: str | None = None,
    relationship_status_code: str | None = None,
    geography: str | None = None,
    source: str | None = None,
    added_by: str | None = None,
    created_by_user_id: UUID | None = None,
    added_from_date: date | None = None,
    added_to_date: date | None = None,
    created_from: date | None = None,
    created_to: date | None = None,
    last_contact_from: date | None = None,
    last_contact_to: date | None = None,
    tag: str | None = None,
    has_website: bool | None = None,
    include_archived: bool = False,
    sort_by: str = Query(default="newest", pattern="^(newest|oldest|name_asc|last_contact_desc|last_contact_asc)$"),
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    stmt = select(Organization)
    if not include_archived or current_user.role != "ADMIN":
        stmt = stmt.where(not_archived(Organization.is_archived))
    if organization_type:
        stmt = stmt.where(Organization.organization_type == organization_type)
    if organization_subtype:
        stmt = stmt.where(Organization.organization_subtype == organization_subtype)
    if category:
        category_like = f"%{category}%"
        stmt = stmt.where(or_(Organization.category_code.ilike(category_like), Organization.category_label.ilike(category_like)))
    if vertical:
        stmt = stmt.where(Organization.vertical_text.ilike(f"%{vertical}%"))
    if expertise:
        expertise_like = f"%{expertise}%"
        expertise_tag_org_ids = (
            select(OrganizationTag.organization_id)
            .join(Tag, Tag.id == OrganizationTag.tag_id)
            .where(or_(Tag.code.ilike(expertise_like), Tag.label.ilike(expertise_like), Tag.tag_group.ilike(expertise_like)))
        )
        stmt = stmt.where(
            or_(
                Organization.solution_summary.ilike(expertise_like),
                Organization.vertical_text.ilike(expertise_like),
                Organization.id.in_(expertise_tag_org_ids),
            )
        )
    if contact_person:
        contact_like = f"%{contact_person}%"
        contact_org_ids = select(Contact.organization_id).where(
            not_archived(Contact.is_archived),
            or_(
                Contact.full_name.ilike(contact_like),
                Contact.email.ilike(contact_like),
                Contact.title.ilike(contact_like),
                Contact.raw_contact_text.ilike(contact_like),
            ),
        )
        stmt = stmt.where(Organization.id.in_(contact_org_ids))
    if notes:
        notes_like = f"%{notes}%"
        notes_org_ids = select(Note.entity_id).where(
            Note.entity_type == "ORGANIZATION",
            not_archived(Note.is_archived),
            Note.body.ilike(notes_like),
        )
        stmt = stmt.where(Organization.id.in_(notes_org_ids))
    if geography:
        stmt = stmt.where(Organization.geography_text.ilike(f"%{geography}%"))
    if source:
        stmt = stmt.where(Organization.source_text.ilike(f"%{source}%"))
    if added_by:
        stmt = stmt.where(Organization.added_by_text.ilike(f"%{added_by}%"))
    if created_by_user_id:
        stmt = stmt.where(Organization.created_by_user_id == created_by_user_id)
    added_from = added_from_date or created_from
    added_to = added_to_date or created_to
    if added_from:
        stmt = stmt.where(Organization.created_at >= datetime.combine(added_from, time.min))
    if added_to:
        stmt = stmt.where(Organization.created_at <= datetime.combine(added_to, time.max))
    if last_contact_from:
        stmt = stmt.where(Organization.last_contact_date >= last_contact_from)
    if last_contact_to:
        stmt = stmt.where(Organization.last_contact_date <= last_contact_to)
    if has_website is True:
        stmt = stmt.where(Organization.website_domain.is_not(None))
    if has_website is False:
        stmt = stmt.where(Organization.website_domain.is_(None))
    if status_code:
        status_ids = select(Status.id).where(Status.status_group == "COMPANY_STATUS", Status.code == status_code)
        stmt = stmt.where(Organization.lifecycle_status_id.in_(status_ids))
    if relationship_status_code:
        relationship_status_ids = select(Status.id).where(
            Status.status_group == "NETWORK_RELATIONSHIP",
            Status.code == relationship_status_code,
        )
        stmt = stmt.where(Organization.relationship_status_id.in_(relationship_status_ids))
    if borusan_company_code:
        fit_org_ids = (
            select(OrganizationBorusanFit.organization_id)
            .join(BorusanCompany, BorusanCompany.id == OrganizationBorusanFit.borusan_company_id)
            .where(BorusanCompany.code == borusan_company_code, not_archived(OrganizationBorusanFit.is_archived))
        )
        stmt = stmt.where(Organization.id.in_(fit_org_ids))
    if tag:
        tag_org_ids = (
            select(OrganizationTag.organization_id)
            .join(Tag, Tag.id == OrganizationTag.tag_id)
            .where(or_(Tag.code.ilike(f"%{tag}%"), Tag.label.ilike(f"%{tag}%"), Tag.tag_group.ilike(f"%{tag}%")))
        )
        stmt = stmt.where(Organization.id.in_(tag_org_ids))
    if q:
        q_like = f"%{q}%"
        q_tag_org_ids = (
            select(OrganizationTag.organization_id)
            .join(Tag, Tag.id == OrganizationTag.tag_id)
            .where(or_(Tag.code.ilike(q_like), Tag.label.ilike(q_like), Tag.tag_group.ilike(q_like)))
        )
        stmt = stmt.where(
            or_(
                Organization.name.ilike(q_like),
                Organization.normalized_name.ilike(q_like),
                Organization.website_url.ilike(q_like),
                Organization.website_domain.ilike(q_like),
                Organization.solution_summary.ilike(q_like),
                Organization.source_text.ilike(q_like),
                Organization.category_code.ilike(q_like),
                Organization.category_label.ilike(q_like),
                Organization.vertical_text.ilike(q_like),
                Organization.added_by_text.ilike(q_like),
                Organization.id.in_(q_tag_org_ids),
            )
        )

    total_count = int(db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one())
    result = db.execute(_ordered(stmt, sort_by).offset(skip).limit(limit))
    return {
        "items": [_summary(db, org) for org in result.scalars().all()],
        "total_count": total_count,
        "limit": limit,
        "offset": skip,
        "sort_by": sort_by,
    }


@router.get("/export")
async def export_organizations(
    q: str | None = None,
    organization_type: str | None = None,
    organization_subtype: str | None = None,
    category: str | None = None,
    vertical: str | None = None,
    expertise: str | None = None,
    contact_person: str | None = None,
    notes: str | None = None,
    borusan_company_code: str | None = None,
    status_code: str | None = None,
    relationship_status_code: str | None = None,
    geography: str | None = None,
    source: str | None = None,
    added_by: str | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    items: list[dict[str, Any]] = []
    skip = 0
    while True:
        response = await list_organizations(
            q=q,
            organization_type=organization_type,
            organization_subtype=organization_subtype,
            category=category,
            vertical=vertical,
            expertise=expertise,
            contact_person=contact_person,
            notes=notes,
            borusan_company_code=borusan_company_code,
            status_code=status_code,
            relationship_status_code=relationship_status_code,
            geography=geography,
            source=source,
            added_by=added_by,
            include_archived=include_archived and current_user.role == "ADMIN",
            skip=skip,
            limit=500,
            sort_by="newest",
            db=db,
            current_user=current_user,
        )
        page_items = response["items"]
        items.extend(page_items)
        if len(page_items) < 500:
            break
        skip += 500
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Name",
            "Type",
            "Category",
            "Vertical",
            "Website",
            "Domain",
            "Geography",
            "Status",
            "Added By",
            "Added Date",
            "Last Contact",
            "Source",
            "Solution Summary",
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.get("name"),
                item.get("organization_type"),
                item.get("category_label"),
                item.get("vertical_text"),
                item.get("website_url"),
                item.get("website_domain"),
                item.get("geography_text"),
                (item.get("lifecycle_status") or {}).get("label"),
                item.get("added_by_display"),
                item.get("created_at"),
                item.get("last_contact_date"),
                item.get("source_text"),
                item.get("solution_summary"),
            ]
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="startup_library_export.csv"'},
    )


@router.get("/{organization_id}")
async def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    organization = await service.get(db, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return _detail(db, organization)


@router.patch("/{organization_id}/archive", response_model=OrganizationRead)
async def archive_organization(
    organization_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Organization:
    return await archive_record(
        db,
        await service.get(db, organization_id),
        entity_type="ORGANIZATION",
        entity_id=organization_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.patch("/{organization_id}/unarchive", response_model=OrganizationRead)
async def unarchive_organization(
    organization_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Organization:
    return await unarchive_record(
        db,
        await service.get(db, organization_id),
        entity_type="ORGANIZATION",
        entity_id=organization_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Organization:
    organization = await service.create(db, _prepare_create(payload, current_user.id))
    await write_audit_log(
        db,
        action="ORGANIZATION_CREATED",
        entity_type="ORGANIZATION",
        entity_id=organization.id,
        actor_user_id=current_user.id,
        after_data=OrganizationRead.model_validate(organization).model_dump(mode="json"),
        commit=True,
    )
    await write_user_contribution(
        db,
        user_id=current_user.id,
        contribution_type="ORGANIZATION_CREATED",
        entity_type="ORGANIZATION",
        entity_id=organization.id,
        metadata_json={"name": organization.name, "organization_type": organization.organization_type},
        commit=True,
    )
    await write_champion_activity(
        db,
        user_id=current_user.id,
        category="ECOSYSTEM_LIBRARY",
        activity_type="VENDOR_ADDED" if (organization.organization_type or "").upper() == "VENDOR" else "STARTUP_ADDED",
        related_entity_type="ORGANIZATION",
        related_entity_id=organization.id,
        notes=f"{organization.organization_type}: {organization.name}",
        created_by_user_id=current_user.id,
        commit=True,
    )
    return organization


async def _update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    db: Session,
    current_user: User,
) -> Organization:
    organization = await service.get(db, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    before_status_id = organization.lifecycle_status_id
    before_last_contact_date = organization.last_contact_date
    before = OrganizationRead.model_validate(organization).model_dump(mode="json")
    organization = await service.update(db, organization, _prepare_update(payload, current_user.id, db))
    after = OrganizationRead.model_validate(organization).model_dump(mode="json")
    await write_audit_log(
        db,
        action="ORGANIZATION_UPDATED",
        entity_type="ORGANIZATION",
        entity_id=organization.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=after,
    )
    if before_status_id != organization.lifecycle_status_id and organization.lifecycle_status_id:
        db.add(
            OrganizationStatusHistory(
                organization_id=organization.id,
                status_id=organization.lifecycle_status_id,
                changed_by_user_id=current_user.id,
                changed_at=datetime.now(timezone.utc),
                note="Status changed from CRM UI",
            )
        )
        await write_audit_log(
            db,
            action="ORGANIZATION_STATUS_CHANGED",
            entity_type="ORGANIZATION",
            entity_id=organization.id,
            actor_user_id=current_user.id,
            before_data={"lifecycle_status_id": str(before_status_id) if before_status_id else None},
            after_data={"lifecycle_status_id": str(organization.lifecycle_status_id)},
        )
    if before_last_contact_date != organization.last_contact_date:
        await write_audit_log(
            db,
            action="ORGANIZATION_LAST_CONTACT_CHANGED",
            entity_type="ORGANIZATION",
            entity_id=organization.id,
            actor_user_id=current_user.id,
            before_data={"last_contact_date": before_last_contact_date.isoformat() if before_last_contact_date else None},
            after_data={"last_contact_date": organization.last_contact_date.isoformat() if organization.last_contact_date else None},
        )
    if before != after:
        await write_user_contribution(
            db,
            user_id=current_user.id,
            contribution_type="ORGANIZATION_UPDATED",
            entity_type="ORGANIZATION",
            entity_id=organization.id,
            metadata_json={"name": organization.name},
        )
    db.commit()
    db.refresh(organization)
    return organization


def _document_payload(db: Session, document: OrganizationDocument) -> dict[str, Any]:
    data = OrganizationDocumentRead.model_validate(document).model_dump(mode="json")
    data["uploaded_by_user"] = _user_payload(db, document.uploaded_by_user_id)
    data["download_url"] = f"/api/v1/organizations/{document.organization_id}/documents/{document.id}/download"
    return data


def _get_document_or_404(db: Session, organization_id: UUID, document_id: UUID) -> OrganizationDocument:
    document = db.get(OrganizationDocument, document_id)
    if document is None or document.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization document not found")
    return document


@router.get("/{organization_id}/documents")
async def list_organization_documents(
    organization_id: UUID,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    if await service.get(db, organization_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    stmt = select(OrganizationDocument).where(OrganizationDocument.organization_id == organization_id)
    if not include_archived or current_user.role != "ADMIN":
        stmt = stmt.where(not_archived(OrganizationDocument.is_archived))
    try:
        rows = db.execute(stmt.order_by(OrganizationDocument.uploaded_at.desc(), OrganizationDocument.id.desc())).scalars().all()
    except SQLAlchemyError:
        db.rollback()
        return []
    return [_document_payload(db, row) for row in rows]


@router.post("/{organization_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_organization_document(
    organization_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    if await service.get(db, organization_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_DECK_SUFFIXES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF and PPTX startup decks are supported")
    if file.content_type not in ALLOWED_DECK_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported startup deck content type")

    contents = await file.read()
    if len(contents) > MAX_DECK_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Startup deck exceeds 50 MB limit")
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Startup deck file is empty")

    DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(contents).hexdigest()
    stored_filename = f"{uuid4()}{suffix}"
    storage_path = DOCUMENT_UPLOAD_DIR / stored_filename
    storage_path.write_bytes(contents)

    document = OrganizationDocument(
        organization_id=organization_id,
        uploaded_by_user_id=current_user.id,
        document_type="STARTUP_DECK",
        original_filename=Path(file.filename or stored_filename).name,
        stored_filename=stored_filename,
        file_path=str(storage_path),
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(contents),
        sha256_hash=digest,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    payload = _document_payload(db, document)
    await write_audit_log(
        db,
        action="STARTUP_DECK_UPLOADED",
        entity_type="ORGANIZATION_DOCUMENT",
        entity_id=document.id,
        actor_user_id=current_user.id,
        after_data=payload,
        commit=True,
    )
    await write_champion_activity(
        db,
        user_id=current_user.id,
        category="ECOSYSTEM_LIBRARY",
        activity_type="DECK_UPLOADED",
        related_entity_type="ORGANIZATION_DOCUMENT",
        related_entity_id=document.id,
        notes=document.original_filename,
        created_by_user_id=current_user.id,
        commit=True,
    )
    return payload


@router.get("/{organization_id}/documents/{document_id}/download")
async def download_organization_document(
    organization_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    document = _get_document_or_404(db, organization_id, document_id)
    if document.is_archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization document is archived")
    path = Path(document.file_path)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored startup deck file not found")
    return FileResponse(path, media_type=document.mime_type, filename=document.original_filename)


@router.patch("/{organization_id}/documents/{document_id}/archive")
async def archive_organization_document(
    organization_id: UUID,
    document_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    document = _get_document_or_404(db, organization_id, document_id)
    if current_user.role != "ADMIN" and document.uploaded_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins or the uploader can archive this deck")
    document = await archive_record(
        db,
        document,
        entity_type="ORGANIZATION_DOCUMENT",
        entity_id=document_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _document_payload(db, document)


@router.patch("/{organization_id}/documents/{document_id}/unarchive")
async def unarchive_organization_document(
    organization_id: UUID,
    document_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    document = _get_document_or_404(db, organization_id, document_id)
    if current_user.role != "ADMIN" and document.uploaded_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins or the uploader can restore this deck")
    document = await unarchive_record(
        db,
        document,
        entity_type="ORGANIZATION_DOCUMENT",
        entity_id=document_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _document_payload(db, document)


@router.patch("/{organization_id}", response_model=OrganizationRead)
async def patch_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Organization:
    return await _update_organization(organization_id, payload, db, current_user)


@router.put("/{organization_id}", response_model=OrganizationRead)
async def put_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Organization:
    return await _update_organization(organization_id, payload, db, current_user)


@router.get("/{organization_id}/contacts", response_model=list[ContactRead])
async def list_organization_contacts(
    organization_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Contact]:
    return list(
        db.execute(
            select(Contact)
            .where(Contact.organization_id == organization_id, not_archived(Contact.is_archived))
            .order_by(Contact.full_name.asc(), Contact.email.asc(), Contact.id.asc())
        )
        .scalars()
        .all()
    )


@router.post("/{organization_id}/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_organization_contact(
    organization_id: UUID,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Contact:
    if await service.get(db, organization_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    data = payload.model_dump(exclude_unset=True)
    data.pop("organization_id", None)
    contact = Contact(organization_id=organization_id, created_by_user_id=current_user.id, updated_by_user_id=current_user.id, **data)
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
        metadata_json={"organization_id": str(organization_id)},
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


@router.get("/{organization_id}/notes", response_model=list[NoteRead])
async def list_organization_notes(
    organization_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Note]:
    return list(
        db.execute(
            select(Note)
            .where(Note.entity_type == "ORGANIZATION", Note.entity_id == organization_id, not_archived(Note.is_archived))
            .order_by(Note.occurred_at.desc(), Note.created_at.desc(), Note.id.desc())
        )
        .scalars()
        .all()
    )


@router.post("/{organization_id}/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_organization_note(
    organization_id: UUID,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Note:
    if await service.get(db, organization_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    data = payload.model_dump(exclude_unset=True)
    data.pop("created_by_user_id", None)
    note = Note(entity_type="ORGANIZATION", entity_id=organization_id, created_by_user_id=current_user.id, **data)
    db.add(note)
    db.commit()
    db.refresh(note)
    await write_audit_log(
        db,
        action="NOTE_CREATED",
        entity_type="NOTE",
        entity_id=note.id,
        actor_user_id=current_user.id,
        after_data=NoteRead.model_validate(note).model_dump(mode="json"),
        commit=True,
    )
    await write_user_contribution(
        db,
        user_id=current_user.id,
        contribution_type="NOTE_CREATED",
        entity_type="NOTE",
        entity_id=note.id,
        metadata_json={"organization_id": str(organization_id), "note_type": note.note_type},
        commit=True,
    )
    return note


@router.get("/{organization_id}/borusan-fit")
async def list_organization_borusan_fit(
    organization_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    return _fits(db, organization_id)


@router.post("/{organization_id}/borusan-fit", response_model=OrganizationBorusanFitRead, status_code=status.HTTP_201_CREATED)
async def create_organization_borusan_fit(
    organization_id: UUID,
    payload: OrganizationBorusanFitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationBorusanFit:
    if await service.get(db, organization_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    fit = OrganizationBorusanFit(organization_id=organization_id, **payload.model_dump())
    db.add(fit)
    db.commit()
    db.refresh(fit)
    await write_audit_log(
        db,
        action="BORUSAN_FIT_CREATED",
        entity_type="ORGANIZATION_BORUSAN_FIT",
        entity_id=fit.id,
        actor_user_id=current_user.id,
        after_data=OrganizationBorusanFitRead.model_validate(fit).model_dump(mode="json"),
        commit=True,
    )
    await write_user_contribution(
        db,
        user_id=current_user.id,
        contribution_type="BORUSAN_FIT_CREATED",
        entity_type="ORGANIZATION_BORUSAN_FIT",
        entity_id=fit.id,
        metadata_json={"organization_id": str(organization_id), "borusan_company_id": str(fit.borusan_company_id)},
        commit=True,
    )
    return fit


@router.put("/{organization_id}/borusan-fit/{fit_id}", response_model=OrganizationBorusanFitRead)
async def update_organization_borusan_fit(
    organization_id: UUID,
    fit_id: UUID,
    payload: OrganizationBorusanFitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationBorusanFit:
    fit = db.get(OrganizationBorusanFit, fit_id)
    if fit is None or fit.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borusan fit not found")
    before = OrganizationBorusanFitRead.model_validate(fit).model_dump(mode="json")
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(fit, field_name, value)
    db.add(fit)
    db.commit()
    db.refresh(fit)
    await write_audit_log(
        db,
        action="BORUSAN_FIT_UPDATED",
        entity_type="ORGANIZATION_BORUSAN_FIT",
        entity_id=fit.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=OrganizationBorusanFitRead.model_validate(fit).model_dump(mode="json"),
        commit=True,
    )
    return fit


@router.patch("/{organization_id}/borusan-fit/{fit_id}/archive", response_model=OrganizationBorusanFitRead)
async def archive_organization_borusan_fit(
    organization_id: UUID,
    fit_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> OrganizationBorusanFit:
    fit = db.get(OrganizationBorusanFit, fit_id)
    if fit is None or fit.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borusan fit not found")
    return await archive_record(
        db,
        fit,
        entity_type="ORGANIZATION_BORUSAN_FIT",
        entity_id=fit_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.patch("/{organization_id}/borusan-fit/{fit_id}/unarchive", response_model=OrganizationBorusanFitRead)
async def unarchive_organization_borusan_fit(
    organization_id: UUID,
    fit_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> OrganizationBorusanFit:
    fit = db.get(OrganizationBorusanFit, fit_id)
    if fit is None or fit.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borusan fit not found")
    return await unarchive_record(
        db,
        fit,
        entity_type="ORGANIZATION_BORUSAN_FIT",
        entity_id=fit_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.delete("/{organization_id}/borusan-fit/{fit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization_borusan_fit(
    organization_id: UUID,
    fit_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    fit = db.get(OrganizationBorusanFit, fit_id)
    if fit is None or fit.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borusan fit not found")
    await archive_record(
        db,
        fit,
        entity_type="ORGANIZATION_BORUSAN_FIT",
        entity_id=fit_id,
        actor=current_user,
        reason="Archived via legacy DELETE endpoint",
    )
