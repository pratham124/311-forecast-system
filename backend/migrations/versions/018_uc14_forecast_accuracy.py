"""uc14 forecast accuracy

Revision ID: 018_uc14_forecast_accuracy
Revises: 017_uc10_threshold_alerts
Create Date: 2026-04-10 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "018_uc14_forecast_accuracy"
down_revision = "017_uc10_threshold_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forecast_accuracy_requests",
        sa.Column("forecast_accuracy_request_id", sa.String(length=36), primary_key=True),
        sa.Column("requested_by_actor", sa.String(length=32), nullable=False),
        sa.Column("requested_by_subject", sa.String(length=255), nullable=False),
        sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_evaluation_result_id", sa.String(length=36), nullable=True),
        sa.Column("forecast_product_name", sa.String(length=64), nullable=True),
        sa.Column("comparison_granularity", sa.String(length=16), nullable=False),
        sa.Column("time_range_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_range_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("service_category", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("render_reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_cleaned_dataset_version_id"], ["dataset_versions.dataset_version_id"]),
        sa.ForeignKeyConstraint(["source_forecast_version_id"], ["forecast_versions.forecast_version_id"]),
        sa.ForeignKeyConstraint(["source_evaluation_result_id"], ["evaluation_results.evaluation_result_id"]),
    )
    op.create_table(
        "forecast_accuracy_metric_resolutions",
        sa.Column("forecast_accuracy_metric_resolution_id", sa.String(length=36), primary_key=True),
        sa.Column("forecast_accuracy_request_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("source_evaluation_result_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_status", sa.String(length=32), nullable=False),
        sa.Column("metric_names_json", sa.Text(), nullable=False),
        sa.Column("metric_values_json", sa.Text(), nullable=True),
        sa.Column("status_message", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["forecast_accuracy_request_id"], ["forecast_accuracy_requests.forecast_accuracy_request_id"]),
        sa.ForeignKeyConstraint(["source_evaluation_result_id"], ["evaluation_results.evaluation_result_id"]),
    )
    op.create_table(
        "forecast_accuracy_results",
        sa.Column("forecast_accuracy_result_id", sa.String(length=36), primary_key=True),
        sa.Column("forecast_accuracy_request_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("view_status", sa.String(length=32), nullable=False),
        sa.Column("metric_resolution_status", sa.String(length=32), nullable=True),
        sa.Column("status_message", sa.Text(), nullable=True),
        sa.Column("aligned_bucket_count", sa.Integer(), nullable=False),
        sa.Column("excluded_bucket_count", sa.Integer(), nullable=False),
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["forecast_accuracy_request_id"], ["forecast_accuracy_requests.forecast_accuracy_request_id"]),
    )
    op.create_table(
        "forecast_accuracy_aligned_buckets",
        sa.Column("forecast_accuracy_aligned_bucket_id", sa.String(length=36), primary_key=True),
        sa.Column("forecast_accuracy_result_id", sa.String(length=36), nullable=False),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bucket_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("service_category", sa.String(length=255), nullable=True),
        sa.Column("forecast_value", sa.Numeric(12, 4), nullable=False),
        sa.Column("actual_value", sa.Numeric(12, 4), nullable=False),
        sa.Column("absolute_error_value", sa.Numeric(12, 4), nullable=False),
        sa.Column("percentage_error_value", sa.Numeric(12, 4), nullable=True),
        sa.ForeignKeyConstraint(["forecast_accuracy_result_id"], ["forecast_accuracy_results.forecast_accuracy_result_id"]),
    )
    op.create_table(
        "forecast_accuracy_render_events",
        sa.Column("forecast_accuracy_render_event_id", sa.String(length=36), primary_key=True),
        sa.Column("forecast_accuracy_request_id", sa.String(length=36), nullable=False),
        sa.Column("forecast_accuracy_result_id", sa.String(length=36), nullable=False),
        sa.Column("render_outcome", sa.String(length=32), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("reported_by_subject", sa.String(length=255), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["forecast_accuracy_request_id"], ["forecast_accuracy_requests.forecast_accuracy_request_id"]),
        sa.ForeignKeyConstraint(["forecast_accuracy_result_id"], ["forecast_accuracy_results.forecast_accuracy_result_id"]),
    )


def downgrade() -> None:
    op.drop_table("forecast_accuracy_render_events")
    op.drop_table("forecast_accuracy_aligned_buckets")
    op.drop_table("forecast_accuracy_results")
    op.drop_table("forecast_accuracy_metric_resolutions")
    op.drop_table("forecast_accuracy_requests")
