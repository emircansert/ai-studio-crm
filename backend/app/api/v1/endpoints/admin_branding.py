import hashlib
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import BrandingAsset, User
from app.schemas import BrandingAssetCreate, BrandingAssetRead, BrandingAssetUpdate
from app.services.audit import write_audit_log
from app.services.crud import CRUDService

router = APIRouter(prefix="/admin/branding", tags=["admin-branding"])
service = CRUDService[BrandingAsset, BrandingAssetCreate, BrandingAssetUpdate](BrandingAsset)

ALLOWED_LOGO_TYPES = {"image/png", "image/jpeg", "image/svg+xml", "image/webp"}
ALLOWED_LOGO_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".webp"}
MAX_LOGO_SIZE_BYTES = 5 * 1024 * 1024
UPLOAD_DIR = Path(__file__).resolve().parents[5] / "uploads" / "branding"
FALLBACK_CONTENT_TYPES = {"", "application/octet-stream", None}


def _asset_payload(asset: BrandingAsset) -> dict[str, object]:
    data = BrandingAssetRead.model_validate(asset).model_dump(mode="json")
    data["content_url"] = f"/api/v1/admin/branding/{asset.id}/content"
    return data


@router.get("", response_model=list[BrandingAssetRead])
async def list_branding_assets(
    asset_type: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[BrandingAsset]:
    return list(
        await service.list(
            db,
            skip=skip,
            limit=limit,
            filters={"asset_type": asset_type, "is_active": is_active},
            order_by=[BrandingAsset.created_at.desc(), BrandingAsset.id.desc()],
        )
    )


@router.get("/active")
async def get_active_branding_asset(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, object] | None:
    asset = (
        db.execute(
            select(BrandingAsset)
            .where(BrandingAsset.asset_type == "LOGO", BrandingAsset.is_active == true())
            .order_by(BrandingAsset.created_at.desc(), BrandingAsset.id.desc())
        )
        .scalars()
        .first()
    )
    return _asset_payload(asset) if asset else None


@router.get("/{asset_id}/content")
async def get_branding_asset_content(
    asset_id: UUID,
    db: Session = Depends(get_db),
) -> FileResponse:
    asset = await service.get(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branding asset not found")
    if asset.asset_type != "LOGO":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branding asset not found")
    path = Path(asset.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored logo file not found")
    return FileResponse(path, media_type=asset.content_type, filename=asset.original_filename)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_branding_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, object]:
    suffix = Path(file.filename or "logo").suffix.lower()
    if suffix not in ALLOWED_LOGO_SUFFIXES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported logo file extension")

    content_type = file.content_type
    if content_type in FALLBACK_CONTENT_TYPES:
        content_type = mimetypes.types_map.get(suffix, "application/octet-stream")
    if content_type not in ALLOWED_LOGO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported logo content type: {file.content_type or 'unknown'}",
        )

    contents = await file.read()
    if len(contents) > MAX_LOGO_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo exceeds 5 MB limit")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(contents).hexdigest()
    storage_path = UPLOAD_DIR / f"{digest}{suffix}"
    storage_path.write_bytes(contents)

    for active_asset in db.execute(
        select(BrandingAsset).where(BrandingAsset.asset_type == "LOGO", BrandingAsset.is_active == true())
    ).scalars():
        active_asset.is_active = False
        db.add(active_asset)

    asset = BrandingAsset(
        asset_type="LOGO",
        original_filename=file.filename or storage_path.name,
        storage_path=str(storage_path),
        content_type=content_type,
        file_size_bytes=len(contents),
        file_sha256=digest,
        is_active=True,
        uploaded_by_user_id=current_user.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    await write_audit_log(
        db,
        action="BRANDING_LOGO_UPLOADED",
        entity_type="BRANDING_ASSET",
        entity_id=asset.id,
        actor_user_id=current_user.id,
        after_data=_asset_payload(asset),
        commit=True,
    )
    return _asset_payload(asset)


@router.post("", response_model=BrandingAssetRead, status_code=status.HTTP_201_CREATED)
async def create_branding_asset(
    payload: BrandingAssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> BrandingAsset:
    if payload.content_type not in ALLOWED_LOGO_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported logo content type")
    if payload.file_size_bytes > MAX_LOGO_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo exceeds 5 MB limit")
    if payload.uploaded_by_user_id is None:
        payload = payload.model_copy(update={"uploaded_by_user_id": current_user.id})
    asset = BrandingAsset(**payload.model_dump(), created_at=datetime.now(timezone.utc))
    db.add(asset)
    db.commit()
    db.refresh(asset)
    await write_audit_log(
        db,
        action="CREATE",
        entity_type="BRANDING_ASSET",
        entity_id=asset.id,
        actor_user_id=current_user.id,
        after_data=BrandingAssetRead.model_validate(asset).model_dump(mode="json"),
        commit=True,
    )
    return asset


@router.patch("/{asset_id}", response_model=BrandingAssetRead)
async def update_branding_asset(
    asset_id: UUID,
    payload: BrandingAssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> BrandingAsset:
    asset = await service.get(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branding asset not found")
    before = BrandingAssetRead.model_validate(asset).model_dump(mode="json")
    if payload.is_active:
        for active_asset in db.execute(
            select(BrandingAsset).where(BrandingAsset.asset_type == asset.asset_type, BrandingAsset.is_active == true())
        ).scalars():
            active_asset.is_active = False
            db.add(active_asset)
    asset = await service.update(db, asset, payload)
    await write_audit_log(
        db,
        action="UPDATE",
        entity_type="BRANDING_ASSET",
        entity_id=asset.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=BrandingAssetRead.model_validate(asset).model_dump(mode="json"),
        commit=True,
    )
    return asset
