"""uc11 surge alerts

Revision ID: 020_uc11_surge_alerts
Revises: 019_merge_uc14_uc19_heads
Create Date: 2026-04-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "020_uc11_surge_alerts"
down_revision = "019_merge_uc14_uc19_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "surge_detection_configurations",
        sa.Column("surge_detection_configuration_id", sa.String(length=36), primary_key=True),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("forecast_product", sa.String(length=16), nullable=False),
        sa.Column("z_score_threshold", sa.Numeric(10, 4), nullable=False),
        sa.Column("percent_above_forecast_floor", sa.Numeric(10, 4), nullable=False),
        sa.Column("rolling_baseline_window_count", sa.Integer(), nullable=False),
        sa.Column("notification_channels_json", sa.Text(), nullable=False),
        sa.Column("operational_manager_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "service_category",
            "forecast_product",
            "operational_manager_id",
            "effective_from",
            name="uq_surge_detection_configurations_scope_effective_from",
        ),
    )
    op.create_table(
        "surge_evaluation_runs",
        sa.Column("surge_evaluation_run_id", sa.String(length=36), primary_key=True),
        sa.Column("ingestion_run_id", sa.String(length=36), nullable=False),
        sa.Column("trigger_source", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("evaluated_scope_count", sa.Integer(), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("confirmed_count", sa.Integer(), nullable=False),
        sa.Column("notification_created_count", sa.Integer(), nullable=False),
        sa.Column("failure_summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.run_id"]),
    )
    op.create_table(
        "surge_candidates",
        sa.Column("surge_candidate_id", sa.String(length=36), primary_key=True),
        sa.Column("surge_evaluation_run_id", sa.String(length=36), nullable=False),
        sa.Column("surge_detection_configuration_id", sa.String(length=36), nullable=True),
        sa.Column("forecast_run_id", sa.String(length=36), nullable=True),
        sa.Column("forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("evaluation_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluation_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_demand_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("forecast_p50_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("residual_value", sa.Numeric(10, 4), nullable=True),
        sa.Column("residual_z_score", sa.Numeric(10, 4), nullable=True),
        sa.Column("percent_above_forecast", sa.Numeric(10, 4), nullable=True),
        sa.Column("rolling_baseline_mean", sa.Numeric(10, 4), nullable=True),
        sa.Column("rolling_baseline_stddev", sa.Numeric(10, 4), nullable=True),
        sa.Column("candidate_status", sa.String(length=32), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["forecast_run_id"], ["forecast_runs.forecast_run_id"]),
        sa.ForeignKeyConstraint(["forecast_version_id"], ["forecast_versions.forecast_version_id"]),
        sa.ForeignKeyConstraint(["surge_detection_configuration_id"], ["surge_detection_configurations.surge_detection_configuration_id"]),
        sa.ForeignKeyConstraint(["surge_evaluation_run_id"], ["surge_evaluation_runs.surge_evaluation_run_id"]),
    )
    op.create_table(
        "surge_notification_events",
        sa.Column("surge_notification_event_id", sa.String(length=36), primary_key=True),
        sa.Column("surge_evaluation_run_id", sa.String(length=36), nullable=False),
        sa.Column("surge_candidate_id", sa.String(length=36), nullable=False),
        sa.Column("surge_detection_configuration_id", sa.String(length=36), nullable=False),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("forecast_product", sa.String(length=16), nullable=False),
        sa.Column("evaluation_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluation_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_demand_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("forecast_p50_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("residual_value", sa.Numeric(10, 4), nullable=False),
        sa.Column("residual_z_score", sa.Numeric(10, 4), nullable=False),
        sa.Column("percent_above_forecast", sa.Numeric(10, 4), nullable=True),
        sa.Column("overall_delivery_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("follow_up_reason", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["surge_candidate_id"], ["surge_candidates.surge_candidate_id"]),
        sa.ForeignKeyConstraint(["surge_detection_configuration_id"], ["surge_detection_configurations.surge_detection_configuration_id"]),
        sa.ForeignKeyConstraint(["surge_evaluation_run_id"], ["surge_evaluation_runs.surge_evaluation_run_id"]),
    )
    op.create_table(
        "surge_confirmation_outcomes",
        sa.Column("surge_confirmation_outcome_id", sa.String(length=36), primary_key=True),
        sa.Column("surge_candidate_id", sa.String(length=36), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("z_score_check_passed", sa.Boolean(), nullable=True),
        sa.Column("percent_floor_check_passed", sa.Boolean(), nullable=True),
        sa.Column("surge_notification_event_id", sa.String(length=36), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["surge_candidate_id"], ["surge_candidates.surge_candidate_id"]),
        sa.ForeignKeyConstraint(["surge_notification_event_id"], ["surge_notification_events.surge_notification_event_id"]),
    )
    op.create_table(
        "surge_states",
        sa.Column("surge_state_id", sa.String(length=36), primary_key=True),
        sa.Column("surge_detection_configuration_id", sa.String(length=36), nullable=False),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("forecast_product", sa.String(length=16), nullable=False),
        sa.Column("current_state", sa.String(length=32), nullable=False),
        sa.Column("notification_armed", sa.Boolean(), nullable=False),
        sa.Column("active_since", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_to_normal_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_surge_candidate_id", sa.String(length=36), nullable=True),
        sa.Column("last_confirmation_outcome_id", sa.String(length=36), nullable=True),
        sa.Column("last_notification_event_id", sa.String(length=36), nullable=True),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["last_confirmation_outcome_id"], ["surge_confirmation_outcomes.surge_confirmation_outcome_id"]),
        sa.ForeignKeyConstraint(["last_notification_event_id"], ["surge_notification_events.surge_notification_event_id"]),
        sa.ForeignKeyConstraint(["last_surge_candidate_id"], ["surge_candidates.surge_candidate_id"]),
        sa.ForeignKeyConstraint(["surge_detection_configuration_id"], ["surge_detection_configurations.surge_detection_configuration_id"]),
        sa.UniqueConstraint("service_category", "forecast_product", name="uq_surge_states_scope"),
    )
    op.create_table(
        "surge_notification_channel_attempts",
        sa.Column("surge_notification_channel_attempt_id", sa.String(length=36), primary_key=True),
        sa.Column("surge_notification_event_id", sa.String(length=36), nullable=False),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("provider_reference", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["surge_notification_event_id"], ["surge_notification_events.surge_notification_event_id"]),
    )


def downgrade() -> None:
    op.drop_table("surge_notification_channel_attempts")
    op.drop_table("surge_states")
    op.drop_table("surge_confirmation_outcomes")
    op.drop_table("surge_notification_events")
    op.drop_table("surge_candidates")
    op.drop_table("surge_evaluation_runs")
    op.drop_table("surge_detection_configurations")
