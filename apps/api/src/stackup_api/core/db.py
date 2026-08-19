"""Async database engine, session factory, and the declarative base.

Enforces ADR-002: PostgreSQL (Neon) is the only permitted datastore in
staging/production. A SQLite URL is tolerated only for local development and
tests so the app can boot without external infra; it is rejected outright in
staging/production to prevent an accidental non-durable datastore.
"""

from __future__ import annotations

import ssl
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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


# libpq/JDBC-style query params that asyncpg (via SQLAlchemy) does not accept
# in the URL — we strip them and handle TLS ourselves so the raw Neon
# connection string works after only swapping the scheme to +asyncpg.
_ASYNCPG_STRIP_PARAMS = {"sslmode", "channel_binding", "ssl", "options"}


def _prepare_asyncpg(url: str) -> tuple[str, dict[str, Any]]:
    """Return (clean_url, connect_args) for an asyncpg Postgres URL.

    - TLS: use a verifying SSL context (Neon presents a valid CA cert), so a
      copy-pasted `?sslmode=require` Neon string works without extra config.
    - statement_cache_size=0: required behind Neon's PgBouncer pooler, which
      does not support server-side prepared statements.
    """
    parts = urlsplit(url)
    query = [
        (k, v) for k, v in parse_qsl(parts.query) if k not in _ASYNCPG_STRIP_PARAMS
    ]
    clean = urlunsplit(parts._replace(query=urlencode(query)))
    connect_args: dict[str, Any] = {"statement_cache_size": 0}
    if not parts.hostname or parts.hostname not in ("localhost", "127.0.0.1"):
        connect_args["ssl"] = ssl.create_default_context()
    return clean, connect_args


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    settings = settings or get_settings()
    _validate_datastore(settings)
    url = settings.database_url
    connect_args: dict[str, Any] = {}
    if url.startswith("postgresql+asyncpg"):
        url, connect_args = _prepare_asyncpg(url)
    return create_async_engine(
        url,
        echo=settings.debug,
        pool_pre_ping=True,
        future=True,
        connect_args=connect_args,
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
