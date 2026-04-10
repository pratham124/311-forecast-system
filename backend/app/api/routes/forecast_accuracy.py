from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_forecast_accuracy_reader
from app.core.auth import get_current_claims
from app.core.config import get_settings
from app.core.db import get_db_session
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.forecast_accuracy_repository import ForecastAccuracyRepository
from app.repositories.forecast_repository import ForecastRepository
from app.schemas.forecast_accuracy import (
    ForecastAccuracyQuery,
    ForecastAccuracyRenderEvent,
    ForecastAccuracyRenderEventResponse,
    ForecastAccuracyResponse,
)
from app.services.forecast_accuracy_alignment_service import ForecastAccuracyAlignmentService
from app.services.forecast_accuracy_metric_service import ForecastAccuracyMetricService
from app.services.forecast_accuracy_observability_service import ForecastAccuracyObservabilityService
from app.services.forecast_accuracy_query_service import ForecastAccuracyQueryService
from app.clients.actual_demand_client import ActualDemandClient
from app.clients.forecast_history_client import ForecastHistoryClient

router = APIRouter(prefix="/api/v1/forecast-accuracy", tags=["forecast-accuracy"])


def build_query_service(session: Session) -> ForecastAccuracyQueryService:
    settings = get_settings()
    repository = ForecastAccuracyRepository(session)
    observability = ForecastAccuracyObservabilityService(repository, logger=logging.getLogger("forecast_accuracy.api"))
    return ForecastAccuracyQueryService(
        repository=repository,
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_history_client=ForecastHistoryClient(ForecastRepository(session)),
        actual_demand_client=ActualDemandClient(CleanedDatasetRepository(session), settings.source_name),
        metric_service=ForecastAccuracyMetricService(EvaluationRepository(session)),
        alignment_service=ForecastAccuracyAlignmentService(),
        observability_service=observability,
        source_name=settings.source_name,
        logger=logging.getLogger("forecast_accuracy.api"),
    )


def build_observability_service(session: Session) -> ForecastAccuracyObservabilityService:
    return ForecastAccuracyObservabilityService(
        ForecastAccuracyRepository(session),
        logger=logging.getLogger("forecast_accuracy.api"),
    )


@router.get("", response_model=ForecastAccuracyResponse)
def get_forecast_accuracy(
    time_range_start: str | None = Query(default=None, alias="timeRangeStart"),
    time_range_end: str | None = Query(default=None, alias="timeRangeEnd"),
    service_category: str | None = Query(default=None, alias="serviceCategory"),
    session: Session = Depends(get_db_session),
    claims: dict = Depends(require_forecast_accuracy_reader),
) -> ForecastAccuracyResponse:
    try:
        query = ForecastAccuracyQuery.model_validate(
            {
                "timeRangeStart": time_range_start,
                "timeRangeEnd": time_range_end,
                "serviceCategory": service_category,
            }
        )
    except Exception as exc:  # pragma: no cover - FastAPI validation path wrapper
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return build_query_service(session).get_view(query, claims)


@router.post("/{forecast_accuracy_request_id}/render-events", response_model=ForecastAccuracyRenderEventResponse, status_code=status.HTTP_202_ACCEPTED)
def record_forecast_accuracy_render_event(
    forecast_accuracy_request_id: str,
    payload: ForecastAccuracyRenderEvent,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_forecast_accuracy_reader),
    claims: dict = Depends(get_current_claims),
) -> ForecastAccuracyRenderEventResponse:
    try:
        return build_observability_service(session).record_render_event(
            forecast_accuracy_request_id=forecast_accuracy_request_id,
            payload=payload,
            claims=claims,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Forecast accuracy request not found") from exc
