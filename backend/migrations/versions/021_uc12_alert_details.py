"""uc12 alert details

Revision ID: 021_uc12_alert_details
Revises: 020_uc11_surge_alerts
Create Date: 2026-04-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "021_uc12_alert_details"
down_revision = "020_uc11_surge_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_detail_load_records",
        sa.Column("alert_detail_load_id", sa.String(length=36), primary_key=True),
        sa.Column("alert_source", sa.String(length=32), nullable=False),
        sa.Column("alert_id", sa.String(length=36), nullable=False),
        sa.Column("requested_by_subject", sa.String(length=255), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_weekly_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_threshold_evaluation_run_id", sa.String(length=36), nullable=True),
        sa.Column("source_surge_evaluation_run_id", sa.String(length=36), nullable=True),
        sa.Column("source_surge_candidate_id", sa.String(length=36), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("view_status", sa.String(length=24), nullable=False),
        sa.Column("distribution_status", sa.String(length=24), nullable=False),
        sa.Column("drivers_status", sa.String(length=24), nullable=False),
        sa.Column("anomalies_status", sa.String(length=24), nullable=False),
        sa.Column("preparation_status", sa.String(length=24), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("render_status", sa.String(length=24), nullable=True),
        sa.Column("render_failure_reason", sa.Text(), nullable=True),
        sa.Column("render_reported_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("alert_detail_load_records")
