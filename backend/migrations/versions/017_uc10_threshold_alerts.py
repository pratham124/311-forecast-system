"""uc10 threshold alerts

Revision ID: 017_uc10_threshold_alerts
Revises: 016_uc17_public_forecast_portal
Create Date: 2026-04-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "017_uc10_threshold_alerts"
down_revision = "016_uc17_public_forecast_portal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "threshold_configurations",
        sa.Column("threshold_configuration_id", sa.String(length=36), primary_key=True),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("geography_type", sa.String(length=64), nullable=True),
        sa.Column("geography_value", sa.String(length=255), nullable=True),
        sa.Column("forecast_window_type", sa.String(length=32), nullable=False),
        sa.Column("threshold_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("notification_channels_json", sa.Text(), nullable=False),
        sa.Column("operational_manager_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "service_category",
            "geography_type",
            "geography_value",
            "forecast_window_type",
            "operational_manager_id",
            "effective_from",
            name="uq_threshold_configurations_scope_effective_from",
        ),
    )
    op.create_table(
        "threshold_evaluation_runs",
        sa.Column("threshold_evaluation_run_id", sa.String(length=36), primary_key=True),
        sa.Column("forecast_run_id", sa.String(length=36), nullable=True),
        sa.Column("forecast_version_reference", sa.String(length=36), nullable=False),
        sa.Column("forecast_product", sa.String(length=16), nullable=False),
        sa.Column("trigger_source", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("evaluated_scope_count", sa.Integer(), nullable=False),
        sa.Column("alert_created_count", sa.Integer(), nullable=False),
        sa.Column("failure_summary", sa.Text(), nullable=True),
    )
    op.create_table(
        "notification_events",
        sa.Column("notification_event_id", sa.String(length=36), primary_key=True),
        sa.Column("threshold_evaluation_run_id", sa.String(length=36), nullable=False),
        sa.Column("threshold_configuration_id", sa.String(length=36), nullable=False),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("geography_type", sa.String(length=64), nullable=True),
        sa.Column("geography_value", sa.String(length=255), nullable=True),
        sa.Column("forecast_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_window_type", sa.String(length=32), nullable=False),
        sa.Column("forecast_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("threshold_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("overall_delivery_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("follow_up_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["threshold_configuration_id"],
            ["threshold_configurations.threshold_configuration_id"],
        ),
        sa.ForeignKeyConstraint(
            ["threshold_evaluation_run_id"],
            ["threshold_evaluation_runs.threshold_evaluation_run_id"],
        ),
    )
    op.create_table(
        "notification_channel_attempts",
        sa.Column("notification_channel_attempt_id", sa.String(length=36), primary_key=True),
        sa.Column("notification_event_id", sa.String(length=36), nullable=False),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("provider_reference", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["notification_event_id"],
            ["notification_events.notification_event_id"],
        ),
    )
    op.create_table(
        "threshold_scope_evaluations",
        sa.Column("threshold_scope_evaluation_id", sa.String(length=36), primary_key=True),
        sa.Column("threshold_evaluation_run_id", sa.String(length=36), nullable=False),
        sa.Column("threshold_configuration_id", sa.String(length=36), nullable=True),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("geography_type", sa.String(length=64), nullable=True),
        sa.Column("geography_value", sa.String(length=255), nullable=True),
        sa.Column("forecast_window_type", sa.String(length=32), nullable=False),
        sa.Column("forecast_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_bucket_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("threshold_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("notification_event_id", sa.String(length=36), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["notification_event_id"],
            ["notification_events.notification_event_id"],
        ),
        sa.ForeignKeyConstraint(
            ["threshold_configuration_id"],
            ["threshold_configurations.threshold_configuration_id"],
        ),
        sa.ForeignKeyConstraint(
            ["threshold_evaluation_run_id"],
            ["threshold_evaluation_runs.threshold_evaluation_run_id"],
        ),
    )
    op.create_table(
        "threshold_states",
        sa.Column("threshold_state_id", sa.String(length=36), primary_key=True),
        sa.Column("threshold_configuration_id", sa.String(length=36), nullable=False),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("geography_type", sa.String(length=64), nullable=True),
        sa.Column("geography_value", sa.String(length=255), nullable=True),
        sa.Column("forecast_window_type", sa.String(length=32), nullable=False),
        sa.Column("forecast_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_state", sa.String(length=32), nullable=False),
        sa.Column("last_forecast_bucket_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("last_threshold_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_notification_event_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["last_notification_event_id"],
            ["notification_events.notification_event_id"],
        ),
        sa.ForeignKeyConstraint(
            ["threshold_configuration_id"],
            ["threshold_configurations.threshold_configuration_id"],
        ),
        sa.UniqueConstraint(
            "service_category",
            "geography_type",
            "geography_value",
            "forecast_window_type",
            "forecast_window_start",
            "forecast_window_end",
            name="uq_threshold_states_scope_window",
        ),
    )


def downgrade() -> None:
    op.drop_table("threshold_states")
    op.drop_table("threshold_scope_evaluations")
    op.drop_table("notification_channel_attempts")
    op.drop_table("notification_events")
    op.drop_table("threshold_evaluation_runs")
    op.drop_table("threshold_configurations")
