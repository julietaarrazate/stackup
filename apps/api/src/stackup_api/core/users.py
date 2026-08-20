"""fastapi-users wiring: user manager, DB adapters, cookie+DB auth backend.

Sessions are stored in the database (DatabaseStrategy over the access_token
table) so logout/revocation take effect immediately (ADR-003). The session
cookie is HttpOnly, Secure in every non-local environment, and SameSite=Lax.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.authentication.strategy.db import (
    AccessTokenDatabase,
    DatabaseStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from stackup_api.core.config import get_settings
from stackup_api.core.db import get_session
from stackup_api.core.logging import get_logger
from stackup_api.models.access_token import AccessToken
from stackup_api.models.user import User

logger = get_logger(__name__)


async def get_user_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[SQLAlchemyUserDatabase[User, uuid.UUID]]:
    yield SQLAlchemyUserDatabase(session, User)


async def get_access_token_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncIterator[AccessTokenDatabase[AccessToken]]:
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    @property
    def reset_password_token_secret(self) -> str:  # type: ignore[override]
        return get_settings().auth_secret

    @property
    def verification_token_secret(self) -> str:  # type: ignore[override]
        return get_settings().auth_secret

    async def on_after_register(
        self, user: User, request: object | None = None
    ) -> None:
        logger.info("auth.user_registered", user_id=str(user.id))

    async def on_after_forgot_password(
        self, user: User, token: str, request: object | None = None
    ) -> None:
        from stackup_api.services.email import password_reset_email, send_email

        logger.info("auth.forgot_password", user_id=str(user.id))
        subject, html = password_reset_email(token)
        await send_email(to=user.email, subject=subject, html=html)

    async def on_after_request_verify(
        self, user: User, token: str, request: object | None = None
    ) -> None:
        from stackup_api.services.email import send_email, verify_email

        logger.info("auth.request_verify", user_id=str(user.id))
        subject, html = verify_email(token)
        await send_email(to=user.email, subject=subject, html=html)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = Depends(get_user_db),
) -> AsyncIterator[UserManager]:
    yield UserManager(user_db)


def _cookie_transport() -> CookieTransport:
    settings = get_settings()
    return CookieTransport(
        cookie_name=settings.session_cookie_name,
        cookie_max_age=settings.session_lifetime_seconds,
        cookie_secure=settings.cookie_secure,
        cookie_httponly=True,
        cookie_samesite="lax",
        cookie_domain=settings.cookie_domain,
    )


def get_database_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
) -> DatabaseStrategy[User, uuid.UUID, AccessToken]:
    return DatabaseStrategy(
        access_token_db,
        lifetime_seconds=get_settings().session_lifetime_seconds,
    )


auth_backend = AuthenticationBackend(
    name="cookie-db",
    transport=_cookie_transport(),
    get_strategy=get_database_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Common dependencies used by routers.
current_active_user = fastapi_users.current_user(active=True)
