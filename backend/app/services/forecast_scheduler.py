from __future__ import annotations

import logging
from typing import Callable

from app.clients.nager_date_client import NagerDateClient
from app.clients.weather_client import build_weather_client
from app.core.config import get_settings
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_model_repository import ForecastModelRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.services.forecast_service import ForecastService
from app.services.forecast_training_service import ForecastTrainingService


def build_forecast_training_job(session_factory: Callable[[], object]) -> Callable[[], object]:
    def run_job() -> object:
        session = session_factory()
        try:
            service = ForecastTrainingService(
                cleaned_dataset_repository=CleanedDatasetRepository(session),
                forecast_model_repository=ForecastModelRepository(session),
                geomet_client=build_weather_client(),
                nager_date_client=NagerDateClient(),
                settings=get_settings(),
                logger=logging.getLogger("scheduler.forecast_model"),
            )
            run = service.start_run(trigger_type="scheduled")
            session.commit()
            service.execute_run(run.forecast_model_run_id)
            session.commit()
            return run.forecast_model_run_id
        finally:
            session.close()

    return run_job


def build_forecast_job(session_factory: Callable[[], object]) -> Callable[[], object]:
    def run_job() -> object:
        session = session_factory()
        try:
            service = ForecastService(
                cleaned_dataset_repository=CleanedDatasetRepository(session),
                forecast_run_repository=ForecastRunRepository(session),
                forecast_repository=ForecastRepository(session),
                forecast_model_repository=ForecastModelRepository(session),
                geomet_client=build_weather_client(),
                nager_date_client=NagerDateClient(),
                settings=get_settings(),
                logger=logging.getLogger("scheduler.forecast"),
            )
            run = service.start_run(trigger_type="scheduled")
            session.commit()
            service.execute_run(run.forecast_run_id)
            session.commit()
            return run.forecast_run_id
        finally:
            session.close()

    return run_job
