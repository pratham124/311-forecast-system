from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_forecast_alert_reader, require_forecast_alert_trigger
from app.clients.notification_service import NotificationDeliveryClient as _NotificationDeliveryClient
from app.core.config import get_settings
from app.core.db import get_db_session, get_session_factory
from app.models import ThresholdConfiguration
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.forecast_alerts import (
    ThresholdAlertEvent,
    ThresholdAlertEventListResponse,
    ThresholdConfigurationListResponse,
    ThresholdConfigurationRead,
    ThresholdConfigurationUpdate,
    ThresholdConfigurationWrite,
    ThresholdEvaluationTriggerRequest,
    ThresholdEvaluationTriggerResponse,
    ServiceCategoryListResponse,
)
from app.services.alert_review_service import AlertReviewService
from app.services.threshold_alert_trigger_service import run_threshold_alert_evaluation

router = APIRouter(prefix="/api/v1/forecast-alerts", tags=["forecast-alerts"])

logger = logging.getLogger("forecast_alerts.api")
NotificationDeliveryClient = _NotificationDeliveryClient


def build_alert_review_service(session: Session) -> AlertReviewService:
    return AlertReviewService(NotificationEventRepository(session))


def serialize_threshold_configuration(configuration: ThresholdConfiguration, notification_channels: list[str]) -> ThresholdConfigurationRead:
    return ThresholdConfigurationRead(
        thresholdConfigurationId=configuration.threshold_configuration_id,
        serviceCategory=configuration.service_category,
        forecastWindowType=configuration.forecast_window_type,
        thresholdValue=float(configuration.threshold_value),
        notificationChannels=notification_channels,
        operationalManagerId=configuration.operational_manager_id,
        status=configuration.status,
        effectiveFrom=configuration.effective_from,
        effectiveTo=configuration.effective_to,
    )


@router.post("/evaluations", response_model=ThresholdEvaluationTriggerResponse, status_code=202)
def trigger_threshold_evaluation(
    payload: ThresholdEvaluationTriggerRequest,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_trigger),
) -> ThresholdEvaluationTriggerResponse:
    run = run_threshold_alert_evaluation(
        session,
        forecast_reference_id=payload.forecast_reference_id,
        forecast_product=payload.forecast_product,
        trigger_source=payload.trigger_source,
    )
    return ThresholdEvaluationTriggerResponse(
        thresholdEvaluationRunId=run.threshold_evaluation_run_id,
        status="accepted",
        acceptedAt=run.started_at,
    )


@router.get("/thresholds", response_model=ThresholdConfigurationListResponse)
def list_threshold_configurations(
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_reader),
) -> ThresholdConfigurationListResponse:
    repository = ThresholdConfigurationRepository(session)
    return ThresholdConfigurationListResponse(
        items=[
            serialize_threshold_configuration(item.configuration, item.notification_channels)
            for item in repository.list_configurations(include_inactive=True)
        ]
    )


@router.post("/thresholds", response_model=ThresholdConfigurationRead, status_code=201)
def create_threshold_configuration(
    background_tasks: BackgroundTasks,
    payload: ThresholdConfigurationWrite,
    session: Session = Depends(get_db_session),
    claims: dict = Depends(require_forecast_alert_trigger),
) -> ThresholdConfigurationRead:
    operational_manager_id = str(claims.get("sub") or "")
    configuration = ThresholdConfigurationRepository(session).create_configuration(
        service_category=payload.service_category,
        forecast_window_type=payload.forecast_window_type,
        threshold_value=payload.threshold_value,
        notification_channels=payload.notification_channels,
        operational_manager_id=operational_manager_id,
    )
    _schedule_recheck(background_tasks, payload.forecast_window_type, trigger_source="manual_replay", service_category=payload.service_category)
    return serialize_threshold_configuration(
        configuration,
        payload.notification_channels,
    )


