from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_forecast_reader, require_forecast_trigger
from app.clients.geomet_client import GeoMetClient
from app.clients.nager_date_client import NagerDateClient
from app.core.config import get_settings
from app.core.db import get_db_session, get_session_factory
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.schemas.forecast import CurrentForecastRead, ForecastRunAccepted, ForecastRunStatusRead, ForecastTriggerRequest
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/api/v1", tags=["forecast"])


def get_geomet_client() -> GeoMetClient:
    return GeoMetClient()


def get_nager_date_client() -> NagerDateClient:
    return NagerDateClient()


def build_forecast_service(session: Session, geomet_client: GeoMetClient, nager_date_client: NagerDateClient) -> ForecastService:
    return ForecastService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_run_repository=ForecastRunRepository(session),
        forecast_repository=ForecastRepository(session),
        forecast_model_repository=ForecastModelRepository(session),
        geomet_client=geomet_client,
        nager_date_client=nager_date_client,
        settings=get_settings(),
        logger=logging.getLogger("forecast.api"),
    )


@router.post("/forecast-runs/1-day/trigger", response_model=ForecastRunAccepted, status_code=202)
def trigger_daily_forecast(
    background_tasks: BackgroundTasks,
    payload: ForecastTriggerRequest | None = None,
    session: Session = Depends(get_db_session),
    geomet_client: GeoMetClient = Depends(get_geomet_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    _claims: dict = Depends(require_forecast_trigger),
) -> ForecastRunAccepted:
    if payload is not None and payload.trigger_type != "on_demand":
        raise HTTPException(status_code=422, detail="triggerType must be on_demand")
    service = build_forecast_service(session, geomet_client, nager_date_client)
    run = service.start_run(trigger_type="on_demand")
    session.commit()

    def execute() -> None:
        background_session = get_session_factory()()
        try:
            background_service = build_forecast_service(background_session, geomet_client, nager_date_client)
            background_service.execute_run(run.forecast_run_id)
            background_session.commit()
        finally:
            background_session.close()

    background_tasks.add_task(execute)
    return ForecastRunAccepted(forecastRunId=run.forecast_run_id, status="running")


@router.get("/forecast-runs/{forecast_run_id}", response_model=ForecastRunStatusRead)
def get_forecast_run(
    forecast_run_id: str = Path(min_length=1),
    session: Session = Depends(get_db_session),
    geomet_client: GeoMetClient = Depends(get_geomet_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    _claims: dict = Depends(require_forecast_reader),
) -> ForecastRunStatusRead:
    service = build_forecast_service(session, geomet_client, nager_date_client)
    return service.get_run_status(forecast_run_id)


@router.get("/forecasts/current", response_model=CurrentForecastRead)
def get_current_forecast(
    session: Session = Depends(get_db_session),
    geomet_client: GeoMetClient = Depends(get_geomet_client),
    nager_date_client: NagerDateClient = Depends(get_nager_date_client),
    _claims: dict = Depends(require_forecast_reader),
) -> CurrentForecastRead:
    service = build_forecast_service(session, geomet_client, nager_date_client)
    return service.get_current_forecast()
