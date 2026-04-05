"""uc17 public forecast portal

Revision ID: 016_uc17_public_forecast_portal
Revises: 015_fix_legacy_filters_nullable
Create Date: 2026-04-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "016_uc17_public_forecast_portal"
down_revision = "015_fix_legacy_filters_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "public_forecast_portal_requests",
        sa.Column("public_forecast_request_id", sa.String(length=36), primary_key=True),
        sa.Column("approved_forecast_version_id", sa.String(length=36), nullable=True),
        sa.Column("approved_forecast_product", sa.String(length=16), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("portal_status", sa.String(length=16), nullable=False),
        sa.Column("forecast_window_label", sa.String(length=128), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_correlation_id", sa.String(length=255), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
    )
    op.create_table(
        "public_forecast_sanitization_outcomes",
        sa.Column("public_forecast_sanitization_outcome_id", sa.String(length=36), primary_key=True),
        sa.Column("public_forecast_request_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("sanitization_status", sa.String(length=16), nullable=False),
        sa.Column("restricted_detail_detected", sa.Boolean(), nullable=False),
        sa.Column("removed_detail_count", sa.Integer(), nullable=False),
        sa.Column("sanitization_summary", sa.Text(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["public_forecast_request_id"],
            ["public_forecast_portal_requests.public_forecast_request_id"],
        ),
    )
    op.create_table(
        "public_forecast_visualization_payloads",
        sa.Column("public_forecast_payload_id", sa.String(length=36), primary_key=True),
        sa.Column("public_forecast_request_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("approved_forecast_version_id", sa.String(length=36), nullable=False),
        sa.Column("forecast_window_label", sa.String(length=128), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("coverage_status", sa.String(length=16), nullable=False),
        sa.Column("coverage_message", sa.Text(), nullable=True),
        sa.Column("category_summaries_json", sa.Text(), nullable=False),
        sa.Column("prepared_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["public_forecast_request_id"],
            ["public_forecast_portal_requests.public_forecast_request_id"],
        ),
    )
    op.create_table(
        "public_forecast_display_events",
        sa.Column("public_forecast_display_event_id", sa.String(length=36), primary_key=True),
        sa.Column("public_forecast_request_id", sa.String(length=36), nullable=False),
        sa.Column("public_forecast_payload_id", sa.String(length=36), nullable=True),
        sa.Column("display_outcome", sa.String(length=16), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["public_forecast_request_id"],
            ["public_forecast_portal_requests.public_forecast_request_id"],
        ),
        sa.ForeignKeyConstraint(
            ["public_forecast_payload_id"],
            ["public_forecast_visualization_payloads.public_forecast_payload_id"],
        ),
    )


def downgrade() -> None:
    op.drop_table("public_forecast_display_events")
    op.drop_table("public_forecast_visualization_payloads")
    op.drop_table("public_forecast_sanitization_outcomes")
    op.drop_table("public_forecast_portal_requests")
