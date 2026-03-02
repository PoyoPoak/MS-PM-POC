"""Add patient latest telemetry table

Revision ID: f3d2c1b0a9e8
Revises: e38207e9b7d2
Create Date: 2026-03-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3d2c1b0a9e8"
down_revision: str | None = "e38207e9b7d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patient_latest_telemetry",
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lead_impedance_ohms", sa.Float(), nullable=False),
        sa.Column("capture_threshold_v", sa.Float(), nullable=False),
        sa.Column("r_wave_sensing_mv", sa.Float(), nullable=False),
        sa.Column("battery_voltage_v", sa.Float(), nullable=False),
        sa.Column("lead_impedance_ohms_rolling_mean_3d", sa.Float(), nullable=True),
        sa.Column("lead_impedance_ohms_rolling_mean_7d", sa.Float(), nullable=True),
        sa.Column("capture_threshold_v_rolling_mean_3d", sa.Float(), nullable=True),
        sa.Column("capture_threshold_v_rolling_mean_7d", sa.Float(), nullable=True),
        sa.Column("lead_impedance_ohms_delta_per_day_3d", sa.Float(), nullable=True),
        sa.Column("lead_impedance_ohms_delta_per_day_7d", sa.Float(), nullable=True),
        sa.Column("capture_threshold_v_delta_per_day_3d", sa.Float(), nullable=True),
        sa.Column("capture_threshold_v_delta_per_day_7d", sa.Float(), nullable=True),
        sa.Column("fail_probability", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("patient_id"),
    )
    op.create_index(
        op.f("ix_patient_latest_telemetry_timestamp"),
        "patient_latest_telemetry",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_patient_latest_telemetry_timestamp"),
        table_name="patient_latest_telemetry",
    )
    op.drop_table("patient_latest_telemetry")
