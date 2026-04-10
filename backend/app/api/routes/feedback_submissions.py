from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_feedback_review_reader
from app.core.auth import get_optional_claims
from app.core.db import get_db_session
from app.repositories.feedback_submission_repository import FeedbackSubmissionRepository
from app.schemas.feedback_submissions import (
    FeedbackSubmissionCreateRequest,
    FeedbackSubmissionCreateResponse,
    FeedbackSubmissionDetail,
    FeedbackSubmissionListResponse,
)
from app.services.feedback_forwarding_service import FeedbackForwardingService
from app.services.feedback_intake_service import FeedbackIntakeService
from app.services.feedback_review_service import FeedbackReviewService


router = APIRouter(prefix="/api/v1/feedback-submissions", tags=["feedback-submissions"])


def build_feedback_intake_service(session: Session) -> FeedbackIntakeService:
    repository = FeedbackSubmissionRepository(session)
    return FeedbackIntakeService(
        repository=repository,
        forwarding_service=FeedbackForwardingService(),
        logger=logging.getLogger("feedback.api"),
    )


def build_feedback_review_service(session: Session) -> FeedbackReviewService:
    return FeedbackReviewService(FeedbackSubmissionRepository(session))


@router.post("", response_model=FeedbackSubmissionCreateResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback_submission(
    payload: FeedbackSubmissionCreateRequest,
    x_client_correlation_id: str | None = Header(default=None, alias="X-Client-Correlation-Id"),
    claims: dict | None = Depends(get_optional_claims),
    session: Session = Depends(get_db_session),
) -> FeedbackSubmissionCreateResponse:
    try:
        result = build_feedback_intake_service(session).submit_feedback(
            payload,
            claims=claims,
            correlation_id=x_client_correlation_id,
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logging.getLogger("feedback.api").exception("feedback submission storage failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback submission could not be fully recorded. Please try again.",
        ) from exc
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        logging.getLogger("feedback.api").exception("feedback submission failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Feedback submission failed. Please try again.",
        ) from exc
    return result.response


@router.get("", response_model=FeedbackSubmissionListResponse)
def list_feedback_submissions(
    report_type: str | None = Query(default=None, alias="reportType"),
    processing_status: str | None = Query(default=None, alias="processingStatus"),
    submitted_after: datetime | None = Query(default=None, alias="submittedAfter"),
    submitted_before: datetime | None = Query(default=None, alias="submittedBefore"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_feedback_review_reader),
) -> FeedbackSubmissionListResponse:
    service = build_feedback_review_service(session)
    items = service.list_submissions(
        report_type=report_type,
        processing_status=processing_status,
        submitted_after=submitted_after,
        submitted_before=submitted_before,
    )
    return FeedbackSubmissionListResponse(items=items)


@router.get("/{feedback_submission_id}", response_model=FeedbackSubmissionDetail)
def get_feedback_submission(
    feedback_submission_id: str,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_feedback_review_reader),
) -> FeedbackSubmissionDetail:
    submission = build_feedback_review_service(session).get_submission(feedback_submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback submission not found")
    return submission
