"""Forecast model training lineage and artifact storage."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "005_uc03_forecast_model_training"
down_revision = "004_uc02_cleaned_current_records"
branch_labels = None
depends_on = None


def _table_names(inspector: sa.Inspector) -> set[str]:
    return set(inspector.get_table_names())


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)

    if "forecast_model_runs" not in table_names:
        op.create_table(
            "forecast_model_runs",
            sa.Column("forecast_model_run_id", sa.String(length=36), primary_key=True),
            sa.Column("trigger_type", sa.String(length=32), nullable=False),
            sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id"), nullable=True),
            sa.Column("training_window_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("training_window_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("result_type", sa.String(length=32), nullable=True),
            sa.Column("forecast_model_artifact_id", sa.String(length=36), nullable=True),
            sa.Column("geography_scope", sa.String(length=32), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
        )
    if "forecast_model_artifacts" not in table_names:
        op.create_table(
            "forecast_model_artifacts",
            sa.Column("forecast_model_artifact_id", sa.String(length=36), primary_key=True),
            sa.Column("forecast_model_run_id", sa.String(length=36), sa.ForeignKey("forecast_model_runs.forecast_model_run_id"), nullable=False),
            sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id"), nullable=False),
            sa.Column("geography_scope", sa.String(length=32), nullable=False),
            sa.Column("model_family", sa.String(length=32), nullable=False),
            sa.Column("baseline_method", sa.String(length=64), nullable=False),
            sa.Column("feature_schema_version", sa.String(length=32), nullable=False),
            sa.Column("artifact_path", sa.Text(), nullable=False),
            sa.Column("storage_status", sa.String(length=16), nullable=False),
            sa.Column("is_current", sa.Boolean(), nullable=False),
            sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
        )
    if "current_forecast_model_markers" not in table_names:
        op.create_table(
            "current_forecast_model_markers",
            sa.Column("forecast_product_name", sa.String(length=64), primary_key=True),
            sa.Column("forecast_model_artifact_id", sa.String(length=36), sa.ForeignKey("forecast_model_artifacts.forecast_model_artifact_id"), nullable=False),
            sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id"), nullable=False),
            sa.Column("training_window_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("training_window_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_by_run_id", sa.String(length=36), sa.ForeignKey("forecast_model_runs.forecast_model_run_id"), nullable=False),
            sa.Column("geography_scope", sa.String(length=32), nullable=False),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)
    if "current_forecast_model_markers" in table_names:
        op.drop_table("current_forecast_model_markers")
    if "forecast_model_artifacts" in table_names:
        op.drop_table("forecast_model_artifacts")
    if "forecast_model_runs" in table_names:
        op.drop_table("forecast_model_runs")
