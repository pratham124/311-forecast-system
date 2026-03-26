from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.clients.edmonton_311 import Edmonton311Client
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.core.auth import require_operational_manager, require_planner_or_manager
from app.core.db import get_db_session
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.failure_notification_repository import FailureNotificationRepository
from app.repositories.run_repository import RunRepository
from app.schemas.failure_notifications import FailureNotificationList
from app.schemas.ingestion import CurrentDataset, IngestionRunAccepted, IngestionRunStatus
from app.services.ingestion_logging_service import IngestionLoggingService
from app.services.ingestion_query_service import IngestionQueryService

router = APIRouter(prefix="/api/v1", tags=["ingestion"])


def get_client() -> Edmonton311Client:
    return Edmonton311Client()


def _build_query_service(session: Session) -> IngestionQueryService:
    return IngestionQueryService(
        run_repository=RunRepository(session),
        dataset_repository=DatasetRepository(session),
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        failure_repository=FailureNotificationRepository(session),
    )


@router.post("/ingestion-runs/311/trigger", response_model=IngestionRunAccepted, status_code=202)
def trigger_ingestion(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
    client: Edmonton311Client = Depends(get_client),
    _claims: dict = Depends(require_operational_manager),
) -> IngestionRunAccepted:
    pipeline = IngestionPipeline(session, client, IngestionLoggingService(logging.getLogger("ingestion")))
    run_id, cursor_used, previous_marker = pipeline.start_run(trigger_type="on_demand")

    def execute() -> None:
        pipeline.run(
            trigger_type="on_demand",
            existing_run_id=run_id,
            existing_cursor=cursor_used,
            previous_marker=previous_marker,
        )

    background_tasks.add_task(execute)
    session.commit()
    return IngestionRunAccepted(run_id=run_id, status="running")


@router.get("/ingestion-runs/{run_id}", response_model=IngestionRunStatus)
def get_run_status(
    run_id: str,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_planner_or_manager),
) -> IngestionRunStatus:
    return _build_query_service(session).get_run_status(run_id)


@router.get("/datasets/current", response_model=CurrentDataset)
def get_current_dataset(
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_planner_or_manager),
) -> CurrentDataset:
    return _build_query_service(session).get_current_dataset("edmonton_311")


@router.get("/monitoring/failure-notifications", response_model=FailureNotificationList)
def list_failure_notifications(
    run_id: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_planner_or_manager),
) -> FailureNotificationList:
    return _build_query_service(session).list_failure_notifications(run_id)
