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

    # --- Authentication (ADR-003) ---
    # Signs email-verification and password-reset tokens. MUST be overridden
    # in production; the dev default is rejected at startup when deployed.
    auth_secret: str = "dev-insecure-change-me"
    # Session lifetime for the database-backed, revocable session token.
    session_lifetime_seconds: int = Field(default=60 * 60 * 24 * 7, gt=0)  # 7 days
    session_cookie_name: str = "stackup_session"
    # Parent domain for the session cookie (e.g. ".stackup.ar") so it is valid
    # across app/api subdomains. None -> host-only cookie (local dev).
    cookie_domain: str | None = None

    # Public base URL of the frontend, used to build links in emails
    # (password reset, verification). Defaults to the CORS origin.
    frontend_base_url: str | None = None

    # --- Email (Resend) ---
    # When RESEND_API_KEY is set, transactional emails are sent via Resend;
    # otherwise they are logged (dev/test).
    resend_api_key: str | None = None
    email_from: str = "STACKUP <onboarding@resend.dev>"

    # --- Background jobs (Phase 7, ADR-005) ---
    # Upstash Redis URL for the arq queue. When unset, jobs run inline.
    redis_url: str | None = None

    # --- GitHub integration (Phase 8) ---
    # An OAuth App (not a GitHub App) with the "repo" scope for read access
    # to manifest files. When unset, the /integrations/github routes are
    # disabled (404) rather than erroring on every call.
    github_client_id: str | None = None
    github_client_secret: str | None = None

    @property
    def github_configured(self) -> bool:
        return bool(self.github_client_id and self.github_client_secret)

    @property
    def github_redirect_uri(self) -> str:
        return f"{self.frontend_link_base}/api/auth/github/callback"

    # --- Observability ---
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)

    # --- Uploads / storage (Phase 6, ADR-006) ---
    max_upload_size_mb: int = Field(default=10, gt=0)
    # Cloudflare R2 (S3-compatible). When all are set, the R2 backend is used;
    # otherwise an in-process backend is used (dev/test only). Evidence is
    # never stored on Render's ephemeral filesystem.
    storage_endpoint: str | None = None
    storage_bucket: str | None = None
    storage_access_key: str | None = None
    storage_secret_key: str | None = None
    storage_region: str = "auto"

    @property
    def storage_configured(self) -> bool:
        return all(
            (
                self.storage_endpoint,
                self.storage_bucket,
                self.storage_access_key,
                self.storage_secret_key,
            )
        )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cookie_secure(self) -> bool:
        # Secure cookies everywhere except plain-HTTP local development.
        return self.environment != "development"

    def validate_for_runtime(self) -> None:
        """Fail fast on unsafe production configuration."""
        if self.environment in ("staging", "production"):
            if self.database_url.startswith("sqlite"):
                raise RuntimeError(
                    "SQLite is not permitted in staging/production (ADR-002)."
                )
            if self.auth_secret == "dev-insecure-change-me":
                raise RuntimeError(
                    "AUTH_SECRET must be set to a strong secret in staging/production."
                )
            if self.environment == "production" and not self.storage_configured:
                raise RuntimeError(
                    "Object storage (R2) must be configured in production; "
                    "the in-process backend is dev/test only (ADR-006)."
                )

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_origin]

    @property
    def frontend_link_base(self) -> str:
        return (self.frontend_base_url or self.frontend_origin).rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
