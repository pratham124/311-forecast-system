"""uc19 feedback reporting

Revision ID: 018_uc19_feedback_reporting
Revises: 017_uc10_threshold_alerts
Create Date: 2026-04-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "018_uc19_feedback_reporting"
down_revision = "017_uc10_threshold_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback_submissions",
        sa.Column("feedback_submission_id", sa.String(length=36), primary_key=True),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("submitter_kind", sa.String(length=32), nullable=False),
        sa.Column("submitter_user_id", sa.String(length=36), nullable=True),
        sa.Column("processing_status", sa.String(length=32), nullable=False),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_status_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["submitter_user_id"], ["user_accounts.user_account_id"]),
    )
    op.create_index(
        "ix_feedback_submissions_processing_status",
        "feedback_submissions",
        ["processing_status"],
        unique=False,
    )
    op.create_index(
        "ix_feedback_submissions_submitted_at",
        "feedback_submissions",
        ["submitted_at"],
        unique=False,
    )

    op.create_table(
        "submission_status_events",
        sa.Column("submission_status_event_id", sa.String(length=36), primary_key=True),
        sa.Column("feedback_submission_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_reason", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["feedback_submission_id"],
            ["feedback_submissions.feedback_submission_id"],
        ),
    )
    op.create_index(
        "ix_submission_status_events_feedback_submission_id",
        "submission_status_events",
        ["feedback_submission_id"],
        unique=False,
    )
    op.create_index(
        "ix_submission_status_events_recorded_at",
        "submission_status_events",
        ["recorded_at"],
        unique=False,
    )

    op.create_table(
        "review_queue_records",
        sa.Column("review_queue_record_id", sa.String(length=36), primary_key=True),
        sa.Column("feedback_submission_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("visibility_status", sa.String(length=16), nullable=False),
        sa.Column("triage_status", sa.String(length=16), nullable=False),
        sa.Column("assigned_reviewer_user_id", sa.String(length=36), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["feedback_submission_id"],
            ["feedback_submissions.feedback_submission_id"],
        ),
        sa.ForeignKeyConstraint(
            ["assigned_reviewer_user_id"],
            ["user_accounts.user_account_id"],
        ),
    )
    op.create_index(
        "ix_review_queue_records_visibility_status",
        "review_queue_records",
        ["visibility_status"],
        unique=False,
    )
    op.create_index(
        "ix_review_queue_records_triage_status",
        "review_queue_records",
        ["triage_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_review_queue_records_triage_status", table_name="review_queue_records")
    op.drop_index("ix_review_queue_records_visibility_status", table_name="review_queue_records")
    op.drop_table("review_queue_records")
    op.drop_index("ix_submission_status_events_recorded_at", table_name="submission_status_events")
    op.drop_index("ix_submission_status_events_feedback_submission_id", table_name="submission_status_events")
    op.drop_table("submission_status_events")
    op.drop_index("ix_feedback_submissions_submitted_at", table_name="feedback_submissions")
    op.drop_index("ix_feedback_submissions_processing_status", table_name="feedback_submissions")
    op.drop_table("feedback_submissions")
