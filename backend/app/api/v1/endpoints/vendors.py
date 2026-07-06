from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import User, Vendor, VendorRating
from app.schemas import ArchiveRequest, VendorCreate, VendorRatingUpsert, VendorRead, VendorUpdate
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.champion_score import write_champion_activity
from app.services.contributions import write_user_contribution
from app.services.crud import CRUDService
from app.services.soft_delete import not_archived

router = APIRouter(prefix="/vendors", tags=["vendors"])
service = CRUDService[Vendor, VendorCreate, VendorUpdate](Vendor)

# Weighted rating categories. Weights are percentages and must total 100.
RATING_WEIGHTS: dict[str, float] = {
    "quality_score": 0.35,
    "reliability_score": 0.25,
    "pricing_score": 0.20,
    "borusan_fit_score": 0.20,
}

VENDOR_STATUSES = ["PROSPECT", "EVALUATING", "ACTIVE", "ON_HOLD", "DISCONTINUED"]


def weighted_score(quality: int, reliability: int, pricing: int, borusan_fit: int) -> float:
    return (
        quality * RATING_WEIGHTS["quality_score"]
        + reliability * RATING_WEIGHTS["reliability_score"]
        + pricing * RATING_WEIGHTS["pricing_score"]
        + borusan_fit * RATING_WEIGHTS["borusan_fit_score"]
    )


def _weighted_sql_expression() -> Any:
    return (
        VendorRating.quality_score * RATING_WEIGHTS["quality_score"]
        + VendorRating.reliability_score * RATING_WEIGHTS["reliability_score"]
        + VendorRating.pricing_score * RATING_WEIGHTS["pricing_score"]
        + VendorRating.borusan_fit_score * RATING_WEIGHTS["borusan_fit_score"]
    )


def _rating_summaries(db: Session, vendor_ids: list[UUID]) -> dict[UUID, dict[str, Any]]:
    if not vendor_ids:
        return {}
    rows = db.execute(
        select(
            VendorRating.vendor_id,
            func.count(VendorRating.id),
            func.avg(_weighted_sql_expression()),
            func.avg(VendorRating.quality_score),
            func.avg(VendorRating.reliability_score),
            func.avg(VendorRating.pricing_score),
            func.avg(VendorRating.borusan_fit_score),
        )
        .where(VendorRating.vendor_id.in_(vendor_ids))
        .group_by(VendorRating.vendor_id)
    ).all()
    return {
        vendor_id: {
            "rating_count": int(count),
            "overall_score": round(float(overall), 2) if overall is not None else None,
            "category_averages": {
                "quality_score": round(float(quality), 2) if quality is not None else None,
                "reliability_score": round(float(reliability), 2) if reliability is not None else None,
                "pricing_score": round(float(pricing), 2) if pricing is not None else None,
                "borusan_fit_score": round(float(borusan_fit), 2) if borusan_fit is not None else None,
            },
        }
        for vendor_id, count, overall, quality, reliability, pricing, borusan_fit in rows
    }


def _empty_summary() -> dict[str, Any]:
    return {
        "rating_count": 0,
        "overall_score": None,
        "category_averages": {
            "quality_score": None,
            "reliability_score": None,
            "pricing_score": None,
            "borusan_fit_score": None,
        },
    }


def _user_payload(db: Session, user_id: UUID | None) -> dict[str, Any] | None:
    if not user_id:
        return None
    user = db.get(User, user_id)
    if user is None:
        return {"id": user_id, "full_name": None, "email": None}
    return {"id": user.id, "full_name": user.full_name, "email": user.email}


def _rating_payload(db: Session, rating: VendorRating) -> dict[str, Any]:
    return {
        "id": rating.id,
        "vendor_id": rating.vendor_id,
        "rater": _user_payload(db, rating.rater_user_id),
        "quality_score": rating.quality_score,
        "reliability_score": rating.reliability_score,
        "pricing_score": rating.pricing_score,
        "borusan_fit_score": rating.borusan_fit_score,
        "weighted_score": round(
            weighted_score(
                rating.quality_score,
                rating.reliability_score,
                rating.pricing_score,
                rating.borusan_fit_score,
            ),
            2,
        ),
        "comment": rating.comment,
        "created_at": rating.created_at,
        "updated_at": rating.updated_at,
    }


