"""user full name

Revision ID: 0008_user_full_name
Revises: 0007_github_integration
Create Date: 2026-08-20 12:38:59.822723
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_user_full_name"
down_revision: str | None = "0007_github_integration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user", sa.Column("full_name", sa.String(length=160), nullable=True))


def downgrade() -> None:
    op.drop_column("user", "full_name")
