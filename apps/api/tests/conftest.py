"""Shared test fixtures.

Each test gets an isolated in-memory SQLite database (shared across sessions
within the test via a StaticPool single connection). The app's `get_session`
dependency is overridden to use this database, and the rate limiter is reset
so limits don't bleed between tests.

`client` is a ready-to-use client; `client_factory` mints additional clients
bound to the SAME app and database (each with its own cookie jar), which is
how cross-workspace isolation tests get two independent authenticated users.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Ensure every model is registered on Base.metadata before create_all.
import stackup_api.models  # noqa: F401
from stackup_api.core.db import Base, get_session
from stackup_api.core.ratelimit import reset_rate_limits
from stackup_api.main import create_app


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.fixture
async def client_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[Callable[[], _ClientCM]]:
    reset_rate_limits()
    app = create_app()

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    def make() -> _ClientCM:
        return _ClientCM(app)

    yield make


class _ClientCM:
    def __init__(self, app: object) -> None:
        self._app = app
        self._client: AsyncClient | None = None

    async def __aenter__(self) -> AsyncClient:
        transport = ASGITransport(app=self._app)
        self._client = AsyncClient(transport=transport, base_url="http://test")
        return self._client

    async def __aexit__(self, *exc: object) -> None:
        assert self._client is not None
        await self._client.aclose()


@pytest.fixture
async def client(
    client_factory: Callable[[], _ClientCM],
) -> AsyncIterator[AsyncClient]:
    async with client_factory() as ac:
        yield ac


@asynccontextmanager
async def authed_client(
    client_factory: Callable[[], _ClientCM],
    email: str,
    password: str = "Sup3rSecret!",
) -> AsyncIterator[AsyncClient]:
    """Yield a new client already registered and logged in as `email`."""
    async with client_factory() as ac:
        resp = await ac.post(
            "/api/v1/auth/register", json={"email": email, "password": password}
        )
        assert resp.status_code == 201, resp.text
        resp = await ac.post(
            "/api/v1/auth/login", data={"username": email, "password": password}
        )
        assert resp.status_code == 204, resp.text
        yield ac
