"""Add pacemaker telemetry table

Revision ID: a5b5e3b3c9c1
Revises: fe56fa70289e
Create Date: 2026-02-28 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a5b5e3b3c9c1"
down_revision: str | None = "fe56fa70289e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pacemaker_telemetry",
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lead_impedance_ohms", sa.Float(), nullable=False),
        sa.Column("capture_threshold_v", sa.Float(), nullable=False),
        sa.Column("r_wave_sensing_mv", sa.Float(), nullable=False),
        sa.Column("battery_voltage_v", sa.Float(), nullable=False),
        sa.Column("target_fail_next_7d", sa.Integer(), nullable=True),
        sa.Column(
            "lead_impedance_ohms_rolling_mean_3d",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "lead_impedance_ohms_rolling_mean_7d",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "capture_threshold_v_rolling_mean_3d",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "capture_threshold_v_rolling_mean_7d",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "lead_impedance_ohms_delta_per_day_3d",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "lead_impedance_ohms_delta_per_day_7d",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "capture_threshold_v_delta_per_day_3d",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "capture_threshold_v_delta_per_day_7d",
            sa.Float(),
            nullable=True,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_pacemaker_telemetry_patient_id"),
        "pacemaker_telemetry",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pacemaker_telemetry_timestamp"),
        "pacemaker_telemetry",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_pacemaker_telemetry_timestamp"),
        table_name="pacemaker_telemetry",
    )
    op.drop_index(
        op.f("ix_pacemaker_telemetry_patient_id"),
        table_name="pacemaker_telemetry",
    )
    op.drop_table("pacemaker_telemetry")
