"""Application configuration, loaded from environment variables.

No secret ever has a real default here; production must set them explicitly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Runtime ---
    environment: Environment = "development"
    debug: bool = False

    # --- Database ---
    # Async SQLAlchemy URL, e.g.
    # postgresql+asyncpg://user:pass@host/db  (Neon in every real environment).
    # Defaults to a local aiosqlite file only so the app and tests can boot
    # without external infra; production MUST override this with Neon.
    database_url: str = "sqlite+aiosqlite:///./stackup_dev.db"

    # --- CORS: the single first-party origin (the Next.js BFF) ---
    frontend_origin: str = "http://localhost:3000"

    # --- Observability ---
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)

    # --- Uploads (Phase 6) ---
    max_upload_size_mb: int = Field(default=10, gt=0)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_origin]


@lru_cache
def get_settings() -> Settings:
    return Settings()
