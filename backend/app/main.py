from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.approved_dataset_status import router as approved_dataset_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.review_needed_status import router as review_needed_router
from app.api.routes.validation_run_status import router as validation_run_router
from app.core.config import get_settings
from app.core.db import get_session_factory, run_migrations
from app.services.scheduler_service import SchedulerService, build_ingestion_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    scheduler_service = SchedulerService()
    app.state.scheduler_service = scheduler_service
    if settings.scheduler_enabled:
        scheduler_service.register_cron_job(
            'edmonton_311_ingestion',
            build_ingestion_job(app.state.session_factory),
            settings.scheduler_cron,
        )
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
    return app


app = create_app()
