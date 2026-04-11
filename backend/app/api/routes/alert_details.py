from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_alert_detail_reader
from app.clients.nager_date_client import NagerDateClient
from app.clients.weather_client import build_weather_client
from app.core.config import get_settings
from app.core.db import get_db_session
from app.repositories.alert_detail_repository import AlertDetailRepository
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.notification_event_repository import NotificationEventRepository
from app.repositories.surge_evaluation_repository import SurgeEvaluationRepository
from app.repositories.surge_notification_event_repository import SurgeNotificationEventRepository
from app.repositories.threshold_evaluation_repository import ThresholdEvaluationRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.alert_details import AlertDetailRead, AlertDetailRenderEvent, AlertDetailRenderEventResponse, AlertSource
from app.services.alert_detail_service import AlertDetailService
from app.services.forecast_training_service import ForecastTrainingService
from app.services.weekly_forecast_training_service import WeeklyForecastTrainingService

router = APIRouter(prefix="/api/v1/alert-details", tags=["alert-details"])


def get_weather_client():
    return build_weather_client()


def get_nager_date_client() -> NagerDateClient:
    return NagerDateClient()


def build_alert_detail_service(session: Session, geomet_client: object, nager_date_client: NagerDateClient) -> AlertDetailService:
    settings = get_settings()
    cleaned_dataset_repository = CleanedDatasetRepository(session)
    forecast_model_repository = ForecastModelRepository(session)
    return AlertDetailService(
        alert_detail_repository=AlertDetailRepository(session),
        notification_event_repository=NotificationEventRepository(session),
        threshold_evaluation_repository=ThresholdEvaluationRepository(session),
        surge_notification_event_repository=SurgeNotificationEventRepository(session),
        surge_evaluation_repository=SurgeEvaluationRepository(session),
        forecast_repository=ForecastRepository(session),
        weekly_forecast_repository=WeeklyForecastRepository(session),
        cleaned_dataset_repository=cleaned_dataset_repository,
        forecast_model_repository=forecast_model_repository,
        forecast_training_service=ForecastTrainingService(
            cleaned_dataset_repository=cleaned_dataset_repository,
            forecast_model_repository=forecast_model_repository,
            geomet_client=geomet_client,
            nager_date_client=nager_date_client,
            settings=settings,
            logger=logging.getLogger("alert_details.forecast_training"),
        ),
        weekly_forecast_training_service=WeeklyForecastTrainingService(
            cleaned_dataset_repository=cleaned_dataset_repository,
            forecast_model_repository=forecast_model_repository,
            geomet_client=geomet_client,
            nager_date_client=nager_date_client,
            settings=settings,
            logger=logging.getLogger("alert_details.weekly_forecast_training"),
        ),
        geomet_client=geomet_client,
        nager_date_client=nager_date_client,
        settings=settings,
        logger=logging.getLogger("alert_details.api"),
    )


@router.get("/{alert_source}/{alert_id}", response_model=AlertDetailRead)
def get_alert_detail(
    alert_source: AlertSource,
    alert_id: str,
    session: Session = Depends(get_db_session),
    geomet_client: object = Depends(get_weather_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    claims: dict = Depends(require_alert_detail_reader),
) -> AlertDetailRead:
    return build_alert_detail_service(session, geomet_client, nager_date_client).get_alert_detail(
        alert_source=alert_source,
        alert_id=alert_id,
        claims=claims,
    )


@router.post("/{alert_detail_load_id}/render-events", response_model=AlertDetailRenderEventResponse, status_code=202)
def record_alert_detail_render_event(
    alert_detail_load_id: str,
    payload: AlertDetailRenderEvent,
    session: Session = Depends(get_db_session),
    geomet_client: object = Depends(get_weather_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    claims: dict = Depends(require_alert_detail_reader),
) -> AlertDetailRenderEventResponse:
    return build_alert_detail_service(session, geomet_client, nager_date_client).record_render_event(
        alert_detail_load_id=alert_detail_load_id,
        payload=payload,
        claims=claims,
    )
