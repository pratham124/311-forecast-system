from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_demand_comparison_reader
from app.core.auth import get_current_claims
from app.core.config import get_settings
from app.core.db import get_db_session
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.demand_comparison_repository import DemandComparisonRepository
from app.repositories.demand_lineage_repository import DemandLineageRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.demand_comparison_api import (
    DemandComparisonContext,
    DemandComparisonQueryRequest,
    DemandComparisonRenderEvent,
    DemandComparisonRenderEventResponse,
)
from app.services.demand_comparison_context_service import DemandComparisonContextService
from app.services.demand_comparison_render_service import DemandComparisonRenderService
from app.services.demand_comparison_result_builder import DemandComparisonResultBuilder
from app.services.demand_comparison_service import DemandComparisonService
from app.services.demand_comparison_source_resolution import DemandComparisonSourceResolver
from app.services.demand_comparison_warning_service import DemandComparisonWarningService

router = APIRouter(prefix="/api/v1/demand-comparisons", tags=["demand-comparisons"])


def build_demand_comparison_service(session: Session) -> DemandComparisonService:
    settings = get_settings()
    cleaned_repository = CleanedDatasetRepository(session)
    forecast_repository = ForecastRepository(session)
    weekly_forecast_repository = WeeklyForecastRepository(session)
    return DemandComparisonService(
        comparison_repository=DemandComparisonRepository(session),
        cleaned_dataset_repository=cleaned_repository,
        forecast_repository=forecast_repository,
        weekly_forecast_repository=weekly_forecast_repository,
        context_service=DemandComparisonContextService(cleaned_repository, settings.source_name),
        warning_service=DemandComparisonWarningService(),
        source_resolver=DemandComparisonSourceResolver(
            demand_lineage_repository=DemandLineageRepository(
                cleaned_dataset_repository=cleaned_repository,
                forecast_repository=forecast_repository,
                weekly_forecast_repository=weekly_forecast_repository,
            ),
            source_name=settings.source_name,
            daily_forecast_product_name=settings.forecast_product_name,
            weekly_forecast_product_name=settings.weekly_forecast_product_name,
        ),
        result_builder=DemandComparisonResultBuilder(),
        logger=logging.getLogger("demand_comparison.api"),
    )


def build_render_service(session: Session) -> DemandComparisonRenderService:
    return DemandComparisonRenderService(
        DemandComparisonRepository(session),
        logger=logging.getLogger("demand_comparison.api"),
    )


@router.get("/context", response_model=DemandComparisonContext)
def get_demand_comparison_context(
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_demand_comparison_reader),
) -> DemandComparisonContext:
    settings = get_settings()
    return DemandComparisonContextService(CleanedDatasetRepository(session), settings.source_name).get_context()


@router.post("/queries")
def create_demand_comparison_query(
    payload: DemandComparisonQueryRequest,
    session: Session = Depends(get_db_session),
    claims: dict = Depends(require_demand_comparison_reader),
):
    try:
        return build_demand_comparison_service(session).execute_query(payload, claims)
    except LookupError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/{comparison_request_id}/render-events",
    response_model=DemandComparisonRenderEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def record_demand_comparison_render_event(
    comparison_request_id: str,
    payload: DemandComparisonRenderEvent,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_demand_comparison_reader),
    claims: dict = Depends(get_current_claims),
) -> DemandComparisonRenderEventResponse:
    try:
        return build_render_service(session).record_event(
            comparison_request_id=comparison_request_id,
            payload=payload,
            claims=claims,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Demand comparison request not found") from exc
