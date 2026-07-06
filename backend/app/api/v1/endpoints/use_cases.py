from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import BorusanCompany, Organization, UseCaseProposal, User
from app.schemas import ArchiveRequest, UseCaseProposalCreate, UseCaseProposalRead, UseCaseProposalUpdate
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.champion_score import write_champion_activity
from app.services.contributions import write_user_contribution
from app.services.soft_delete import not_archived

router = APIRouter()


def _user_payload(db: Session, user_id: UUID | None) -> dict[str, Any] | None:
    if not user_id:
        return None
    user = db.get(User, user_id)
    if user is None:
        return {"id": user_id, "full_name": None, "email": None}
    return {"id": user.id, "full_name": user.full_name, "email": user.email}


def _use_case_payload(db: Session, use_case: UseCaseProposal) -> dict[str, Any]:
    data = UseCaseProposalRead.model_validate(use_case).model_dump(mode="json")
    company = db.get(BorusanCompany, use_case.borusan_company_id) if use_case.borusan_company_id else None
    organization = db.get(Organization, use_case.related_organization_id) if use_case.related_organization_id else None
    data["proposer_user"] = _user_payload(db, use_case.proposer_user_id)
    data["created_by_user"] = _user_payload(db, use_case.created_by_user_id)
    data["borusan_company"] = {"id": company.id, "code": company.code, "name": company.english_name or company.name} if company else None
    data["related_organization"] = {"id": organization.id, "name": organization.name} if organization else None
    return data


@router.get("")
async def list_use_cases(
    q: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    stage: str | None = None,
    borusan_company_id: UUID | None = None,
    proposer_user_id: UUID | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    stmt = select(UseCaseProposal)
    if not include_archived or current_user.role != "ADMIN":
        stmt = stmt.where(not_archived(UseCaseProposal.is_archived))
    if status_filter:
        stmt = stmt.where(UseCaseProposal.status == status_filter)
    if stage:
        stmt = stmt.where(UseCaseProposal.stage == stage)
    if borusan_company_id:
        stmt = stmt.where(UseCaseProposal.borusan_company_id == borusan_company_id)
    if proposer_user_id:
        stmt = stmt.where(UseCaseProposal.proposer_user_id == proposer_user_id)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                UseCaseProposal.title.ilike(pattern),
                UseCaseProposal.description.ilike(pattern),
                UseCaseProposal.business_unit_text.ilike(pattern),
                UseCaseProposal.problem_area.ilike(pattern),
                UseCaseProposal.proposed_solution.ilike(pattern),
                UseCaseProposal.expected_impact.ilike(pattern),
            )
        )
    rows = db.execute(stmt.order_by(UseCaseProposal.created_at.desc(), UseCaseProposal.id.desc()).offset(skip).limit(limit)).scalars().all()
    return {"items": [_use_case_payload(db, row) for row in rows], "limit": limit, "offset": skip}


@router.get("/{use_case_id}")
async def get_use_case(
    use_case_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    use_case = db.get(UseCaseProposal, use_case_id)
    if use_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    return _use_case_payload(db, use_case)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_use_case(
    payload: UseCaseProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = payload.model_dump(exclude_unset=True)
    data["created_by_user_id"] = current_user.id
    data["proposer_user_id"] = data.get("proposer_user_id") or current_user.id
    use_case = UseCaseProposal(**data)
    db.add(use_case)
    db.commit()
    db.refresh(use_case)
    response = _use_case_payload(db, use_case)
    await write_audit_log(
        db,
        action="USE_CASE_CREATED",
        entity_type="USE_CASE_PROPOSAL",
        entity_id=use_case.id,
        actor_user_id=current_user.id,
        after_data=response,
        commit=True,
    )
    await write_user_contribution(
        db,
        user_id=current_user.id,
        contribution_type="USE_CASE_CREATED",
        entity_type="USE_CASE_PROPOSAL",
        entity_id=use_case.id,
        metadata_json={"title": use_case.title},
        commit=True,
    )
    await write_champion_activity(
        db,
        user_id=use_case.proposer_user_id or current_user.id,
        category="VISION_STRATEGY",
        activity_type="USE_CASE_PROPOSED",
        related_entity_type="USE_CASE_PROPOSAL",
        related_entity_id=use_case.id,
        notes=use_case.title,
        created_by_user_id=current_user.id,
        commit=True,
    )
    return response


@router.put("/{use_case_id}")
async def update_use_case(
    use_case_id: UUID,
    payload: UseCaseProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    use_case = db.get(UseCaseProposal, use_case_id)
    if use_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Use case not found")
    before = _use_case_payload(db, use_case)
    before_projectized = use_case.stage == "PROJECTIZED" or use_case.status == "PROJECTIZED"
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(use_case, field_name, value)
    db.add(use_case)
    db.commit()
    db.refresh(use_case)
    after_projectized = use_case.stage == "PROJECTIZED" or use_case.status == "PROJECTIZED"
    response = _use_case_payload(db, use_case)
    await write_audit_log(
        db,
        action="USE_CASE_UPDATED",
        entity_type="USE_CASE_PROPOSAL",
        entity_id=use_case.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=response,
        commit=True,
    )
    if after_projectized and not before_projectized:
        await write_champion_activity(
            db,
            user_id=use_case.proposer_user_id or use_case.created_by_user_id,
            category="VISION_STRATEGY",
            activity_type="USE_CASE_PROJECTIZED",
            related_entity_type="USE_CASE_PROPOSAL",
            related_entity_id=use_case.id,
            notes=use_case.title,
            created_by_user_id=current_user.id,
            commit=True,
        )
    return response


@router.patch("/{use_case_id}/archive")
async def archive_use_case(
    use_case_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    record = await archive_record(
        db,
        db.get(UseCaseProposal, use_case_id),
        entity_type="USE_CASE_PROPOSAL",
        entity_id=use_case_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _use_case_payload(db, record)


@router.patch("/{use_case_id}/unarchive")
async def unarchive_use_case(
    use_case_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    record = await unarchive_record(
        db,
        db.get(UseCaseProposal, use_case_id),
        entity_type="USE_CASE_PROPOSAL",
        entity_id=use_case_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _use_case_payload(db, record)