def _rating_audit_payload(rating: VendorRating) -> dict[str, Any]:
    """JSON-safe snapshot of a rating for the audit log (no UUID/datetime objects)."""
    return {
        "id": str(rating.id),
        "vendor_id": str(rating.vendor_id),
        "rater_user_id": str(rating.rater_user_id),
        "quality_score": rating.quality_score,
        "reliability_score": rating.reliability_score,
        "pricing_score": rating.pricing_score,
        "borusan_fit_score": rating.borusan_fit_score,
        "weighted_score": round(
            weighted_score(
                rating.quality_score,
                rating.reliability_score,
                rating.pricing_score,
                rating.borusan_fit_score,
            ),
            2,
        ),
        "comment": rating.comment,
    }


def _vendor_payload(db: Session, vendor: Vendor, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    created_by = _user_payload(db, vendor.created_by_user_id)
    return {
        "id": vendor.id,
        "name": vendor.name,
        "category_text": vendor.category_text,
        "description": vendor.description,
        "contact_info": vendor.contact_info,
        "website_url": vendor.website_url,
        "status": vendor.status,
        "geography_text": vendor.geography_text,
        "last_contact_date": vendor.last_contact_date,
        "created_by_user_id": vendor.created_by_user_id,
        "created_by_user": created_by,
        "added_by_display": created_by["full_name"] if created_by else None,
        "added_at": vendor.created_at,
        "is_archived": vendor.is_archived,
        "archived_at": vendor.archived_at,
        "archive_reason": vendor.archive_reason,
        "created_at": vendor.created_at,
        "updated_at": vendor.updated_at,
        "rating_summary": summary or _empty_summary(),
        "rating_weights": RATING_WEIGHTS,
    }


def _get_vendor_or_404(db: Session, vendor_id: UUID) -> Vendor:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return vendor


def _ordered(stmt: Any, sort_by: str, score_expr: Any) -> Any:
    if sort_by == "oldest":
        return stmt.order_by(Vendor.created_at.asc(), Vendor.id.asc())
    if sort_by == "name_asc":
        return stmt.order_by(Vendor.name.asc(), Vendor.id.asc())
    if sort_by == "last_contact_desc":
        return stmt.order_by(Vendor.last_contact_date.desc(), Vendor.created_at.desc(), Vendor.id.desc())
    if sort_by == "last_contact_asc":
        return stmt.order_by(
            case((Vendor.last_contact_date.is_(None), 1), else_=0).asc(),
            Vendor.last_contact_date.asc(),
            Vendor.created_at.asc(),
            Vendor.id.asc(),
        )
    if sort_by == "score_desc":
        # SQL Server sorts NULLs last in DESC, so unrated vendors sink naturally.
        return stmt.order_by(score_expr.desc(), Vendor.created_at.desc(), Vendor.id.desc())
    if sort_by == "score_asc":
        return stmt.order_by(
            case((score_expr.is_(None), 1), else_=0).asc(),
            score_expr.asc(),
            Vendor.created_at.asc(),
            Vendor.id.asc(),
        )
    return stmt.order_by(Vendor.created_at.desc(), Vendor.id.desc())


@router.get("/statuses")
async def vendor_statuses(_: User = Depends(get_current_user)) -> list[str]:
    return VENDOR_STATUSES


@router.get("")
async def list_vendors(
    q: str | None = None,
    category: str | None = None,
    vendor_status: str | None = Query(default=None, alias="status"),
    geography: str | None = None,
    added_from_date: date | None = None,
    added_to_date: date | None = None,
    include_archived: bool = False,
    sort_by: str = Query(
        default="newest",
        pattern="^(newest|oldest|name_asc|score_desc|score_asc|last_contact_desc|last_contact_asc)$",
    ),
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    score_subquery = (
        select(
            VendorRating.vendor_id.label("vendor_id"),
            func.avg(_weighted_sql_expression()).label("overall_score"),
        )
        .group_by(VendorRating.vendor_id)
        .subquery()
    )
    score_expr = score_subquery.c.overall_score

    stmt = select(Vendor).outerjoin(score_subquery, score_subquery.c.vendor_id == Vendor.id)
    if not include_archived or current_user.role != "ADMIN":
        stmt = stmt.where(not_archived(Vendor.is_archived))
    if category:
        stmt = stmt.where(Vendor.category_text.ilike(f"%{category}%"))
    if vendor_status:
        stmt = stmt.where(Vendor.status == vendor_status)
    if geography:
        stmt = stmt.where(Vendor.geography_text.ilike(f"%{geography}%"))
    if added_from_date:
        stmt = stmt.where(Vendor.created_at >= datetime.combine(added_from_date, time.min))
    if added_to_date:
        stmt = stmt.where(Vendor.created_at <= datetime.combine(added_to_date, time.max))
    if q:
        q_like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Vendor.name.ilike(q_like),
                Vendor.category_text.ilike(q_like),
                Vendor.description.ilike(q_like),
                Vendor.contact_info.ilike(q_like),
                Vendor.geography_text.ilike(q_like),
                Vendor.website_url.ilike(q_like),
            )
        )

    total_count = int(db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one())
    vendors = db.execute(_ordered(stmt, sort_by, score_expr).offset(skip).limit(limit)).scalars().all()
    summaries = _rating_summaries(db, [vendor.id for vendor in vendors])
    return {
        "items": [_vendor_payload(db, vendor, summaries.get(vendor.id)) for vendor in vendors],
        "total_count": total_count,
        "limit": limit,
        "offset": skip,
        "sort_by": sort_by,
        "statuses": VENDOR_STATUSES,
    }


