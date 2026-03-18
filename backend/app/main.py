from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.ingestion import router as ingestion_router
from app.core.config import get_settings
from app.core.db import Base, get_engine, get_session_factory
from app.services.scheduler_service import SchedulerService, build_ingestion_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    scheduler_service = SchedulerService()
    app.state.scheduler_service = scheduler_service
    if settings.scheduler_enabled:
        scheduler_service.register_cron_job(
            "edmonton_311_ingestion",
            build_ingestion_job(app.state.session_factory),
            settings.scheduler_cron,
        )
        scheduler_service.start()
    try:
        yield
    finally:
        scheduler_service.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="311 Forecast System Backend", lifespan=lifespan)
    Base.metadata.create_all(bind=get_engine())
    app.state.session_factory = get_session_factory()
    app.include_router(ingestion_router)
    return app


app = create_app()
