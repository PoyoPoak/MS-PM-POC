"""Add model artifact table

Revision ID: c4f9ab72a1de
Revises: a5b5e3b3c9c1
Create Date: 2026-03-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c4f9ab72a1de"
down_revision: str | None = "a5b5e3b3c9c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_artifact",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_version_id", sa.String(length=255), nullable=True),
        sa.Column("source_run_id", sa.String(length=255), nullable=True),
        sa.Column("trained_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("algorithm", sa.String(length=255), nullable=False),
        sa.Column("hyperparameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("dataset_info", sa.JSON(), nullable=False),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("model_size_bytes", sa.Integer(), nullable=False),
        sa.Column("model_sha256", sa.String(length=64), nullable=False),
        sa.Column("model_blob", sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_model_artifact_client_version_id"),
        "model_artifact",
        ["client_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_artifact_model_sha256"),
        "model_artifact",
        ["model_sha256"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_artifact_source_run_id"),
        "model_artifact",
        ["source_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_model_artifact_source_run_id"),
        table_name="model_artifact",
    )
    op.drop_index(
        op.f("ix_model_artifact_model_sha256"),
        table_name="model_artifact",
    )
    op.drop_index(
        op.f("ix_model_artifact_client_version_id"),
        table_name="model_artifact",
    )
    op.drop_table("model_artifact")
