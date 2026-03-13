"""Add is_active to model artifact

Revision ID: 7d3f1c2a9e11
Revises: f3d2c1b0a9e8
Create Date: 2026-03-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d3f1c2a9e11"
down_revision: str | None = "f3d2c1b0a9e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "model_artifact",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        op.f("ix_model_artifact_is_active"),
        "model_artifact",
        ["is_active"],
        unique=False,
    )

    # Set newest uploaded model as active so existing environments keep working.
    op.execute(
        """
        WITH newest AS (
            SELECT id FROM model_artifact
            ORDER BY created_at DESC NULLS LAST
            LIMIT 1
        )
        UPDATE model_artifact
        SET is_active = TRUE
        WHERE id IN (SELECT id FROM newest)
        """
    )

    op.alter_column("model_artifact", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_model_artifact_is_active"), table_name="model_artifact")
    op.drop_column("model_artifact", "is_active")
