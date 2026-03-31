"""UC-07 historical demand exploration schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "012_uc07_historical_demand_analysis"
down_revision = "011_uc06_evaluation_lifecycle"
branch_labels = None
depends_on = None


def _table_names(inspector: sa.Inspector) -> set[str]:
    return set(inspector.get_table_names())


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)

    if "historical_demand_analysis_requests" not in table_names:
        op.create_table(
            "historical_demand_analysis_requests",
            sa.Column("analysis_request_id", sa.String(length=36), primary_key=True),
            sa.Column("requested_by_actor", sa.String(length=32), nullable=False),
            sa.Column(
                "source_cleaned_dataset_version_id",
                sa.String(length=36),
                sa.ForeignKey("dataset_versions.dataset_version_id"),
                nullable=True,
            ),
            sa.Column("service_category_filter", sa.String(length=255), nullable=True),
            sa.Column("time_range_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("time_range_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("geography_filter_type", sa.String(length=32), nullable=True),
            sa.Column("geography_filter_value", sa.String(length=255), nullable=True),
            sa.Column("warning_status", sa.String(length=16), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True),
        )

    if "historical_demand_analysis_results" not in table_names:
        op.create_table(
            "historical_demand_analysis_results",
            sa.Column("analysis_result_id", sa.String(length=36), primary_key=True),
            sa.Column(
                "analysis_request_id",
                sa.String(length=36),
                sa.ForeignKey("historical_demand_analysis_requests.analysis_request_id"),
                nullable=False,
                unique=True,
            ),
            sa.Column(
                "source_cleaned_dataset_version_id",
                sa.String(length=36),
                sa.ForeignKey("dataset_versions.dataset_version_id"),
                nullable=False,
            ),
            sa.Column("aggregation_granularity", sa.String(length=16), nullable=False),
            sa.Column("result_mode", sa.String(length=16), nullable=False),
            sa.Column("service_category_filter", sa.String(length=255), nullable=True),
            sa.Column("time_range_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("time_range_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("geography_filter_type", sa.String(length=32), nullable=True),
            sa.Column("geography_filter_value", sa.String(length=255), nullable=True),
            sa.Column("record_count", sa.Integer(), nullable=False),
            sa.Column("stored_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "historical_demand_summary_points" not in table_names:
        op.create_table(
            "historical_demand_summary_points",
            sa.Column("summary_point_id", sa.String(length=36), primary_key=True),
            sa.Column(
                "analysis_result_id",
                sa.String(length=36),
                sa.ForeignKey("historical_demand_analysis_results.analysis_result_id"),
                nullable=False,
            ),
            sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("bucket_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("service_category", sa.String(length=255), nullable=False),
            sa.Column("geography_key", sa.String(length=255), nullable=True),
            sa.Column("demand_count", sa.Integer(), nullable=False),
        )

    if "historical_analysis_outcome_records" not in table_names:
        op.create_table(
            "historical_analysis_outcome_records",
            sa.Column("analysis_outcome_id", sa.String(length=36), primary_key=True),
            sa.Column(
                "analysis_request_id",
                sa.String(length=36),
                sa.ForeignKey("historical_demand_analysis_requests.analysis_request_id"),
                nullable=False,
                unique=True,
            ),
            sa.Column("outcome_type", sa.String(length=32), nullable=False),
            sa.Column("warning_acknowledged", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)
    if "historical_analysis_outcome_records" in table_names:
        op.drop_table("historical_analysis_outcome_records")
    if "historical_demand_summary_points" in table_names:
        op.drop_table("historical_demand_summary_points")
    if "historical_demand_analysis_results" in table_names:
        op.drop_table("historical_demand_analysis_results")
    if "historical_demand_analysis_requests" in table_names:
        op.drop_table("historical_demand_analysis_requests")
