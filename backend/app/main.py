import logging
import time
import traceback
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.identity import IdentityError, resolve_user_from_token
from app.core.section_access import (
    access_allows,
    match_section_for_path,
    required_access_for_method,
    resolve_user_section_access,
)
from app.db.session import SessionLocal

logger = logging.getLogger("borusan_crm.api")


def _error_payload(
    *,
    error_code: str,
    message: str,
    request_id: str | None = None,
    details: object | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {"error_code": error_code, "message": message}
    if details is not None:
        payload["details"] = details
    if request_id:
        payload["request_id"] = request_id
    return payload


def create_app() -> FastAPI:
    # API docs (Swagger / ReDoc / OpenAPI JSON) are exposed only in explicit
    # development environments. Fail closed: a missing or unrecognised
    # ENVIRONMENT value disables them entirely (the routes return 404).
    docs_enabled = settings.is_development
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Foundation API for the Borusan AI Studio CRM.",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001 - central defensive logging.
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.error(
                "Unhandled request error request_id=%s method=%s path=%s duration_ms=%s exc_type=%s exc=%s\n%s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                exc.__class__.__name__,
                exc,
                traceback.format_exc(),
            )
            return JSONResponse(
                status_code=500,
                content=_error_payload(
                    error_code="INTERNAL_SERVER_ERROR",
                    message="An unexpected server error occurred.",
                    request_id=request_id,
                ),
                headers={"x-request-id": request_id},
            )
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers["x-request-id"] = request_id
        logger.info(
            "request request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.middleware("http")
    async def section_access_middleware(request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        section = match_section_for_path(request.url.path)
        if section is None:
            return await call_next(request)

        request_id = getattr(request.state, "request_id", request.headers.get("x-request-id"))
        auth_header = request.headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content=_error_payload(
                    error_code="NOT_AUTHENTICATED",
                    message="Authentication is required for this section.",
                    request_id=request_id,
                ),
            )

        token = auth_header.split(" ", 1)[1].strip()
        with SessionLocal() as db:
            try:
                # Shared resolver: identical identity semantics to get_current_user
                # in both local and Entra auth modes.
                user = resolve_user_from_token(db, token)
            except IdentityError as exc:
                return JSONResponse(
                    status_code=401,
                    content=_error_payload(
                        error_code=exc.error_code,
                        message=exc.message,
                        request_id=request_id,
                    ),
                )
            access_level = resolve_user_section_access(db, user, section.key)

        # Hand the already-validated user to get_current_user so it does not
        # re-query for the same identity on this request (see app.api.deps).
        request.state.section_user = user
        request.state.section_user_token = token

        required_level = required_access_for_method(request.method)
        if not access_allows(access_level, required_level):
            message = (
                f"{section.label} requires full access for this action."
                if required_level == "FULL"
                else f"{section.label} is hidden for this user."
            )
            return JSONResponse(
                status_code=403,
                content=_error_payload(
                    error_code="SECTION_ACCESS_DENIED",
                    message=message,
                    request_id=request_id,
                    details={
                        "section_key": section.key,
                        "section_label": section.label,
                        "access_level": access_level,
                        "required_level": required_level,
                    },
                ),
            )

        return await call_next(request)

    @app.exception_handler(HTTPException)
    async def fastapi_http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", request.headers.get("x-request-id"))
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed."
        details = detail if not isinstance(detail, str) else None
        headers = dict(exc.headers or {})
        if request_id:
            headers["x-request-id"] = request_id
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                error_code=f"HTTP_{exc.status_code}",
                message=message,
                request_id=request_id,
                details=details,
            ),
            headers=headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", request.headers.get("x-request-id"))
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                error_code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                request_id=request_id,
            ),
            headers={"x-request-id": request_id} if request_id else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", request.headers.get("x-request-id"))
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                error_code="VALIDATION_ERROR",
                message="Request validation failed.",
                request_id=request_id,
                details=exc.errors(),
            ),
            headers={"x-request-id": request_id} if request_id else None,
        )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
