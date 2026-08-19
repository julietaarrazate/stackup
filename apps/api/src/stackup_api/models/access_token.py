"""Access-token table backing revocable, database-stored sessions (ADR-003)."""

from __future__ import annotations

# Import the top-level adapter package fully before its `access_token`
# submodule to avoid a circular-import edge in fastapi-users where importing
# the submodule first leaves `fastapi_users.db` half-initialized.
import fastapi_users.db  # noqa: F401
from fastapi_users_db_sqlalchemy.access_token import (
    SQLAlchemyBaseAccessTokenTableUUID,
)

from stackup_api.core.db import Base


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    """Server-side session token.

    Because sessions live in the database (not a self-contained JWT), logging
    out or revoking a session deletes the row and immediately invalidates it.
    """

    __tablename__ = "access_token"
