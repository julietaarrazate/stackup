"""Async database engine, session factory, and the declarative base.

Enforces ADR-002: PostgreSQL (Neon) is the only permitted datastore in
staging/production. A SQLite URL is tolerated only for local development and
tests so the app can boot without external infra; it is rejected outright in
staging/production to prevent an accidental non-durable datastore.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from stackup_api.core.config import Settings, get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _validate_datastore(settings: Settings) -> None:
    is_deployed = settings.environment in ("staging", "production")
    if is_deployed and settings.database_url.startswith("sqlite"):
        raise RuntimeError(
            "SQLite is not a permitted datastore in staging/production "
            "(ADR-002). Set DATABASE_URL to the Neon PostgreSQL connection "
            "string."
        )


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    settings = settings or get_settings()
    _validate_datastore(settings)
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        future=True,
    )


engine: AsyncEngine = create_engine()
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a database session."""
    async with SessionLocal() as session:
        yield session
