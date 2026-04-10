from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ReportType = Literal["Feedback", "Bug Report"]
SubmitterKind = Literal["anonymous", "authenticated"]
ProcessingStatus = Literal["accepted", "deferred_for_retry", "forwarded", "forward_failed"]
TriageStatus = Literal["new", "in_review", "resolved", "closed"]
VisibilityStatus = Literal["visible", "hidden", "archived"]
UserOutcome = Literal["accepted", "accepted_with_delay", "failed"]

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class FeedbackSubmissionCreateRequest(BaseModel):
    report_type: ReportType = Field(alias="reportType")
    description: str = Field(min_length=1, max_length=5000)
    contact_email: str | None = Field(default=None, alias="contactEmail", max_length=320)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Description is required")
        return normalized

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if not _EMAIL_PATTERN.match(normalized):
            raise ValueError("Contact email must be a valid email address")
        return normalized


class ValidationErrorDetail(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class SubmissionStatusEventRead(BaseModel):
    event_type: ProcessingStatus = Field(alias="eventType")
    event_reason: str | None = Field(default=None, alias="eventReason")
    recorded_at: datetime = Field(alias="recordedAt")
    correlation_id: str | None = Field(default=None, alias="correlationId")

    model_config = ConfigDict(populate_by_name=True)


class FeedbackSubmissionCreateResponse(BaseModel):
    feedback_submission_id: str = Field(alias="feedbackSubmissionId")
    report_type: ReportType = Field(alias="reportType")
    processing_status: ProcessingStatus = Field(alias="processingStatus")
    accepted_at: datetime = Field(alias="acceptedAt")
    user_outcome: UserOutcome = Field(alias="userOutcome")
    status_message: str = Field(alias="statusMessage")

    model_config = ConfigDict(populate_by_name=True)


class FeedbackSubmissionSummary(BaseModel):
    feedback_submission_id: str = Field(alias="feedbackSubmissionId")
    report_type: ReportType = Field(alias="reportType")
    submitter_kind: SubmitterKind = Field(alias="submitterKind")
    processing_status: ProcessingStatus = Field(alias="processingStatus")
    submitted_at: datetime = Field(alias="submittedAt")
    triage_status: TriageStatus = Field(alias="triageStatus")

    model_config = ConfigDict(populate_by_name=True)


class FeedbackSubmissionListResponse(BaseModel):
    items: list[FeedbackSubmissionSummary]

    model_config = ConfigDict(populate_by_name=True)


class FeedbackSubmissionDetail(BaseModel):
    feedback_submission_id: str = Field(alias="feedbackSubmissionId")
    report_type: ReportType = Field(alias="reportType")
    description: str
    contact_email: str | None = Field(default=None, alias="contactEmail")
    submitter_kind: SubmitterKind = Field(alias="submitterKind")
    processing_status: ProcessingStatus = Field(alias="processingStatus")
    external_reference: str | None = Field(default=None, alias="externalReference")
    submitted_at: datetime = Field(alias="submittedAt")
    triage_status: TriageStatus = Field(alias="triageStatus")
    visibility_status: VisibilityStatus = Field(alias="visibilityStatus")
    status_events: list[SubmissionStatusEventRead] = Field(alias="statusEvents")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_status_events(self):
        if not self.status_events:
            raise ValueError("Feedback submission detail requires at least one status event")
        return self
