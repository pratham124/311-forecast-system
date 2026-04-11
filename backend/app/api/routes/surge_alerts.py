from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_surge_alert_reader, require_surge_alert_trigger
from app.core.db import get_db_session
from app.repositories.surge_evaluation_repository import SurgeEvaluationRepository
from app.repositories.surge_notification_event_repository import SurgeNotificationEventRepository
from app.schemas.surge_alerts import (
    SurgeAlertEvent,
    SurgeAlertEventListResponse,
    SurgeEvaluationRunDetail,
    SurgeEvaluationRunListResponse,
    SurgeEvaluationTriggerRequest,
    SurgeEvaluationTriggerResponse,
)
from app.services.surge_alert_review_service import SurgeAlertReviewService
from app.services.surge_alert_trigger_service import run_surge_alert_evaluation_for_forecast

router = APIRouter(prefix="/api/v1/surge-alerts", tags=["surge-alerts"])


def build_review_service(session: Session) -> SurgeAlertReviewService:
    return SurgeAlertReviewService(
        evaluation_repository=SurgeEvaluationRepository(session),
        event_repository=SurgeNotificationEventRepository(session),
    )


@router.post("/evaluations", response_model=SurgeEvaluationTriggerResponse, status_code=202)
def trigger_surge_evaluation(
    payload: SurgeEvaluationTriggerRequest,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_surge_alert_trigger),
) -> SurgeEvaluationTriggerResponse:
    run = run_surge_alert_evaluation_for_forecast(
        session,
        forecast_version_id=payload.forecast_reference_id,
        trigger_source=payload.trigger_source,
    )
    return SurgeEvaluationTriggerResponse(
        surgeEvaluationRunId=run.surge_evaluation_run_id,
        status="accepted",
        acceptedAt=run.started_at,
    )


@router.get("/evaluations", response_model=SurgeEvaluationRunListResponse)
def list_surge_evaluations(
    ingestion_run_id: str | None = Query(default=None, alias="ingestionRunId"),
    run_status: str | None = Query(default=None, alias="status"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_surge_alert_reader),
) -> SurgeEvaluationRunListResponse:
    return build_review_service(session).list_evaluations(ingestion_run_id=ingestion_run_id, status=run_status)


@router.get("/evaluations/{surge_evaluation_run_id}", response_model=SurgeEvaluationRunDetail)
def get_surge_evaluation(
    surge_evaluation_run_id: str,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_surge_alert_reader),
) -> SurgeEvaluationRunDetail:
    return build_review_service(session).get_evaluation(surge_evaluation_run_id)


@router.get("/events", response_model=SurgeAlertEventListResponse)
def list_surge_events(
    service_category: str | None = Query(default=None, alias="serviceCategory"),
    overall_delivery_status: str | None = Query(default=None, alias="overallDeliveryStatus"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_surge_alert_reader),
) -> SurgeAlertEventListResponse:
    return build_review_service(session).list_events(
        service_category=service_category,
        overall_delivery_status=overall_delivery_status,
    )


@router.get("/events/{surge_notification_event_id}", response_model=SurgeAlertEvent)
def get_surge_event(
    surge_notification_event_id: str,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_surge_alert_reader),
) -> SurgeAlertEvent:
    return build_review_service(session).get_event(surge_notification_event_id)
