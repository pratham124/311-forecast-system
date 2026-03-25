"""UC-04 weekly forecast lifecycle schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "006_uc04_weekly_forecast"
down_revision = "005_uc03_forecast_model_training"
branch_labels = None
depends_on = None


def _table_names(inspector: sa.Inspector) -> set[str]:
    return set(inspector.get_table_names())


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)

    if "weekly_forecast_runs" not in table_names:
        op.create_table(
            "weekly_forecast_runs",
            sa.Column("weekly_forecast_run_id", sa.String(length=36), primary_key=True),
            sa.Column("trigger_type", sa.String(length=32), nullable=False),
            sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id"), nullable=True),
            sa.Column("week_start_local", sa.DateTime(timezone=True), nullable=False),
            sa.Column("week_end_local", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("result_type", sa.String(length=32), nullable=True),
            sa.Column("generated_forecast_version_id", sa.String(length=36), nullable=True),
            sa.Column("served_forecast_version_id", sa.String(length=36), nullable=True),
            sa.Column("geography_scope", sa.String(length=32), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
        )
    if "weekly_forecast_versions" not in table_names:
        op.create_table(
            "weekly_forecast_versions",
            sa.Column("weekly_forecast_version_id", sa.String(length=36), primary_key=True),
            sa.Column("weekly_forecast_run_id", sa.String(length=36), sa.ForeignKey("weekly_forecast_runs.weekly_forecast_run_id"), nullable=False),
            sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id"), nullable=False),
            sa.Column("week_start_local", sa.DateTime(timezone=True), nullable=False),
            sa.Column("week_end_local", sa.DateTime(timezone=True), nullable=False),
            sa.Column("bucket_granularity", sa.String(length=16), nullable=False),
            sa.Column("bucket_count_days", sa.Integer(), nullable=False),
            sa.Column("geography_scope", sa.String(length=32), nullable=False),
            sa.Column("baseline_method", sa.String(length=64), nullable=False),
            sa.Column("storage_status", sa.String(length=16), nullable=False),
            sa.Column("is_current", sa.Boolean(), nullable=False),
            sa.Column("stored_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
        )
    if "weekly_forecast_buckets" not in table_names:
        op.create_table(
            "weekly_forecast_buckets",
            sa.Column("weekly_forecast_bucket_id", sa.String(length=36), primary_key=True),
            sa.Column("weekly_forecast_version_id", sa.String(length=36), sa.ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"), nullable=False),
            sa.Column("forecast_date_local", sa.Date(), nullable=False),
            sa.Column("service_category", sa.String(length=255), nullable=False),
            sa.Column("geography_key", sa.String(length=255), nullable=True),
            sa.Column("point_forecast", sa.Numeric(10, 2), nullable=False),
            sa.Column("quantile_p10", sa.Numeric(10, 2), nullable=False),
            sa.Column("quantile_p50", sa.Numeric(10, 2), nullable=False),
            sa.Column("quantile_p90", sa.Numeric(10, 2), nullable=False),
            sa.Column("baseline_value", sa.Numeric(10, 2), nullable=False),
        )
    if "current_weekly_forecast_markers" not in table_names:
        op.create_table(
            "current_weekly_forecast_markers",
            sa.Column("forecast_product_name", sa.String(length=64), primary_key=True),
            sa.Column("weekly_forecast_version_id", sa.String(length=36), sa.ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"), nullable=False),
            sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id"), nullable=False),
            sa.Column("week_start_local", sa.DateTime(timezone=True), nullable=False),
            sa.Column("week_end_local", sa.DateTime(timezone=True), nullable=False),
            sa.Column("geography_scope", sa.String(length=32), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_by_run_id", sa.String(length=36), sa.ForeignKey("weekly_forecast_runs.weekly_forecast_run_id"), nullable=False),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)
    if "current_weekly_forecast_markers" in table_names:
        op.drop_table("current_weekly_forecast_markers")
    if "weekly_forecast_buckets" in table_names:
        op.drop_table("weekly_forecast_buckets")
    if "weekly_forecast_versions" in table_names:
        op.drop_table("weekly_forecast_versions")
    if "weekly_forecast_runs" in table_names:
        op.drop_table("weekly_forecast_runs")
