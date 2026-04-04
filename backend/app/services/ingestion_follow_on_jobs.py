from __future__ import annotations

import logging

from app.core.db import get_session_factory
from app.services.forecast_scheduler import build_forecast_job, build_forecast_training_job
from app.services.weekly_forecast_scheduler import build_weekly_forecast_job, build_weekly_forecast_training_job


def launch_ingestion_follow_on_jobs() -> None:
    session_factory = get_session_factory()
    logger = logging.getLogger("ingestion.follow_on")
    jobs = (
        ("forecast-model-training", build_forecast_training_job(session_factory)),
        ("forecast-generation", build_forecast_job(session_factory)),
        ("weekly-forecast-model-training", build_weekly_forecast_training_job(session_factory)),
        ("weekly-forecast-generation", build_weekly_forecast_job(session_factory)),
    )

    for name, job in jobs:
        logger.info("ingestion.follow_on.job.started job_name=%s", name)
        _run_job(name, job)
        logger.info("ingestion.follow_on.job.completed job_name=%s", name)


def _run_job(name: str, job) -> None:
    try:
        job()
    except Exception:
        logging.getLogger("ingestion.follow_on").exception("ingestion follow-on job failed", extra={"job_name": name})
