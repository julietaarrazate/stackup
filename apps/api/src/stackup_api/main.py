"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware

from stackup_api import __version__
from stackup_api.api.health import router as health_router
from stackup_api.api.v1.applications import router as applications_router
from stackup_api.api.v1.router import api_router
from stackup_api.api.v1.vendors import router as vendors_router
from stackup_api.api.v1.workspaces import router as workspaces_router
from stackup_api.core.config import get_settings
from stackup_api.core.logging import configure_logging, get_logger
from stackup_api.core.middleware import request_id_middleware
from stackup_api.core.observability import init_sentry
from stackup_api.core.ratelimit import RateLimiter
from stackup_api.core.users import auth_backend, fastapi_users
from stackup_api.schemas.user import UserCreate, UserRead, UserUpdate


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(debug=settings.debug)
    settings.validate_for_runtime()
    init_sentry(settings)
    get_logger(__name__).info(
        "api.startup",
        environment=settings.environment,
        version=__version__,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="STACKUP API",
        version=__version__,
        lifespan=lifespan,
    )

    @app.exception_handler(IntegrityError)
    async def _integrity_error_handler(
        _request: Request, _exc: IntegrityError
    ) -> JSONResponse:
        # Uniqueness / FK / constraint violations become a clean 409 without
        # leaking the underlying SQL or schema details.
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "The request conflicts with an existing resource "
                "or a data integrity constraint."
            },
        )

    app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health / readiness
    app.include_router(health_router)

    # --- Auth (fastapi-users) ---
    login_limiter = RateLimiter(limit=10, window_seconds=60)
    register_limiter = RateLimiter(limit=5, window_seconds=60 * 60)
    reset_limiter = RateLimiter(limit=5, window_seconds=60 * 60)

    app.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix="/api/v1/auth",
        tags=["auth"],
        dependencies=[Depends(login_limiter)],
    )
    app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix="/api/v1/auth",
        tags=["auth"],
        dependencies=[Depends(register_limiter)],
    )
    app.include_router(
        fastapi_users.get_reset_password_router(),
        prefix="/api/v1/auth",
        tags=["auth"],
        dependencies=[Depends(reset_limiter)],
    )
    app.include_router(
        fastapi_users.get_verify_router(UserRead),
        prefix="/api/v1/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
        prefix="/api/v1/users",
        tags=["users"],
    )

    # --- Domain API ---
    app.include_router(api_router)  # /api/v1/meta
    app.include_router(workspaces_router, prefix="/api/v1")
    app.include_router(applications_router, prefix="/api/v1")
    app.include_router(vendors_router, prefix="/api/v1")

    return app


app = create_app()
