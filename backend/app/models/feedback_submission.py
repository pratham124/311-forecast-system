from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class FeedbackSubmission(Base):
    __tablename__ = "feedback_submissions"

    feedback_submission_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    submitter_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    submitter_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_accounts.user_account_id"),
        nullable=True,
    )
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="accepted")
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_status_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class SubmissionStatusEvent(Base):
    __tablename__ = "submission_status_events"

    submission_status_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    feedback_submission_id: Mapped[str] = mapped_column(
        ForeignKey("feedback_submissions.feedback_submission_id"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ReviewQueueRecord(Base):
    __tablename__ = "review_queue_records"

    review_queue_record_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    feedback_submission_id: Mapped[str] = mapped_column(
        ForeignKey("feedback_submissions.feedback_submission_id"),
        nullable=False,
        unique=True,
    )
    visibility_status: Mapped[str] = mapped_column(String(16), nullable=False, default="visible")
    triage_status: Mapped[str] = mapped_column(String(16), nullable=False, default="new")
    assigned_reviewer_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_accounts.user_account_id"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
