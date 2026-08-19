"""Config and datastore-guard tests (ADR-002)."""

from __future__ import annotations

import pytest

from stackup_api.core.config import Settings
from stackup_api.core.db import _validate_datastore


def test_sqlite_rejected_in_production() -> None:
    settings = Settings(
        environment="production",
        database_url="sqlite+aiosqlite:///./x.db",
    )
    with pytest.raises(RuntimeError, match="ADR-002"):
        _validate_datastore(settings)


def test_sqlite_allowed_in_development() -> None:
    settings = Settings(
        environment="development",
        database_url="sqlite+aiosqlite:///./x.db",
    )
    # Should not raise.
    _validate_datastore(settings)


def test_postgres_allowed_in_production() -> None:
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://u:p@host/db",
    )
    _validate_datastore(settings)


def test_cors_origins_is_frontend_origin() -> None:
    settings = Settings(frontend_origin="https://app.stackup.ar")
    assert settings.cors_origins == ["https://app.stackup.ar"]
