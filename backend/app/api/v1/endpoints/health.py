from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter()

CRITICAL_TABLES = [
    "users",
    "organizations",
    "contacts",
    "notes",
    "organization_borusan_fit",
    "opportunities",
    "opportunity_documents",
    "use_case_proposals",
    "events",
    "program_activities",
    "program_activity_participants",
    "follow_up_actions",
    "import_batches",
    "import_candidates",
    "user_contributions",
    "champion_activities",
    "organization_documents",
    "audit_logs",
    "notifications",
    "crm_activity_events",
]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="borusan-ai-studio-crm-api")


@router.get("/health/readiness", response_model=ReadinessResponse)
async def readiness_check(db: Session = Depends(get_db)) -> ReadinessResponse:
    checks: dict[str, str] = {"config": "ok"}
    migration_version: str | None = None
    database_status = "ok"

    try:
        db.execute(text("SELECT 1"))
        version_result = db.execute(text("SELECT version_num FROM alembic_version"))
        migration_version = version_result.scalar_one_or_none()
        checks["database_connectivity"] = "ok"
        checks["alembic_version"] = migration_version or "missing"
        if migration_version is None:
            database_status = "degraded"
        table_rows = db.execute(
            text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        ).scalars().all()
        existing_tables = {str(table_name) for table_name in table_rows}
        missing_tables = [table_name for table_name in CRITICAL_TABLES if table_name not in existing_tables]
        checks["critical_tables"] = "ok" if not missing_tables else f"missing: {', '.join(missing_tables)}"
        if missing_tables:
            database_status = "degraded"
        if "organizations" in existing_tables:
            checks["organizations_count"] = str(db.execute(text("SELECT COUNT(*) FROM organizations")).scalar_one())
        if "users" in existing_tables:
            checks["users_count"] = str(db.execute(text("SELECT COUNT(*) FROM users")).scalar_one())
    except SQLAlchemyError as exc:
        database_status = "error"
        checks["database_connectivity"] = f"error: {exc.__class__.__name__}"

    return ReadinessResponse(
        status="ok" if database_status == "ok" else "degraded",
        service=settings.app_name,
        database=database_status,
        migration_version=migration_version,
        checks=checks,
    )


@router.get("/health/routes")
async def route_diagnostics(request: Request) -> dict[str, object]:
    required_paths = ["/api/v1/use-cases", "/api/v1/program-activities"]
    registered_paths = sorted({getattr(route, "path", "") for route in request.app.routes})
    return {
        "status": "ok" if all(path in registered_paths for path in required_paths) else "degraded",
        "required": {path: path in registered_paths for path in required_paths},
        "matches": [path for path in registered_paths if "use-cases" in path or "program-activities" in path],
    }
