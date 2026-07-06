import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import Opportunity, OpportunityDocument, User
from app.schemas import ArchiveRequest, OpportunityCreate, OpportunityDocumentRead, OpportunityRead, OpportunityUpdate
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.champion_score import write_champion_activity
from app.services.contributions import write_user_contribution
from app.services.crud import CRUDService
from app.services.soft_delete import not_archived

router = APIRouter(prefix="/opportunities", tags=["opportunities"])
service = CRUDService[Opportunity, OpportunityCreate, OpportunityUpdate](Opportunity)

POC_STAGE_ORDER = ["IDEA", "SCOUTING", "SHORT_LISTING", "POC", "POST_POC"]
POC_STAGE_ALIASES = {
    "": "IDEA",
    "IDEA": "IDEA",
    "SCOUTING": "SCOUTING",
    "DISCOVERY": "SCOUTING",
    "DISCUSSIONS_ONGOING": "SCOUTING",
    "EVALUATION": "SHORT_LISTING",
    "SHORTLIST": "SHORT_LISTING",
    "SHORT_LIST": "SHORT_LISTING",
    "SHORT_LISTING": "SHORT_LISTING",
    "POC_PLANNED": "POC",
    "POC_ACTIVE": "POC",
    "POC": "POC",
    "PILOT": "POC",
    "COMPLETED": "POST_POC",
    "ON_HOLD": "POST_POC",
    "CANCELLED": "POST_POC",
    "POST_POC": "POST_POC",
}

DOCUMENT_UPLOAD_DIR = Path(__file__).resolve().parents[5] / "uploads" / "opportunity_documents"
MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".pptx", ".docx", ".xlsx"}
ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class OpportunityStageUpdate(BaseModel):
    stage: str


def normalize_poc_stage(stage: str | None) -> str:
    raw_stage = (stage or "").strip().upper().replace(" ", "_").replace("-", "_")
    normalized = POC_STAGE_ALIASES.get(raw_stage)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported PoC stage '{stage}'. Expected one of: {', '.join(POC_STAGE_ORDER)}.",
        )
    return normalized


def _safe_original_filename(file: UploadFile) -> str:
    filename = Path(file.filename or "poc-document").name
    return filename[:255] or "poc-document"


def _document_payload(db: Session, document: OpportunityDocument) -> dict:
    data = OpportunityDocumentRead.model_validate(document).model_dump(mode="json")
    uploader = db.get(User, document.uploaded_by_user_id) if document.uploaded_by_user_id else None
    data["uploaded_by_user"] = (
        {"id": uploader.id, "full_name": uploader.full_name, "email": uploader.email, "role": uploader.role}
        if uploader
        else None
    )
    data["download_url"] = f"/api/v1/opportunities/{document.opportunity_id}/documents/{document.id}/download"
    return data


def _get_opportunity_or_404(db: Session, opportunity_id: UUID) -> Opportunity:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return opportunity


def _get_document_or_404(db: Session, opportunity_id: UUID, document_id: UUID) -> OpportunityDocument:
    document = db.get(OpportunityDocument, document_id)
    if document is None or document.opportunity_id != opportunity_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity document not found")
    return document


@router.get("", response_model=list[OpportunityRead])
async def list_opportunities(
    stage: str | None = None,
    borusan_company_id: UUID | None = None,
    organization_id: UUID | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Opportunity]:
    normalized_stage = normalize_poc_stage(stage) if stage else None
    return list(
        await service.list(
            db,
            skip=skip,
            limit=limit,
            filters={
                "stage": normalized_stage,
                "borusan_company_id": borusan_company_id,
                "organization_id": organization_id,
            },
            order_by=[Opportunity.updated_at.desc(), Opportunity.id.desc()],
            include_archived=include_archived and current_user.role == "ADMIN",
        )
    )


