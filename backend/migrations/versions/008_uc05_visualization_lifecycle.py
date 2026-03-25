"""UC-05 visualization lifecycle schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "008_uc05_visualization_lifecycle"
down_revision = "007_uc03_model_product_scope"
branch_labels = None
depends_on = None


def _table_names(inspector: sa.Inspector) -> set[str]:
    return set(inspector.get_table_names())


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)

    if "visualization_load_records" not in table_names:
        op.create_table(
            "visualization_load_records",
            sa.Column("visualization_load_id", sa.String(length=36), primary_key=True),
            sa.Column("requested_by_actor", sa.String(length=64), nullable=False),
            sa.Column("forecast_product_name", sa.String(length=32), nullable=False),
            sa.Column("forecast_granularity", sa.String(length=16), nullable=False),
            sa.Column("service_category_filter", sa.String(length=255), nullable=True),
            sa.Column("history_window_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("history_window_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("forecast_window_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("forecast_window_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id"), nullable=True),
            sa.Column("source_forecast_version_id", sa.String(length=36), sa.ForeignKey("forecast_versions.forecast_version_id"), nullable=True),
            sa.Column("source_weekly_forecast_version_id", sa.String(length=36), sa.ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"), nullable=True),
            sa.Column("fallback_snapshot_id", sa.String(length=36), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("degradation_type", sa.String(length=32), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("render_reported_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True),
        )
    if "visualization_snapshots" not in table_names:
        op.create_table(
            "visualization_snapshots",
            sa.Column("visualization_snapshot_id", sa.String(length=36), primary_key=True),
            sa.Column("forecast_product_name", sa.String(length=32), nullable=False),
            sa.Column("forecast_granularity", sa.String(length=16), nullable=False),
            sa.Column("service_category_filter", sa.String(length=255), nullable=True),
            sa.Column("source_cleaned_dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id"), nullable=False),
            sa.Column("source_forecast_version_id", sa.String(length=36), sa.ForeignKey("forecast_versions.forecast_version_id"), nullable=True),
            sa.Column("source_weekly_forecast_version_id", sa.String(length=36), sa.ForeignKey("weekly_forecast_versions.weekly_forecast_version_id"), nullable=True),
            sa.Column("source_forecast_run_id", sa.String(length=36), sa.ForeignKey("forecast_runs.forecast_run_id"), nullable=True),
            sa.Column("source_weekly_forecast_run_id", sa.String(length=36), sa.ForeignKey("weekly_forecast_runs.weekly_forecast_run_id"), nullable=True),
            sa.Column("history_window_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("history_window_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("forecast_window_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("forecast_window_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("band_standard", sa.String(length=32), nullable=False),
            sa.Column("snapshot_status", sa.String(length=16), nullable=False),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_from_load_id", sa.String(length=36), sa.ForeignKey("visualization_load_records.visualization_load_id"), nullable=False),
        )
    inspector = sa.inspect(op.get_bind())
    if "visualization_load_records" in inspector.get_table_names():
        fk_columns = {
            fk["constrained_columns"][0]
            for fk in inspector.get_foreign_keys("visualization_load_records")
            if fk["constrained_columns"]
        }
        if "fallback_snapshot_id" not in fk_columns:
            with op.batch_alter_table("visualization_load_records") as batch_op:
                batch_op.create_foreign_key(
                    "fk_visualization_load_records_fallback_snapshot_id",
                    "visualization_snapshots",
                    ["fallback_snapshot_id"],
                    ["visualization_snapshot_id"],
                )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "visualization_load_records" in inspector.get_table_names():
        fk_names = {fk["name"] for fk in inspector.get_foreign_keys("visualization_load_records")}
        if "fk_visualization_load_records_fallback_snapshot_id" in fk_names:
            with op.batch_alter_table("visualization_load_records") as batch_op:
                batch_op.drop_constraint("fk_visualization_load_records_fallback_snapshot_id", type_="foreignkey")
    inspector = sa.inspect(op.get_bind())
    if "visualization_snapshots" in inspector.get_table_names():
        op.drop_table("visualization_snapshots")
    if "visualization_load_records" in inspector.get_table_names():
        op.drop_table("visualization_load_records")
