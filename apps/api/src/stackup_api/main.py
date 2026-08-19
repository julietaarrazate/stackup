"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from stackup_api import __version__
from stackup_api.api.health import router as health_router
from stackup_api.api.v1.router import api_router
from stackup_api.core.config import get_settings
from stackup_api.core.logging import configure_logging, get_logger
from stackup_api.core.middleware import request_id_middleware
from stackup_api.core.observability import init_sentry


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(debug=settings.debug)
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

    app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(api_router)
    return app


app = create_app()
