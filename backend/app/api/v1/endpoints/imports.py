import hashlib
import re
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import ImportBatch, ImportCandidate, User
from app.schemas import (
    ImportBatchCreate,
    ImportBatchRead,
    ImportBatchUpdate,
    ImportCandidateDecisionUpdate,
    ImportCandidateRead,
)
from app.services.audit import write_audit_log
from app.services.crud import CRUDService
from app.services.excel_import.candidates import ImportCandidateService
from app.services.excel_import.pipeline import ExcelImportPipeline

router = APIRouter(prefix="/imports", tags=["imports"])
service = CRUDService[ImportBatch, ImportBatchCreate, ImportBatchUpdate](ImportBatch)

PROJECT_ROOT = Path(__file__).resolve().parents[5]
BACKEND_ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIR = PROJECT_ROOT / "config"
UPLOAD_DIR = BACKEND_ROOT / "uploads" / "imports"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
pipeline = ExcelImportPipeline(CONFIG_DIR)
candidate_service = ImportCandidateService(CONFIG_DIR)


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(filename).name).strip("._")
    return cleaned or "workbook.xlsx"


@router.get("", response_model=list[ImportBatchRead])
async def list_import_batches(
    status_filter: str | None = Query(default=None, alias="status"),
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ImportBatch]:
    return list(
        await service.list(
            db,
            skip=skip,
            limit=limit,
            filters={"status": status_filter},
            order_by=[ImportBatch.created_at.desc(), ImportBatch.id.desc()],
        )
    )


@router.get("/{batch_id}", response_model=ImportBatchRead)
async def get_import_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ImportBatch:
    batch = await service.get(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import batch not found")
    return batch


@router.post("/upload", response_model=ImportBatchRead, status_code=status.HTTP_201_CREATED)
async def upload_import_workbook(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ImportBatch:
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx workbook uploads are supported.",
        )

    contents = await file.read()
    file_size = len(contents)
    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded workbook is empty.")
    if not contents.startswith(b"PK"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid .xlsx workbook container.",
        )
    if file_size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Workbook exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit.",
        )

    file_sha256 = hashlib.sha256(contents).hexdigest()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    storage_path = UPLOAD_DIR / f"{file_sha256[:16]}_{_safe_filename(filename)}"
    storage_path.write_bytes(contents)

    try:
        batch = pipeline.stage_workbook(
            db,
            workbook_path=storage_path,
            original_filename=Path(filename).name,
            file_sha256=file_sha256,
            file_size_bytes=file_size,
            uploaded_by_user_id=current_user.id,
        )
        await write_audit_log(
            db,
            action="IMPORT_UPLOAD_STAGED",
            entity_type="ImportBatch",
            actor_user_id=current_user.id,
            entity_id=batch.id,
            after_data={
                "original_filename": batch.original_filename,
                "file_sha256": batch.file_sha256,
                "status": batch.status,
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            commit=True,
        )
        return batch
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workbook could not be profiled and staged: {exc}",
        ) from exc


@router.get("/{batch_id}/preview")
async def get_import_preview(
    batch_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    try:
        return pipeline.build_preview(db, batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{batch_id}/candidates/generate")
async def generate_import_candidates(
    batch_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    try:
        return candidate_service.generate_candidates(db, batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{batch_id}/candidates")
async def get_import_candidates(
    batch_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    try:
        return candidate_service.build_candidate_preview(db, batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/candidates/{candidate_id}/decision", response_model=ImportCandidateRead)
async def update_import_candidate_decision(
    candidate_id: UUID,
    payload: ImportCandidateDecisionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ImportCandidate:
    try:
        return candidate_service.update_decision(
            db,
            candidate_id,
            decision_status=payload.decision_status,
            decision_reason=payload.decision_reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{batch_id}/commit")
async def commit_import_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    try:
        return candidate_service.commit(db, batch_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("", response_model=ImportBatchRead, status_code=status.HTTP_201_CREATED)
async def create_import_batch(
    payload: ImportBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImportBatch:
    if payload.uploaded_by_user_id is None:
        payload = payload.model_copy(update={"uploaded_by_user_id": current_user.id})
    return await service.create(db, payload)


@router.patch("/{batch_id}", response_model=ImportBatchRead)
async def update_import_batch(
    batch_id: UUID,
    payload: ImportBatchUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ImportBatch:
    batch = await service.get(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import batch not found")
    return await service.update(db, batch, payload)
