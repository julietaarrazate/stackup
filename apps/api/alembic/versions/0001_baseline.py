"""baseline — establishes the migration chain

This baseline intentionally creates no tables. It exists so the migration
history has a root, the async Alembic environment is proven to run against
the target datastore (Neon), and later phases add tables on top of a stable
starting point. Domain tables are introduced in Phase 2+ migrations.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-08-19
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
