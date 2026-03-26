from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_evaluation_reader, require_evaluation_trigger
from app.core.config import get_settings
from app.core.db import get_db_session, get_session_factory
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.evaluation import CurrentEvaluationRead, EvaluationRunAccepted, EvaluationRunStatusRead, EvaluationRunTrigger, ForecastProduct
from app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/api/v1", tags=["evaluation"])


def build_evaluation_service(session: Session) -> EvaluationService:
    return EvaluationService(
        evaluation_repository=EvaluationRepository(session),
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_repository=ForecastRepository(session),
        weekly_forecast_repository=WeeklyForecastRepository(session),
        settings=get_settings(),
        logger=logging.getLogger("evaluation.api"),
    )


@router.post("/evaluation-runs/trigger", response_model=EvaluationRunAccepted, status_code=202)
def trigger_evaluation_run(
    payload: EvaluationRunTrigger,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_evaluation_trigger),
) -> EvaluationRunAccepted:
    service = build_evaluation_service(session)
    run = service.start_run(payload.forecast_product, trigger_type="on_demand")
    session.commit()

    def execute() -> None:
        background_session = get_session_factory()()
        try:
            background_service = build_evaluation_service(background_session)
            background_service.execute_run(run.evaluation_run_id)
            background_session.commit()
        finally:
            background_session.close()

    background_tasks.add_task(execute)
    return EvaluationRunAccepted(evaluationRunId=run.evaluation_run_id, status="running")


@router.get("/evaluation-runs/{evaluation_run_id}", response_model=EvaluationRunStatusRead)
def get_evaluation_run(
    evaluation_run_id: str,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_evaluation_reader),
) -> EvaluationRunStatusRead:
    service = build_evaluation_service(session)
    return service.get_run_status(evaluation_run_id)


@router.get("/evaluations/current", response_model=CurrentEvaluationRead)
def get_current_evaluation(
    forecast_product: ForecastProduct = Query(alias="forecastProduct"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_evaluation_reader),
) -> CurrentEvaluationRead:
    service = build_evaluation_service(session)
    return service.get_current_evaluation(forecast_product)
