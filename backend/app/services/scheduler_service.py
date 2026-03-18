from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.clients.edmonton_311 import Edmonton311Client
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.services.ingestion_logging_service import IngestionLoggingService


@dataclass
class SchedulerService:
    scheduler: BackgroundScheduler = field(default_factory=BackgroundScheduler)
    jobs: dict[str, Callable[[], object]] = field(default_factory=dict)

    def register_job(self, job_id: str, callback: Callable[[], object]) -> None:
        self.jobs[job_id] = callback

    def register_cron_job(self, job_id: str, callback: Callable[[], object], cron_expression: str) -> None:
        self.register_job(job_id, callback)
        self.scheduler.add_job(callback, CronTrigger.from_crontab(cron_expression), id=job_id, replace_existing=True)

    def trigger_job(self, job_id: str) -> object:
        if job_id not in self.jobs:
            raise KeyError(job_id)
        return self.jobs[job_id]()

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)


def build_ingestion_job(session_factory: Callable[[], object]) -> Callable[[], object]:
    def run_job() -> object:
        session = session_factory()
        try:
            pipeline = IngestionPipeline(
                session=session,
                client=Edmonton311Client(),
                logging_service=IngestionLoggingService(logging.getLogger("scheduler.ingestion")),
            )
            return pipeline.run(trigger_type="scheduled")
        finally:
            session.close()

    return run_job
