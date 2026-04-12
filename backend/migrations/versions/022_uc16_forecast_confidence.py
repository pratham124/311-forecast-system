"""uc16 forecast confidence

Revision ID: 022_uc16_forecast_confidence
Revises: 021_uc12_alert_details
Create Date: 2026-04-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "022_uc16_forecast_confidence"
down_revision = "021_uc12_alert_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("visualization_load_records") as batch_op:
        batch_op.add_column(sa.Column("confidence_assessment_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("confidence_indicator_state", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("confidence_reason_categories_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("confidence_supporting_signals_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("confidence_message", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("confidence_signal_resolution_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("confidence_render_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("confidence_render_reported_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("confidence_render_failure_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("visualization_load_records") as batch_op:
        batch_op.drop_column("confidence_render_failure_reason")
        batch_op.drop_column("confidence_render_reported_at")
        batch_op.drop_column("confidence_render_status")
        batch_op.drop_column("confidence_signal_resolution_status")
        batch_op.drop_column("confidence_message")
        batch_op.drop_column("confidence_supporting_signals_json")
        batch_op.drop_column("confidence_reason_categories_json")
        batch_op.drop_column("confidence_indicator_state")
        batch_op.drop_column("confidence_assessment_status")