@router.get("/{vendor_id}")
async def get_vendor(
    vendor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    vendor = _get_vendor_or_404(db, vendor_id)
    if vendor.is_archived and current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    summary = _rating_summaries(db, [vendor.id]).get(vendor.id)
    ratings = db.execute(
        select(VendorRating)
        .where(VendorRating.vendor_id == vendor.id)
        .order_by(VendorRating.updated_at.desc(), VendorRating.id.desc())
    ).scalars().all()
    my_rating = next((rating for rating in ratings if rating.rater_user_id == current_user.id), None)
    return {
        **_vendor_payload(db, vendor, summary),
        "ratings": [_rating_payload(db, rating) for rating in ratings],
        "my_rating": _rating_payload(db, my_rating) if my_rating else None,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_vendor(
    payload: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    if payload.status not in VENDOR_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown vendor status: {payload.status}")
    vendor = Vendor(
        **payload.model_dump(exclude_unset=True),
        created_by_user_id=current_user.id,
        updated_by_user_id=current_user.id,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    read_payload = VendorRead.model_validate(vendor).model_dump(mode="json")
    await write_audit_log(
        db,
        action="VENDOR_CREATED",
        entity_type="VENDOR",
        entity_id=vendor.id,
        actor_user_id=current_user.id,
        after_data=read_payload,
        commit=True,
    )
    await write_user_contribution(
        db,
        user_id=current_user.id,
        contribution_type="VENDOR_CREATED",
        entity_type="VENDOR",
        entity_id=vendor.id,
        metadata_json={"name": vendor.name},
        commit=True,
    )
    await write_champion_activity(
        db,
        user_id=current_user.id,
        category="ECOSYSTEM_LIBRARY",
        activity_type="VENDOR_ADDED",
        related_entity_type="VENDOR",
        related_entity_id=vendor.id,
        notes=f"VENDOR: {vendor.name}",
        created_by_user_id=current_user.id,
        commit=True,
    )
    return _vendor_payload(db, vendor)


@router.patch("/{vendor_id}")
async def update_vendor(
    vendor_id: UUID,
    payload: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    vendor = _get_vendor_or_404(db, vendor_id)
    if payload.status is not None and payload.status not in VENDOR_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown vendor status: {payload.status}")
    before = VendorRead.model_validate(vendor).model_dump(mode="json")
    update_payload = payload.model_copy(update={})
    vendor = await service.update(db, vendor, update_payload)
    vendor.updated_by_user_id = current_user.id
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    await write_audit_log(
        db,
        action="VENDOR_UPDATED",
        entity_type="VENDOR",
        entity_id=vendor.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=VendorRead.model_validate(vendor).model_dump(mode="json"),
        commit=True,
    )
    summary = _rating_summaries(db, [vendor.id]).get(vendor.id)
    return _vendor_payload(db, vendor, summary)


@router.patch("/{vendor_id}/archive")
async def archive_vendor(
    vendor_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    vendor = await archive_record(
        db,
        db.get(Vendor, vendor_id),
        entity_type="VENDOR",
        entity_id=vendor_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _vendor_payload(db, vendor, _rating_summaries(db, [vendor.id]).get(vendor.id))


@router.patch("/{vendor_id}/unarchive")
async def unarchive_vendor(
    vendor_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    vendor = await unarchive_record(
        db,
        db.get(Vendor, vendor_id),
        entity_type="VENDOR",
        entity_id=vendor_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
    return _vendor_payload(db, vendor, _rating_summaries(db, [vendor.id]).get(vendor.id))


@router.put("/{vendor_id}/my-rating")
async def upsert_my_rating(
    vendor_id: UUID,
    payload: VendorRatingUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    vendor = _get_vendor_or_404(db, vendor_id)
    if vendor.is_archived:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archived vendors cannot be rated")
    rating = db.execute(
        select(VendorRating).where(
            VendorRating.vendor_id == vendor.id,
            VendorRating.rater_user_id == current_user.id,
        )
    ).scalar_one_or_none()
    action = "VENDOR_RATING_UPDATED" if rating else "VENDOR_RATING_CREATED"
    before = _rating_audit_payload(rating) if rating else None
    if rating is None:
        rating = VendorRating(vendor_id=vendor.id, rater_user_id=current_user.id)
        db.add(rating)
    rating.quality_score = payload.quality_score
    rating.reliability_score = payload.reliability_score
    rating.pricing_score = payload.pricing_score
    rating.borusan_fit_score = payload.borusan_fit_score
    rating.comment = payload.comment
    db.commit()
    db.refresh(rating)
    await write_audit_log(
        db,
        action=action,
        entity_type="VENDOR_RATING",
        entity_id=rating.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=_rating_audit_payload(rating),
        commit=True,
    )
    summary = _rating_summaries(db, [vendor.id]).get(vendor.id)
    return {
        "my_rating": _rating_payload(db, rating),
        "rating_summary": summary or _empty_summary(),
    }


@router.delete("/{vendor_id}/my-rating")
async def delete_my_rating(
    vendor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    vendor = _get_vendor_or_404(db, vendor_id)
    rating = db.execute(
        select(VendorRating).where(
            VendorRating.vendor_id == vendor.id,
            VendorRating.rater_user_id == current_user.id,
        )
    ).scalar_one_or_none()
    if rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You have not rated this vendor")
    before = _rating_audit_payload(rating)
    rating_id = rating.id
    db.delete(rating)
    db.commit()
    await write_audit_log(
        db,
        action="VENDOR_RATING_DELETED",
        entity_type="VENDOR_RATING",
        entity_id=rating_id,
        actor_user_id=current_user.id,
        before_data=before,
        commit=True,
    )
    summary = _rating_summaries(db, [vendor.id]).get(vendor.id)
    return {
        "my_rating": None,
        "rating_summary": summary or _empty_summary(),
    }
