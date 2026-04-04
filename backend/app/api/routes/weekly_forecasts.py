from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_forecast_reader, require_forecast_trigger
from app.clients.nager_date_client import NagerDateClient
from app.clients.weather_client import build_weather_client
from app.core.config import get_settings
from app.core.db import get_db_session, get_session_factory
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository
from app.schemas.weekly_forecast import (
    CurrentWeeklyForecastModelRead,
    CurrentWeeklyForecastRead,
    WeeklyForecastModelRunStatusRead,
    WeeklyForecastRunAccepted,
    WeeklyForecastRunStatusRead,
    WeeklyForecastTriggerRequest,
)
from app.services.weekly_forecast_service import WeeklyForecastService
from app.services.weekly_forecast_training_service import WeeklyForecastTrainingService

router = APIRouter(prefix="/api/v1", tags=["weekly-forecast"])


def get_weather_client():
    return build_weather_client()


def get_nager_date_client() -> NagerDateClient:
    return NagerDateClient()


def build_weekly_forecast_training_service(
    session: Session,
    geomet_client: object,
    nager_date_client: NagerDateClient,
) -> WeeklyForecastTrainingService:
    return WeeklyForecastTrainingService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_model_repository=ForecastModelRepository(session),
        settings=get_settings(),
        geomet_client=geomet_client,
        nager_date_client=nager_date_client,
        logger=logging.getLogger("weekly_forecast.training.api"),
    )


def build_weekly_forecast_service(
    session: Session,
    geomet_client: object,
    nager_date_client: NagerDateClient,
) -> WeeklyForecastService:
    return WeeklyForecastService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        weekly_forecast_run_repository=WeeklyForecastRunRepository(session),
        weekly_forecast_repository=WeeklyForecastRepository(session),
        settings=get_settings(),
        geomet_client=geomet_client,
        nager_date_client=nager_date_client,
        forecast_model_repository=ForecastModelRepository(session),
        logger=logging.getLogger("weekly_forecast.api"),
    )


@router.post("/forecast-runs/7-day/trigger", response_model=WeeklyForecastRunAccepted, status_code=202)
def trigger_weekly_forecast(
    background_tasks: BackgroundTasks,
    payload: WeeklyForecastTriggerRequest | None = None,
    session: Session = Depends(get_db_session),
    geomet_client: object = Depends(get_weather_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    _claims: dict = Depends(require_forecast_trigger),
) -> WeeklyForecastRunAccepted:
    if payload is not None and payload.trigger_type != "on_demand":
        raise HTTPException(status_code=422, detail="triggerType must be on_demand")
    service = build_weekly_forecast_service(session, geomet_client, nager_date_client)
    run, should_execute = service.start_run(trigger_type="on_demand")
    session.commit()

    if should_execute:
        def execute() -> None:
            background_session = get_session_factory()()
            try:
                background_service = build_weekly_forecast_service(background_session, geomet_client, nager_date_client)
                background_service.execute_run(run.weekly_forecast_run_id)
                background_session.commit()
            finally:
                background_session.close()

        background_tasks.add_task(execute)

    return WeeklyForecastRunAccepted(weeklyForecastRunId=run.weekly_forecast_run_id, status="running")


@router.get("/forecast-runs/7-day/{weekly_forecast_run_id}", response_model=WeeklyForecastRunStatusRead)
def get_weekly_forecast_run(
    weekly_forecast_run_id: str,
    session: Session = Depends(get_db_session),
    geomet_client: object = Depends(get_weather_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    _claims: dict = Depends(require_forecast_reader),
) -> WeeklyForecastRunStatusRead:
    service = build_weekly_forecast_service(session, geomet_client, nager_date_client)
    return service.get_run_status(weekly_forecast_run_id)


@router.get("/forecast-model-runs/7-day/{forecast_model_run_id}", response_model=WeeklyForecastModelRunStatusRead)
def get_weekly_forecast_model_run(
    forecast_model_run_id: str,
    session: Session = Depends(get_db_session),
    geomet_client: object = Depends(get_weather_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    _claims: dict = Depends(require_forecast_reader),
) -> WeeklyForecastModelRunStatusRead:
    service = build_weekly_forecast_training_service(session, geomet_client, nager_date_client)
    return service.get_run_status(forecast_model_run_id)


@router.get("/forecast-models/current-weekly", response_model=CurrentWeeklyForecastModelRead)
def get_current_weekly_forecast_model(
    session: Session = Depends(get_db_session),
    geomet_client: object = Depends(get_weather_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    _claims: dict = Depends(require_forecast_reader),
) -> CurrentWeeklyForecastModelRead:
    service = build_weekly_forecast_training_service(session, geomet_client, nager_date_client)
    return service.get_current_model()


@router.get("/forecasts/current-weekly", response_model=CurrentWeeklyForecastRead)
def get_current_weekly_forecast(
    session: Session = Depends(get_db_session),
    geomet_client: object = Depends(get_weather_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    _claims: dict = Depends(require_forecast_reader),
) -> CurrentWeeklyForecastRead:
    service = build_weekly_forecast_service(session, geomet_client, nager_date_client)
    return service.get_current_forecast()
