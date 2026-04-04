from __future__ import annotations

import logging
from typing import Callable

from app.clients.nager_date_client import NagerDateClient
from app.clients.weather_client import build_weather_client
from app.core.config import get_settings
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.repositories.weekly_forecast_run_repository import WeeklyForecastRunRepository
from app.services.weekly_forecast_service import WeeklyForecastService
from app.services.weekly_forecast_training_service import WeeklyForecastTrainingService


def _build_job(session_factory: Callable[[], object], trigger_type: str) -> Callable[[], object]:
    def run_job() -> object:
        session = session_factory()
        try:
            service = WeeklyForecastService(
                cleaned_dataset_repository=CleanedDatasetRepository(session),
                weekly_forecast_run_repository=WeeklyForecastRunRepository(session),
                weekly_forecast_repository=WeeklyForecastRepository(session),
                settings=get_settings(),
                geomet_client=build_weather_client(),
                nager_date_client=NagerDateClient(),
                forecast_model_repository=ForecastModelRepository(session),
                logger=logging.getLogger("scheduler.weekly_forecast"),
            )
            run, should_execute = service.start_run(trigger_type=trigger_type)
            session.commit()
            if should_execute:
                service.execute_run(run.weekly_forecast_run_id)
                session.commit()
            return run.weekly_forecast_run_id
        finally:
            session.close()

    return run_job


def build_weekly_forecast_job(session_factory: Callable[[], object]) -> Callable[[], object]:
    return _build_job(session_factory, "scheduled")


def build_weekly_regeneration_job(session_factory: Callable[[], object]) -> Callable[[], object]:
    return _build_job(session_factory, "scheduled")


def build_weekly_forecast_training_job(session_factory: Callable[[], object]) -> Callable[[], object]:
    def run_job() -> object:
        session = session_factory()
        try:
            service = WeeklyForecastTrainingService(
                cleaned_dataset_repository=CleanedDatasetRepository(session),
                forecast_model_repository=ForecastModelRepository(session),
                geomet_client=build_weather_client(),
                nager_date_client=NagerDateClient(),
                settings=get_settings(),
                logger=logging.getLogger("scheduler.weekly_forecast_model"),
            )
            run = service.start_run(trigger_type="scheduled")
            session.commit()
            service.execute_run(run.forecast_model_run_id)
            session.commit()
            return run.forecast_model_run_id
        finally:
            session.close()

    return run_job
