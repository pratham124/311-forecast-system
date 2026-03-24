"""Canonical cleaned current-record storage."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "004_uc02_cleaned_current_records"
down_revision = "003_uc03_daily_forecast"
branch_labels = None
depends_on = None


def _table_names(inspector: sa.Inspector) -> set[str]:
    return set(inspector.get_table_names())


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = _table_names(inspector)

    if "cleaned_current_records" not in table_names:
        op.create_table(
            "cleaned_current_records",
            sa.Column("service_request_id", sa.String(length=255), primary_key=True),
            sa.Column("source_name", sa.String(length=64), nullable=False),
            sa.Column("requested_at", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=255), nullable=False),
            sa.Column("geography_key", sa.String(length=255), nullable=True),
            sa.Column("record_payload", sa.Text(), nullable=False),
            sa.Column("first_seen_ingestion_run_id", sa.String(length=36), nullable=False),
            sa.Column("last_updated_ingestion_run_id", sa.String(length=36), nullable=False),
            sa.Column("source_dataset_version_id", sa.String(length=36), sa.ForeignKey("dataset_versions.dataset_version_id"), nullable=True),
            sa.Column("approved_by_validation_run_id", sa.String(length=36), nullable=True),
            sa.Column(
                "last_approved_dataset_version_id",
                sa.String(length=36),
                sa.ForeignKey("dataset_versions.dataset_version_id"),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    index_names = _index_names(inspector, "cleaned_current_records")
    if "ix_cleaned_current_records_source_name" not in index_names:
        op.create_index("ix_cleaned_current_records_source_name", "cleaned_current_records", ["source_name"])
    if "ix_cleaned_current_records_requested_at" not in index_names:
        op.create_index("ix_cleaned_current_records_requested_at", "cleaned_current_records", ["requested_at"])
    if "ix_cleaned_current_records_geography_key" not in index_names:
        op.create_index("ix_cleaned_current_records_geography_key", "cleaned_current_records", ["geography_key"])
    if "ix_cleaned_current_records_scope_time" not in index_names:
        op.create_index(
            "ix_cleaned_current_records_scope_time",
            "cleaned_current_records",
            ["source_name", "category", "geography_key", "requested_at"],
        )

    op.execute(
        sa.text(
            """
            INSERT INTO cleaned_current_records (
                service_request_id,
                source_name,
                requested_at,
                category,
                geography_key,
                record_payload,
                first_seen_ingestion_run_id,
                last_updated_ingestion_run_id,
                source_dataset_version_id,
                approved_by_validation_run_id,
                last_approved_dataset_version_id,
                created_at,
                updated_at
            )
            SELECT
                dr.source_record_id,
                dv.source_name,
                dr.requested_at,
                dr.category,
                NULL,
                dr.record_payload,
                dv.ingestion_run_id,
                dv.ingestion_run_id,
                dv.source_dataset_version_id,
                dv.approved_by_validation_run_id,
                dv.dataset_version_id,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            FROM dataset_records dr
            JOIN dataset_versions dv ON dv.dataset_version_id = dr.dataset_version_id
            JOIN current_dataset_markers cdm ON cdm.dataset_version_id = dv.dataset_version_id
            WHERE dv.dataset_kind = 'cleaned'
              AND dv.validation_status = 'approved'
              AND NOT EXISTS (
                  SELECT 1
                  FROM cleaned_current_records ccr
                  WHERE ccr.service_request_id = dr.source_record_id
              )
            """
        )
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)
    if "cleaned_current_records" in table_names:
        op.drop_table("cleaned_current_records")
