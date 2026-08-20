"""github integration

Revision ID: 0007_github_integration
Revises: 0006_background_jobs
Create Date: 2026-08-20 05:14:06.017927
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_github_integration"
down_revision: str | None = "0006_background_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_connection",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("github_login", sa.String(length=120), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", name="uq_github_connection_workspace"),
    )
    op.create_index(
        op.f("ix_github_connection_workspace_id"),
        "github_connection",
        ["workspace_id"],
    )
    op.create_table(
        "detection",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("repo_full_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("vendor_name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("evidence", sa.String(length=500), nullable=False),
        sa.Column(
            "confidence",
            sa.Enum(
                "high",
                "medium",
                name="detectionconfidence",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "confirmed",
                "dismissed",
                name="detectionstatus",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("cost_item_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["application.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["cost_item_id"], ["cost_item.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "repo_full_name",
            "file_path",
            "vendor_name",
            name="uq_detection_signal",
        ),
    )
    op.create_index(
        op.f("ix_detection_application_id"), "detection", ["application_id"]
    )
    op.create_index(op.f("ix_detection_status"), "detection", ["status"])
    op.create_index(op.f("ix_detection_workspace_id"), "detection", ["workspace_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_detection_workspace_id"), table_name="detection")
    op.drop_index(op.f("ix_detection_status"), table_name="detection")
    op.drop_index(op.f("ix_detection_application_id"), table_name="detection")
    op.drop_table("detection")
    op.drop_index(
        op.f("ix_github_connection_workspace_id"), table_name="github_connection"
    )
    op.drop_table("github_connection")
