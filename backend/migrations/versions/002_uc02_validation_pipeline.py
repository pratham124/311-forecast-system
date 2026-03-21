"""UC-02 validation and deduplication schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002_uc02_validation_pipeline"
down_revision = "001_uc01_ingestion_foundation"
branch_labels = None
depends_on = None


DATASET_VERSION_UC02_COLUMNS = {
    "source_dataset_version_id": sa.Column("source_dataset_version_id", sa.String(length=36), nullable=True),
    "dataset_kind": sa.Column("dataset_kind", sa.String(length=16), nullable=False, server_default="source"),
    "duplicate_group_count": sa.Column("duplicate_group_count", sa.Integer(), nullable=False, server_default="0"),
    "approved_by_validation_run_id": sa.Column("approved_by_validation_run_id", sa.String(length=36), nullable=True),
}


def _table_names(inspector: sa.Inspector) -> set[str]:
    return set(inspector.get_table_names())


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _foreign_key_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {
        foreign_key["name"]
        for foreign_key in inspector.get_foreign_keys(table_name)
        if foreign_key.get("name") is not None
    }


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = _table_names(inspector)

    existing_dataset_version_columns = _column_names(inspector, "dataset_versions")
    for column_name, column in DATASET_VERSION_UC02_COLUMNS.items():
        if column_name not in existing_dataset_version_columns:
            op.add_column("dataset_versions", column)

    if bind.dialect.name != "sqlite":
        foreign_key_names = _foreign_key_names(inspector, "dataset_versions")
        if "fk_dataset_versions_source_dataset_version_id" not in foreign_key_names:
            op.create_foreign_key(
                "fk_dataset_versions_source_dataset_version_id",
                "dataset_versions",
                "dataset_versions",
                ["source_dataset_version_id"],
                ["dataset_version_id"],
            )

    if "validation_runs" not in table_names:
        op.create_table(
            "validation_runs",
            sa.Column("validation_run_id", sa.String(length=36), primary_key=True),
            sa.Column("ingestion_run_id", sa.String(length=36), sa.ForeignKey("ingestion_runs.run_id"), nullable=False),
            sa.Column(
                "source_dataset_version_id",
                sa.String(length=36),
                sa.ForeignKey("dataset_versions.dataset_version_id"),
                nullable=False,
            ),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("failure_stage", sa.String(length=32), nullable=True),
            sa.Column("duplicate_threshold_type", sa.String(length=32), nullable=False),
            sa.Column("duplicate_percentage", sa.Numeric(5, 2), nullable=True),
            sa.Column(
                "approved_dataset_version_id",
                sa.String(length=36),
                sa.ForeignKey("dataset_versions.dataset_version_id"),
                nullable=True,
            ),
            sa.Column("review_reason", sa.Text(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
        )
    if "validation_results" not in table_names:
        op.create_table(
            "validation_results",
            sa.Column("validation_result_id", sa.String(length=36), primary_key=True),
            sa.Column(
                "validation_run_id",
                sa.String(length=36),
                sa.ForeignKey("validation_runs.validation_run_id"),
                nullable=False,
                unique=True,
            ),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("required_field_check", sa.String(length=16), nullable=False),
            sa.Column("type_check", sa.String(length=16), nullable=False),
            sa.Column("format_check", sa.String(length=16), nullable=False),
            sa.Column("completeness_check", sa.String(length=16), nullable=False),
            sa.Column("issue_summary", sa.Text(), nullable=True),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "duplicate_analysis_results" not in table_names:
        op.create_table(
            "duplicate_analysis_results",
            sa.Column("duplicate_analysis_id", sa.String(length=36), primary_key=True),
            sa.Column(
                "validation_run_id",
                sa.String(length=36),
                sa.ForeignKey("validation_runs.validation_run_id"),
                nullable=False,
                unique=True,
            ),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("total_record_count", sa.Integer(), nullable=False),
            sa.Column("duplicate_record_count", sa.Integer(), nullable=False),
            sa.Column("duplicate_percentage", sa.Numeric(5, 2), nullable=False),
            sa.Column("threshold_percentage", sa.Numeric(5, 2), nullable=False),
            sa.Column("duplicate_group_count", sa.Integer(), nullable=False),
            sa.Column("issue_summary", sa.Text(), nullable=True),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "duplicate_groups" not in table_names:
        op.create_table(
            "duplicate_groups",
            sa.Column("duplicate_group_id", sa.String(length=36), primary_key=True),
            sa.Column(
                "duplicate_analysis_id",
                sa.String(length=36),
                sa.ForeignKey("duplicate_analysis_results.duplicate_analysis_id"),
                nullable=False,
            ),
            sa.Column("group_key", sa.String(length=255), nullable=False),
            sa.Column("source_record_count", sa.Integer(), nullable=False),
            sa.Column("resolution_status", sa.String(length=32), nullable=False),
            sa.Column("cleaned_record_id", sa.String(length=36), nullable=True),
            sa.Column("resolution_summary", sa.Text(), nullable=True),
        )
    if "review_needed_records" not in table_names:
        op.create_table(
            "review_needed_records",
            sa.Column("review_record_id", sa.String(length=36), primary_key=True),
            sa.Column(
                "validation_run_id",
                sa.String(length=36),
                sa.ForeignKey("validation_runs.validation_run_id"),
                nullable=False,
                unique=True,
            ),
            sa.Column(
                "duplicate_analysis_id",
                sa.String(length=36),
                sa.ForeignKey("duplicate_analysis_results.duplicate_analysis_id"),
                nullable=False,
            ),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)
    if "review_needed_records" in table_names:
        op.drop_table("review_needed_records")
    if "duplicate_groups" in table_names:
        op.drop_table("duplicate_groups")
    if "duplicate_analysis_results" in table_names:
        op.drop_table("duplicate_analysis_results")
    if "validation_results" in table_names:
        op.drop_table("validation_results")
    if "validation_runs" in table_names:
        op.drop_table("validation_runs")

    dataset_version_columns = _column_names(inspector, "dataset_versions")
    if op.get_bind().dialect.name != "sqlite":
        foreign_key_names = _foreign_key_names(inspector, "dataset_versions")
        if "fk_dataset_versions_source_dataset_version_id" in foreign_key_names:
            op.drop_constraint("fk_dataset_versions_source_dataset_version_id", "dataset_versions", type_="foreignkey")
    for column_name in [
        "approved_by_validation_run_id",
        "duplicate_group_count",
        "dataset_kind",
        "source_dataset_version_id",
    ]:
        if column_name in dataset_version_columns:
            op.drop_column("dataset_versions", column_name)
