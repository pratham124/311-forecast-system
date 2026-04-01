"""uc08 demand comparison

Revision ID: 013_uc08_demand_comparisons
Revises: 012_uc07_historical_demand_analysis
Create Date: 2026-03-31
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "013_uc08_demand_comparisons"
down_revision = "012_uc07_historical_demand"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "demand_comparison_requests",
        sa.Column("comparison_request_id", sa.String(length=36), primary_key=True),
        sa.Column("requested_by_actor", sa.String(length=32), nullable=False),
        sa.Column("requested_by_subject", sa.String(length=255), nullable=False),
        sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_weekly_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("forecast_product_name", sa.String(length=64), nullable=True),
        sa.Column("forecast_granularity", sa.String(length=16), nullable=True),
        sa.Column("geography_level", sa.String(length=32), nullable=True),
        sa.Column("service_category_count", sa.Integer(), nullable=False),
        sa.Column("geography_value_count", sa.Integer(), nullable=False),
        sa.Column("time_range_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_range_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("warning_status", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("render_reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_cleaned_dataset_version_id"], ["dataset_versions.dataset_version_id"]),
        sa.ForeignKeyConstraint(["source_forecast_version_id"], ["forecast_versions.forecast_version_id"]),
        sa.ForeignKeyConstraint(["source_weekly_forecast_version_id"], ["weekly_forecast_versions.weekly_forecast_version_id"]),
    )
    op.create_table(
        "demand_comparison_results",
        sa.Column("comparison_result_id", sa.String(length=36), primary_key=True),
        sa.Column("comparison_request_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_weekly_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("forecast_product_name", sa.String(length=64), nullable=True),
        sa.Column("forecast_granularity", sa.String(length=16), nullable=True),
        sa.Column("result_mode", sa.String(length=16), nullable=False),
        sa.Column("comparison_granularity", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["comparison_request_id"], ["demand_comparison_requests.comparison_request_id"]),
        sa.ForeignKeyConstraint(["source_cleaned_dataset_version_id"], ["dataset_versions.dataset_version_id"]),
        sa.ForeignKeyConstraint(["source_forecast_version_id"], ["forecast_versions.forecast_version_id"]),
        sa.ForeignKeyConstraint(["source_weekly_forecast_version_id"], ["weekly_forecast_versions.weekly_forecast_version_id"]),
    )
    op.create_table(
        "demand_comparison_series_points",
        sa.Column("comparison_point_id", sa.String(length=36), primary_key=True),
        sa.Column("comparison_result_id", sa.String(length=36), nullable=False),
        sa.Column("series_type", sa.String(length=16), nullable=False),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bucket_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("geography_key", sa.String(length=255), nullable=True),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["comparison_result_id"], ["demand_comparison_results.comparison_result_id"]),
    )
    op.create_table(
        "comparison_missing_combinations",
        sa.Column("missing_combination_id", sa.String(length=36), primary_key=True),
        sa.Column("comparison_result_id", sa.String(length=36), nullable=False),
        sa.Column("service_category", sa.String(length=255), nullable=False),
        sa.Column("geography_key", sa.String(length=255), nullable=True),
        sa.Column("missing_source", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["comparison_result_id"], ["demand_comparison_results.comparison_result_id"]),
    )
    op.create_table(
        "demand_comparison_outcome_records",
        sa.Column("comparison_outcome_id", sa.String(length=36), primary_key=True),
        sa.Column("comparison_request_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("outcome_type", sa.String(length=32), nullable=False),
        sa.Column("warning_acknowledged", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["comparison_request_id"], ["demand_comparison_requests.comparison_request_id"]),
    )


def downgrade() -> None:
    op.drop_table("demand_comparison_outcome_records")
    op.drop_table("comparison_missing_combinations")
    op.drop_table("demand_comparison_series_points")
    op.drop_table("demand_comparison_results")
    op.drop_table("demand_comparison_requests")
