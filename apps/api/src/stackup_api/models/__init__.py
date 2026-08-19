"""SQLAlchemy ORM models.

Import every model module here so that `Base.metadata` is fully populated
for Alembic autogenerate and `alembic check`. Models are added in their
respective phases (Workspace/auth in Phase 2, Application/Vendor/Service in
Phase 3, CostItem/CostHistory in Phase 4, etc.).
"""

from __future__ import annotations

from stackup_api.core.db import Base

__all__ = ["Base"]
