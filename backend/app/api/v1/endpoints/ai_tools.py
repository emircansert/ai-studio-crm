from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import AITool, User
from app.schemas import AIToolCreate, AIToolRead, AIToolUpdate, ArchiveRequest
from app.services.archive import archive_record, unarchive_record
from app.services.audit import write_audit_log
from app.services.champion_score import write_champion_activity
from app.services.contributions import write_user_contribution
from app.services.crud import CRUDService
from app.services.soft_delete import not_archived

router = APIRouter(prefix="/ai-tools", tags=["ai-tools"])
service = CRUDService[AITool, AIToolCreate, AIToolUpdate](AITool)


@router.get("", response_model=list[AIToolRead])
async def list_ai_tools(
    q: str | None = None,
    category: str | None = None,
    category_text: str | None = None,
    vendor: str | None = None,
    use_case: str | None = None,
    pricing_model: str | None = None,
    deployment_type: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    vendor_organization_id: UUID | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AITool]:
    stmt = select(AITool)
    if not (include_archived and current_user.role == "ADMIN"):
        stmt = stmt.where(not_archived(AITool.is_archived))
    if category or category_text:
        stmt = stmt.where(AITool.category_text == (category or category_text))
    if vendor:
        stmt = stmt.where(AITool.vendor_name.ilike(f"%{vendor}%"))
    if use_case:
        pattern = f"%{use_case}%"
        stmt = stmt.where(or_(AITool.primary_use_case.ilike(pattern), AITool.solution_summary.ilike(pattern)))
    if pricing_model:
        stmt = stmt.where(AITool.pricing_model == pricing_model)
    if deployment_type:
        stmt = stmt.where(AITool.deployment_type == deployment_type)
    if status_filter:
        stmt = stmt.where(AITool.status == status_filter)
    if vendor_organization_id:
        stmt = stmt.where(AITool.vendor_organization_id == vendor_organization_id)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                AITool.name.ilike(pattern),
                AITool.vendor_name.ilike(pattern),
                AITool.website_url.ilike(pattern),
                AITool.category_text.ilike(pattern),
                AITool.primary_use_case.ilike(pattern),
                AITool.description.ilike(pattern),
                AITool.solution_summary.ilike(pattern),
                AITool.owner_notes.ilike(pattern),
                AITool.notes.ilike(pattern),
            )
        )
    rows = db.execute(stmt.order_by(AITool.updated_at.desc(), AITool.name.asc(), AITool.id.asc()).offset(skip).limit(limit))
    return list(rows.scalars().all())


@router.get("/{tool_id}", response_model=AIToolRead)
async def get_ai_tool(
    tool_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AITool:
    tool = await service.get(db, tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI tool not found")
    return tool


@router.post("", response_model=AIToolRead, status_code=status.HTTP_201_CREATED)
async def create_ai_tool(
    payload: AIToolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AITool:
    data = payload.model_dump(exclude_unset=True)
    data["added_by_user_id"] = current_user.id
    data["updated_by_user_id"] = current_user.id
    data["source"] = data.get("source") or "MANUAL"
    tool = AITool(**data)
    db.add(tool)
    db.commit()
    db.refresh(tool)
    await write_audit_log(
        db,
        action="AI_TOOL_CREATED",
        entity_type="AI_TOOL",
        entity_id=tool.id,
        actor_user_id=current_user.id,
        after_data=AIToolRead.model_validate(tool).model_dump(mode="json"),
        commit=True,
    )
    await write_user_contribution(
        db,
        user_id=current_user.id,
        contribution_type="AI_TOOL_CREATED",
        entity_type="AI_TOOL",
        entity_id=tool.id,
        metadata_json={"name": tool.name, "category": tool.category_text, "vendor_name": tool.vendor_name},
        commit=True,
    )
    await write_champion_activity(
        db,
        user_id=current_user.id,
        category="ECOSYSTEM_LIBRARY",
        activity_type="AI_TOOL_ADDED",
        related_entity_type="AI_TOOL",
        related_entity_id=tool.id,
        notes=tool.name,
        created_by_user_id=current_user.id,
        commit=True,
    )
    return tool


@router.put("/{tool_id}", response_model=AIToolRead)
async def put_ai_tool(
    tool_id: UUID,
    payload: AIToolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AITool:
    return await update_ai_tool(tool_id, payload, db, current_user)


@router.patch("/{tool_id}", response_model=AIToolRead)
async def update_ai_tool(
    tool_id: UUID,
    payload: AIToolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AITool:
    tool = await service.get(db, tool_id)
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI tool not found")
    before = AIToolRead.model_validate(tool).model_dump(mode="json")
    data = payload.model_dump(exclude_unset=True)
    data["updated_by_user_id"] = current_user.id
    for field_name, value in data.items():
        setattr(tool, field_name, value)
    db.add(tool)
    db.commit()
    db.refresh(tool)
    await write_audit_log(
        db,
        action="AI_TOOL_UPDATED",
        entity_type="AI_TOOL",
        entity_id=tool.id,
        actor_user_id=current_user.id,
        before_data=before,
        after_data=AIToolRead.model_validate(tool).model_dump(mode="json"),
        commit=True,
    )
    return tool


@router.patch("/{tool_id}/archive", response_model=AIToolRead)
async def archive_ai_tool(
    tool_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AITool:
    return await archive_record(
        db,
        await service.get(db, tool_id),
        entity_type="AI_TOOL",
        entity_id=tool_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )


@router.patch("/{tool_id}/unarchive", response_model=AIToolRead)
async def unarchive_ai_tool(
    tool_id: UUID,
    payload: ArchiveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AITool:
    return await unarchive_record(
        db,
        await service.get(db, tool_id),
        entity_type="AI_TOOL",
        entity_id=tool_id,
        actor=current_user,
        reason=payload.reason if payload else None,
    )
