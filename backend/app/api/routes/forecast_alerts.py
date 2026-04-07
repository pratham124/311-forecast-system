from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies.auth import require_forecast_alert_reader, require_forecast_alert_trigger
from app.core.db import get_db_session
from app.pipelines.threshold_alert_evaluation_pipeline import ThresholdAlertEvaluationPipeline
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.threshold_evaluation_repository import ThresholdEvaluationRepository
from app.repositories.threshold_state_repository import ThresholdStateRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.forecast_alerts import (
    ThresholdAlertEventListResponse,
    ThresholdAlertEventRead,
    ThresholdConfigurationListResponse,
    ThresholdConfigurationRead,
    ThresholdConfigurationUpdateRequest,
    ThresholdEvaluationTriggerRequest,
    ThresholdEvaluationTriggerResponse,
)
from app.services.alert_review_service import AlertReviewService
from app.services.forecast_scope_service import ForecastScopeService

router = APIRouter(prefix="/api/v1/forecast-alerts", tags=["forecast-alerts"])


def _is_missing_uc10_table(error: SQLAlchemyError) -> bool:
    message = str(error).lower()
    is_missing_relation = "relation" in message and "does not exist" in message
    has_uc10_relation_name = any(
        name in message
        for name in (
            "threshold_configurations",
            "threshold_evaluation_runs",
            "threshold_scope_evaluations",
            "threshold_states",
            "notification_events",
            "notification_channel_attempts",
        )
    )
    return (
        "no such table" in message
        or (is_missing_relation and has_uc10_relation_name)
    )


def build_pipeline(session: Session) -> ThresholdAlertEvaluationPipeline:
    return ThresholdAlertEvaluationPipeline(
        forecast_scope_service=ForecastScopeService(
            forecast_repository=ForecastRepository(session),
            weekly_forecast_repository=WeeklyForecastRepository(session),
        ),
        threshold_configuration_repository=ThresholdConfigurationRepository(session),
        threshold_evaluation_repository=ThresholdEvaluationRepository(session),
        threshold_state_repository=ThresholdStateRepository(session),
        notification_event_repository=NotificationEventRepository(session),
        logger=logging.getLogger("forecast_alert.pipeline"),
    )


def build_alert_review_service(session: Session) -> AlertReviewService:
    return AlertReviewService(NotificationEventRepository(session))


@router.post("/evaluations", response_model=ThresholdEvaluationTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_threshold_evaluation(
    payload: ThresholdEvaluationTriggerRequest,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_trigger),
) -> ThresholdEvaluationTriggerResponse:
    pipeline = build_pipeline(session)
    run_id = pipeline.evaluate(
        forecast_reference_id=payload.forecast_reference_id,
        forecast_product=payload.forecast_product,
        trigger_source=payload.trigger_source,
    )
    session.commit()
    return ThresholdEvaluationTriggerResponse(
        thresholdEvaluationRunId=run_id,
        status="accepted",
        acceptedAt=datetime.now(timezone.utc),
    )


@router.get("/events", response_model=ThresholdAlertEventListResponse)
def list_threshold_alert_events(
    service_category: str | None = Query(default=None, alias="serviceCategory"),
    geography_value: str | None = Query(default=None, alias="geographyValue"),
    overall_delivery_status: str | None = Query(default=None, alias="overallDeliveryStatus"),
    forecast_window_type: str | None = Query(default=None, alias="forecastWindowType"),
    forecast_window_start: datetime | None = Query(default=None, alias="forecastWindowStart"),
    forecast_window_end: datetime | None = Query(default=None, alias="forecastWindowEnd"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_reader),
) -> ThresholdAlertEventListResponse:
    service = build_alert_review_service(session)
    try:
        items = service.list_events(
            service_category=service_category,
            geography_value=geography_value,
            overall_delivery_status=overall_delivery_status,
            forecast_window_type=forecast_window_type,
            forecast_window_start=forecast_window_start,
            forecast_window_end=forecast_window_end,
        )
    except SQLAlchemyError as exc:
        if _is_missing_uc10_table(exc):
            return ThresholdAlertEventListResponse(items=[])
        raise
    return ThresholdAlertEventListResponse(items=items)


@router.get("/events/{notification_event_id}", response_model=ThresholdAlertEventRead)
def get_threshold_alert_event(
    notification_event_id: str,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_reader),
) -> ThresholdAlertEventRead:
    service = build_alert_review_service(session)
    event = service.get_event(notification_event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Alert event not found")
    return event


@router.put("/threshold-configurations", response_model=ThresholdConfigurationRead)
def update_threshold_configuration(
    payload: ThresholdConfigurationUpdateRequest,
    session: Session = Depends(get_db_session),
    claims: dict = Depends(require_forecast_alert_trigger),
) -> ThresholdConfigurationRead:
    if payload.threshold_value <= 0:
        raise HTTPException(status_code=422, detail="thresholdValue must be greater than zero")
    manager_id = str(claims.get("sub") or claims.get("email") or "operational-manager")
    repository = ThresholdConfigurationRepository(session)
    try:
        configuration = repository.set_global_threshold(
            threshold_value=payload.threshold_value,
            operational_manager_id=manager_id,
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        if _is_missing_uc10_table(exc):
            logging.getLogger("forecast_alert.api").warning(
                "threshold configuration update blocked: uc10 tables missing; error=%s",
                exc,
            )
            raise HTTPException(
                status_code=503,
                detail="Threshold alert tables are not initialized. Run database migrations and retry.",
            ) from exc
        logging.getLogger("forecast_alert.api").exception(
            "threshold configuration update failed due to database error"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update threshold configuration.",
        ) from exc
    return ThresholdConfigurationRead(
        thresholdConfigurationId=configuration.threshold_configuration_id,
        serviceCategory="ALL",
        forecastWindowType=configuration.forecast_window_type,
        thresholdValue=float(configuration.threshold_value),
        operationalManagerId=configuration.operational_manager_id,
        status=configuration.status,
        effectiveFrom=configuration.effective_from,
        effectiveTo=configuration.effective_to,
    )


@router.get("/threshold-configurations", response_model=ThresholdConfigurationListResponse)
def list_threshold_configurations(
    forecast_window_type: str = Query(default="global", alias="forecastWindowType"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_reader),
) -> ThresholdConfigurationListResponse:
    repository = ThresholdConfigurationRepository(session)
    try:
        rows = repository.list_active_category_thresholds(forecast_window_type=forecast_window_type)
    except SQLAlchemyError as exc:
        if _is_missing_uc10_table(exc):
            return ThresholdConfigurationListResponse(items=[])
        raise
    items = [
        ThresholdConfigurationRead(
            thresholdConfigurationId=row.threshold_configuration_id,
            serviceCategory="ALL",
            forecastWindowType=row.forecast_window_type,
            thresholdValue=float(row.threshold_value),
            operationalManagerId=row.operational_manager_id,
            status=row.status,
            effectiveFrom=row.effective_from,
            effectiveTo=row.effective_to,
        )
        for row in rows
    ]
    return ThresholdConfigurationListResponse(items=items)