@router.get("/{opportunity_id}", response_model=OpportunityRead)
async def get_opportunity(opportunity_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Opportunity:
    return _get_opportunity_or_404(db, opportunity_id)


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Opportunity:
    data = payload.model_dump(exclude_unset=True)
    data["stage"] = normalize_poc_stage(data.get("stage"))
    data["created_by_user_id"] = current_user.id
    data["updated_by_user_id"] = current_user.id
    opportunity = Opportunity(**data)
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    await write_audit_log(
        db,
        action="OPPORTUNITY_CREATED",
        entity_type="OPPORTUNITY",
        entity_id=opportunity.id,
        actor_user_id=current_user.id,
        after_data=OpportunityRead.model_validate(opportunity).model_dump(mode="json"),
        commit=True,
    )
    await write_user_contribution(
        db,
        user_id=current_user.id,
        contribution_type="OPPORTUNITY_CREATED",
        entity_type="OPPORTUNITY",
        entity_id=opportunity.id,
        metadata_json={"title": opportunity.title, "organization_id": str(opportunity.organization_id)},
        commit=True,
    )
    await write_champion_activity(
        db,
        user_id=current_user.id,
        category="VISION_STRATEGY",
        activity_type="OPPORTUNITY_CREATED",
        related_entity_type="OPPORTUNITY",
        related_entity_id=opportunity.id,
        notes=opportunity.title,
        created_by_user_id=current_user.id,
        commit=True,
    )
    return opportunity


@router.patch("/{opportunity_id}", response_model=OpportunityRead)
async def update_opportunity(
    opportunity_id: UUID,
    payload: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Opportunity:
    opportunity = _get_opportunity_or_404(db, opportunity_id)
    before = OpportunityRead.model_validate(opportunity).model_dump(mode="json")
    data = payload.model_dump(exclude_unset=True)
    if "stage" in data:
        data["stage"] = normalize_poc_stage(data.get("stage"))
    data["updated_by_user_id"] = current_user.id
    for field_name, value in data.items():
        setattr(opportunity, field_name, value)
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    await write_audit_log(
        db,
        action="OPPORTUNITY_UPDATED",
        entity_type="OPPORTUNITY",
        entity_id=opportunity.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=OpportunityRead.model_validate(opportunity).model_dump(mode="json"),
        commit=True,
    )
    return opportunity


@router.put("/{opportunity_id}", response_model=OpportunityRead)
async def put_opportunity(
    opportunity_id: UUID,
    payload: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Opportunity:
    return await update_opportunity(opportunity_id, payload, db, current_user)


@router.patch("/{opportunity_id}/stage", response_model=OpportunityRead)
async def update_opportunity_stage(
    opportunity_id: UUID,
    payload: OpportunityStageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Opportunity:
    opportunity = _get_opportunity_or_404(db, opportunity_id)
    before = OpportunityRead.model_validate(opportunity).model_dump(mode="json")
    opportunity.stage = normalize_poc_stage(payload.stage)
    opportunity.stage_migration_note = None
    opportunity.updated_by_user_id = current_user.id
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    await write_audit_log(
        db,
        action="OPPORTUNITY_STAGE_UPDATED",
        entity_type="OPPORTUNITY",
        entity_id=opportunity.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=OpportunityRead.model_validate(opportunity).model_dump(mode="json"),
        commit=True,
    )
    return opportunity


@router.patch("/{opportunity_id}/archive", response_model=OpportunityRead)
async def archive_opportunity(
    opportunity_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Opportunity:
    return await archive_record(
        db,
        await service.get(db, opportunity_id),
        entity_type="OPPORTUNITY",
        entity_id=opportunity_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.patch("/{opportunity_id}/unarchive", response_model=OpportunityRead)
async def unarchive_opportunity(
    opportunity_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Opportunity:
    return await unarchive_record(
        db,
        await service.get(db, opportunity_id),
        entity_type="OPPORTUNITY",
        entity_id=opportunity_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.get("/{opportunity_id}/documents")
async def list_opportunity_documents(
    opportunity_id: UUID,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    _get_opportunity_or_404(db, opportunity_id)
    stmt = select(OpportunityDocument).where(OpportunityDocument.opportunity_id == opportunity_id)
    if not (include_archived and current_user.role == "ADMIN"):
        stmt = stmt.where(not_archived(OpportunityDocument.is_archived))
    rows = db.execute(stmt.order_by(OpportunityDocument.uploaded_at.desc(), OpportunityDocument.id.desc())).scalars().all()
    return [_document_payload(db, row) for row in rows]


@router.post("/{opportunity_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_opportunity_document(
    opportunity_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    _get_opportunity_or_404(db, opportunity_id)
    original_filename = _safe_original_filename(file)
    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF, PPTX, DOCX, and XLSX PoC documents are supported")
    if file.content_type not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported PoC document content type")
    content = await file.read()
    if len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PoC document exceeds the 50 MB upload limit")
    DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    sha256_hash = hashlib.sha256(content).hexdigest()
    stored_filename = f"{uuid.uuid4()}{extension}"
    file_path = DOCUMENT_UPLOAD_DIR / stored_filename
    file_path.write_bytes(content)
    document = OpportunityDocument(
        opportunity_id=opportunity_id,
        uploaded_by_user_id=current_user.id,
        document_type="POC_DOCUMENT",
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(content),
        sha256_hash=sha256_hash,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    payload = _document_payload(db, document)
    await write_audit_log(
        db,
        action="OPPORTUNITY_DOCUMENT_UPLOADED",
        entity_type="OPPORTUNITY_DOCUMENT",
        entity_id=document.id,
        actor_user_id=current_user.id,
        after_data=payload,
        commit=True,
    )
    return payload


@router.get("/{opportunity_id}/documents/{document_id}/download")
async def download_opportunity_document(
    opportunity_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    document = _get_document_or_404(db, opportunity_id, document_id)
    if document.is_archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity document is archived")
    path = Path(document.file_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored PoC document file not found")
    return FileResponse(path, media_type=document.mime_type, filename=document.original_filename)


@router.patch("/{opportunity_id}/documents/{document_id}/archive")
async def archive_opportunity_document(
    opportunity_id: UUID,
    document_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    document = _get_document_or_404(db, opportunity_id, document_id)
    if current_user.role != "ADMIN" and document.uploaded_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins or the uploader can archive this PoC document")
    document = await archive_record(
        db,
        document,
        entity_type="OPPORTUNITY_DOCUMENT",
        entity_id=document_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _document_payload(db, document)


@router.patch("/{opportunity_id}/documents/{document_id}/unarchive")
async def unarchive_opportunity_document(
    opportunity_id: UUID,
    document_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    document = _get_document_or_404(db, opportunity_id, document_id)
    document = await unarchive_record(
        db,
        document,
        entity_type="OPPORTUNITY_DOCUMENT",
        entity_id=document_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _document_payload(db, document)
