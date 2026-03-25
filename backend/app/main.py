from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.approved_dataset_status import router as approved_dataset_router
from app.api.routes.forecasts import router as forecast_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.review_needed_status import router as review_needed_router
from app.api.routes.validation_run_status import router as validation_run_router
from app.api.routes.weekly_forecasts import router as weekly_forecast_router
from app.core.config import get_settings
from app.core.db import get_session_factory, run_migrations
from app.services.forecast_scheduler import build_forecast_job, build_forecast_training_job
from app.services.scheduler_service import SchedulerService, build_ingestion_job
from app.services.weekly_forecast_scheduler import build_weekly_forecast_job, build_weekly_forecast_training_job, build_weekly_regeneration_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    scheduler_service = SchedulerService()
    app.state.scheduler_service = scheduler_service
    ingestion_scheduler_enabled = getattr(settings, "scheduler_enabled", False)
    ingestion_scheduler_cron = getattr(settings, "scheduler_cron", "0 0 * * 0")
    forecast_model_scheduler_enabled = getattr(settings, "forecast_model_scheduler_enabled", False)
    forecast_model_scheduler_cron = getattr(settings, "forecast_model_scheduler_cron", "15 0 * * *")
    forecast_scheduler_enabled = getattr(settings, "forecast_scheduler_enabled", False)
    forecast_scheduler_cron = getattr(settings, "forecast_scheduler_cron", "0 * * * *")
    weekly_forecast_scheduler_enabled = getattr(settings, "weekly_forecast_scheduler_enabled", False)
    weekly_forecast_model_scheduler_enabled = getattr(settings, "weekly_forecast_model_scheduler_enabled", False)
    weekly_forecast_scheduler_cron = getattr(settings, "weekly_forecast_scheduler_cron", "0 1 * * 1")
    weekly_forecast_model_scheduler_cron = getattr(settings, "weekly_forecast_model_scheduler_cron", "30 0 * * 0")
    weekly_forecast_daily_regeneration_enabled = getattr(settings, "weekly_forecast_daily_regeneration_enabled", False)
    weekly_forecast_daily_regeneration_cron = getattr(settings, "weekly_forecast_daily_regeneration_cron", "0 2 * * *")

    if ingestion_scheduler_enabled:
        scheduler_service.register_cron_job(
            'edmonton_311_ingestion',
            build_ingestion_job(app.state.session_factory),
            ingestion_scheduler_cron,
        )
    if forecast_model_scheduler_enabled:
        scheduler_service.register_cron_job(
            'daily_demand_forecast_model_training',
            build_forecast_training_job(app.state.session_factory),
            forecast_model_scheduler_cron,
        )
    if forecast_scheduler_enabled:
        scheduler_service.register_cron_job(
            'daily_demand_forecast',
            build_forecast_job(app.state.session_factory),
            forecast_scheduler_cron,
        )
    if weekly_forecast_model_scheduler_enabled:
        scheduler_service.register_cron_job(
            'weekly_demand_forecast_model_training',
            build_weekly_forecast_training_job(app.state.session_factory),
            weekly_forecast_model_scheduler_cron,
        )
    if weekly_forecast_scheduler_enabled:
        scheduler_service.register_cron_job(
            'weekly_demand_forecast',
            build_weekly_forecast_job(app.state.session_factory),
            weekly_forecast_scheduler_cron,
        )
    if weekly_forecast_daily_regeneration_enabled:
        scheduler_service.register_cron_job(
            'weekly_demand_forecast_daily_regeneration',
            build_weekly_regeneration_job(app.state.session_factory),
            weekly_forecast_daily_regeneration_cron,
        )
    if (
        ingestion_scheduler_enabled
        or forecast_model_scheduler_enabled
        or forecast_scheduler_enabled
        or weekly_forecast_model_scheduler_enabled
        or weekly_forecast_scheduler_enabled
        or weekly_forecast_daily_regeneration_enabled
    ):
        scheduler_service.start()
    try:
        yield
    finally:
        scheduler_service.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title='311 Forecast System Backend', lifespan=lifespan)
    run_migrations()
    app.state.session_factory = get_session_factory()
    app.include_router(ingestion_router)
    app.include_router(validation_run_router)
    app.include_router(approved_dataset_router)
    app.include_router(review_needed_router)
    app.include_router(forecast_router)
    app.include_router(weekly_forecast_router)
    return app


app = create_app()
