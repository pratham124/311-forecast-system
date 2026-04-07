from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.approved_dataset_status import router as approved_dataset_router
from app.api.routes.auth import router as auth_router
from app.api.routes.evaluations import router as evaluation_router
from app.api.routes.forecasts import router as forecast_router
from app.api.routes.forecast_visualizations import router as forecast_visualization_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.demand_comparisons import router as demand_comparison_router
from app.api.routes.historical_demand import router as historical_demand_router
from app.api.routes.public_forecast import router as public_forecast_router
from app.api.routes.review_needed_status import router as review_needed_router
from app.api.routes.validation_run_status import router as validation_run_router
from app.api.routes.weather_overlay import router as weather_overlay_router
from app.api.routes.weekly_forecasts import router as weekly_forecast_router
from app.core.config import get_settings
from app.core.db import get_session_factory, run_migrations
from app.core.logging import configure_logging
from app.repositories.auth_repository import AuthRepository
from app.services.auth_service import AuthBootstrapService
from app.services.evaluation_service import build_evaluation_job
from app.services.forecast_scheduler import build_forecast_job, build_forecast_training_job
from app.services.scheduler_service import SchedulerService, build_ingestion_job
from app.services.weekly_forecast_scheduler import build_weekly_forecast_job, build_weekly_forecast_training_job, build_weekly_regeneration_job


def _expand_local_frontend_origins(origin: str) -> list[str]:
    origins = {origin}
    if origin.startswith("http://localhost:"):
        origins.add(origin.replace("http://localhost:", "http://127.0.0.1:", 1))
    elif origin.startswith("http://127.0.0.1:"):
        origins.add(origin.replace("http://127.0.0.1:", "http://localhost:", 1))
    return sorted(origins)


def _parse_allowlist(raw_value: str) -> list[tuple[str, list[str]]]:
    entries: list[tuple[str, list[str]]] = []
    for item in raw_value.split(','):
        token = item.strip()
        if not token or ':' not in token:
            continue
        email, raw_roles = token.split(':', 1)
        roles = [role.strip() for role in raw_roles.split('|') if role.strip()]
        if email.strip() and roles:
            entries.append((email.strip().lower(), roles))
    return entries


def bootstrap_auth_allowlist() -> None:
    settings = get_settings()
    entries = _parse_allowlist(getattr(settings, "auth_signup_allowlist", ""))
    if not entries:
        return
    session = get_session_factory()()
    try:
        AuthBootstrapService(AuthRepository(session)).sync_allowlist(entries)
    finally:
        session.close()


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
    evaluation_scheduler_enabled = getattr(settings, "evaluation_scheduler_enabled", False)
    evaluation_scheduler_cron = getattr(settings, "evaluation_scheduler_cron", "0 3 * * *")

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
    if evaluation_scheduler_enabled:
        scheduler_service.register_cron_job(
            'forecast_evaluation',
            build_evaluation_job(app.state.session_factory),
            evaluation_scheduler_cron,
        )
    if (
        ingestion_scheduler_enabled
        or forecast_model_scheduler_enabled
        or forecast_scheduler_enabled
        or weekly_forecast_model_scheduler_enabled
        or weekly_forecast_scheduler_enabled
        or weekly_forecast_daily_regeneration_enabled
        or evaluation_scheduler_enabled
    ):
        scheduler_service.start()
    try:
        yield
    finally:
        scheduler_service.shutdown()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title='311 Forecast System Backend', lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_expand_local_frontend_origins(getattr(settings, "frontend_origin", "http://localhost:5173")),
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    run_migrations()
    app.state.session_factory = get_session_factory()
    bootstrap_auth_allowlist()
    app.include_router(auth_router)
    app.include_router(ingestion_router)
    app.include_router(validation_run_router)
    app.include_router(approved_dataset_router)
    app.include_router(review_needed_router)
    app.include_router(forecast_router)
    app.include_router(evaluation_router)
    app.include_router(forecast_visualization_router)
    app.include_router(historical_demand_router)
    app.include_router(demand_comparison_router)
    app.include_router(public_forecast_router)
    app.include_router(weather_overlay_router)
    app.include_router(weekly_forecast_router)
    return app


app = create_app()
