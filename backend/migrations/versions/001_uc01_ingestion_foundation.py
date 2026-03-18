"""UC-01 ingestion foundation schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001_uc01_ingestion_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("run_id", sa.String(length=36), primary_key=True),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("result_type", sa.String(length=32), nullable=True),
        sa.Column("source_window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cursor_used", sa.String(length=255), nullable=True),
        sa.Column("cursor_advanced", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("records_received", sa.Integer(), nullable=True),
        sa.Column("candidate_dataset_id", sa.String(length=36), nullable=True),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
    )
    op.create_table(
        "successful_pull_cursors",
        sa.Column("source_name", sa.String(length=64), primary_key=True),
        sa.Column("cursor_value", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_run_id", sa.String(length=36), nullable=False),
    )
    op.create_table(
        "candidate_datasets",
        sa.Column("candidate_dataset_id", sa.String(length=36), primary_key=True),
        sa.Column("ingestion_run_id", sa.String(length=36), sa.ForeignKey("ingestion_runs.run_id")),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("validation_status", sa.String(length=16), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "dataset_versions",
        sa.Column("dataset_version_id", sa.String(length=36), primary_key=True),
        sa.Column("source_name", sa.String(length=64), nullable=False),
        sa.Column("ingestion_run_id", sa.String(length=36), sa.ForeignKey("ingestion_runs.run_id")),
        sa.Column("candidate_dataset_id", sa.String(length=36), sa.ForeignKey("candidate_datasets.candidate_dataset_id")),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("validation_status", sa.String(length=16), nullable=False),
        sa.Column("storage_status", sa.String(length=16), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "dataset_records",
        sa.Column("record_id", sa.String(length=36), primary_key=True),
        sa.Column("dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id")),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("requested_at", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=255), nullable=False),
        sa.Column("record_payload", sa.Text(), nullable=False),
    )
    op.create_table(
        "current_dataset_markers",
        sa.Column("source_name", sa.String(length=64), primary_key=True),
        sa.Column("dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_run_id", sa.String(length=36), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
    )
    op.create_table(
        "failure_notification_records",
        sa.Column("notification_id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("ingestion_runs.run_id")),
        sa.Column("failure_category", sa.String(length=32), nullable=False),
        sa.Column("run_status", sa.String(length=16), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("failure_notification_records")
    op.drop_table("current_dataset_markers")
    op.drop_table("dataset_records")
    op.drop_table("dataset_versions")
    op.drop_table("candidate_datasets")
    op.drop_table("successful_pull_cursors")
    op.drop_table("ingestion_runs")