@router.patch("/thresholds/{threshold_configuration_id}", response_model=ThresholdConfigurationRead)
def update_threshold_configuration(
    threshold_configuration_id: str,
    background_tasks: BackgroundTasks,
    payload: ThresholdConfigurationUpdate,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_trigger),
) -> ThresholdConfigurationRead:
    repository = ThresholdConfigurationRepository(session)
    configuration = repository.update_configuration(
        threshold_configuration_id,
        service_category=payload.service_category,
        forecast_window_type=payload.forecast_window_type,
        threshold_value=payload.threshold_value,
        notification_channels=payload.notification_channels,
    )
    if configuration is None:
        raise HTTPException(status_code=404, detail="Threshold configuration not found")
    _schedule_recheck(background_tasks, payload.forecast_window_type, trigger_source="manual_replay", service_category=payload.service_category)
    return serialize_threshold_configuration(configuration, payload.notification_channels)


@router.delete("/thresholds/{threshold_configuration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_threshold_configuration(
    threshold_configuration_id: str,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_trigger),
) -> Response:
    configuration = ThresholdConfigurationRepository(session).deactivate_configuration(threshold_configuration_id)
    if configuration is None:
        raise HTTPException(status_code=404, detail="Threshold configuration not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _schedule_recheck(
    background_tasks: BackgroundTasks,
    forecast_window_type: str,
    *,
    trigger_source: str,
    service_category: str | None = None,
) -> None:
    settings = get_settings()

    def execute() -> None:
        background_session = get_session_factory()()
        try:
            if forecast_window_type == "hourly":
                marker = ForecastRepository(background_session).get_current_marker(settings.forecast_product_name)
                if marker is None:
                    return
                run_threshold_alert_evaluation(
                    background_session,
                    forecast_reference_id=marker.forecast_version_id,
                    forecast_product="daily",
                    trigger_source=trigger_source,
                    service_category=service_category,
                )
            else:
                marker = WeeklyForecastRepository(background_session).get_current_marker(settings.weekly_forecast_product_name)
                if marker is None:
                    return
                run_threshold_alert_evaluation(
                    background_session,
                    forecast_reference_id=marker.weekly_forecast_version_id,
                    forecast_product="weekly",
                    trigger_source=trigger_source,
                    service_category=service_category,
                )
            background_session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("threshold alert recheck failed for forecast_window_type=%s: %s", forecast_window_type, exc)
            background_session.rollback()
        finally:
            background_session.close()

    background_tasks.add_task(execute)


@router.get("/service-categories", response_model=ServiceCategoryListResponse)
def list_threshold_service_categories(
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_reader),
) -> ServiceCategoryListResponse:
    settings = get_settings()
    forecast_repository = ForecastRepository(session)
    weekly_forecast_repository = WeeklyForecastRepository(session)
    categories = {
        *forecast_repository.list_current_service_categories(settings.forecast_product_name),
        *weekly_forecast_repository.list_current_service_categories(settings.weekly_forecast_product_name),
    }
    return ServiceCategoryListResponse(items=sorted(categories))


@router.get("/events", response_model=ThresholdAlertEventListResponse)
def list_threshold_alert_events(
    service_category: str | None = Query(default=None, alias="serviceCategory"),
    overall_delivery_status: str | None = Query(default=None, alias="overallDeliveryStatus"),
    forecast_window_type: str | None = Query(default=None, alias="forecastWindowType"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_reader),
) -> ThresholdAlertEventListResponse:
    return build_alert_review_service(session).list_events(
        service_category=service_category,
        overall_delivery_status=overall_delivery_status,
        forecast_window_type=forecast_window_type,
    )


@router.get("/events/{notification_event_id}", response_model=ThresholdAlertEvent)
def get_threshold_alert_event(
    notification_event_id: str,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_alert_reader),
) -> ThresholdAlertEvent:
    return build_alert_review_service(session).get_event(notification_event_id)
