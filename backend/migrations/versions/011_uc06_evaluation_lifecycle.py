"""uc06 evaluation lifecycle

Revision ID: 011_uc06_evaluation_lifecycle
Revises: 010_refresh_sessions
Create Date: 2026-03-25 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "011_uc06_evaluation_lifecycle"
down_revision = "010_refresh_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("evaluation_run_id", sa.String(length=36), primary_key=True),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("forecast_product_name", sa.String(length=64), nullable=False),
        sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_weekly_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("evaluation_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluation_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("result_type", sa.String(length=32), nullable=True),
        sa.Column("evaluation_result_id", sa.String(length=36), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_cleaned_dataset_version_id"], ["dataset_versions.dataset_version_id"]),
        sa.ForeignKeyConstraint(["source_forecast_version_id"], ["forecast_versions.forecast_version_id"]),
        sa.ForeignKeyConstraint(["source_weekly_forecast_version_id"], ["weekly_forecast_versions.weekly_forecast_version_id"]),
    )
    op.create_table(
        "evaluation_results",
        sa.Column("evaluation_result_id", sa.String(length=36), primary_key=True),
        sa.Column("evaluation_run_id", sa.String(length=36), nullable=False),
        sa.Column("forecast_product_name", sa.String(length=64), nullable=False),
        sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), nullable=False),
        sa.Column("source_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_weekly_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("evaluation_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluation_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comparison_status", sa.String(length=16), nullable=False),
        sa.Column("baseline_methods_json", sa.Text(), nullable=False),
        sa.Column("metric_set_json", sa.Text(), nullable=False),
        sa.Column("storage_status", sa.String(length=16), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("comparison_summary", sa.Text(), nullable=True),
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.evaluation_run_id"]),
        sa.ForeignKeyConstraint(["source_cleaned_dataset_version_id"], ["dataset_versions.dataset_version_id"]),
        sa.ForeignKeyConstraint(["source_forecast_version_id"], ["forecast_versions.forecast_version_id"]),
        sa.ForeignKeyConstraint(["source_weekly_forecast_version_id"], ["weekly_forecast_versions.weekly_forecast_version_id"]),
    )
    op.create_table(
        "evaluation_segments",
        sa.Column("evaluation_segment_id", sa.String(length=36), primary_key=True),
        sa.Column("evaluation_result_id", sa.String(length=36), nullable=False),
        sa.Column("segment_type", sa.String(length=32), nullable=False),
        sa.Column("segment_key", sa.String(length=255), nullable=False),
        sa.Column("segment_status", sa.String(length=16), nullable=False),
        sa.Column("comparison_row_count", sa.Integer(), nullable=False),
        sa.Column("excluded_metric_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["evaluation_result_id"], ["evaluation_results.evaluation_result_id"]),
    )
    op.create_table(
        "metric_comparison_values",
        sa.Column("metric_comparison_value_id", sa.String(length=36), primary_key=True),
        sa.Column("evaluation_segment_id", sa.String(length=36), nullable=False),
        sa.Column("compared_method", sa.String(length=32), nullable=False),
        sa.Column("compared_method_label", sa.String(length=128), nullable=False),
        sa.Column("metric_name", sa.String(length=16), nullable=False),
        sa.Column("metric_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("is_excluded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("exclusion_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["evaluation_segment_id"], ["evaluation_segments.evaluation_segment_id"]),
    )
    op.create_table(
        "current_evaluation_markers",
        sa.Column("forecast_product_name", sa.String(length=64), primary_key=True),
        sa.Column("evaluation_result_id", sa.String(length=36), nullable=False),
        sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), nullable=False),
        sa.Column("source_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_weekly_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("evaluation_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluation_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comparison_status", sa.String(length=16), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_run_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_result_id"], ["evaluation_results.evaluation_result_id"]),
        sa.ForeignKeyConstraint(["source_cleaned_dataset_version_id"], ["dataset_versions.dataset_version_id"]),
        sa.ForeignKeyConstraint(["source_forecast_version_id"], ["forecast_versions.forecast_version_id"]),
        sa.ForeignKeyConstraint(["source_weekly_forecast_version_id"], ["weekly_forecast_versions.weekly_forecast_version_id"]),
        sa.ForeignKeyConstraint(["updated_by_run_id"], ["evaluation_runs.evaluation_run_id"]),
    )


def downgrade() -> None:
    op.drop_table("current_evaluation_markers")
    op.drop_table("metric_comparison_values")
    op.drop_table("evaluation_segments")
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_runs")
