from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_visualization_reader, require_visualization_writer
from app.core.config import get_settings
from app.core.db import get_db_session
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.visualization_repository import VisualizationRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.schemas.forecast_visualization import ForecastVisualizationRead, ServiceCategoryOptionsRead, VisualizationRenderEvent
from app.services.forecast_visualization_service import ForecastVisualizationService
from app.services.forecast_visualization_sources import ForecastVisualizationSourceService
from app.services.historical_demand_service import HistoricalDemandService
from app.services.visualization_snapshot_service import VisualizationSnapshotService

router = APIRouter(prefix="/api/v1/forecast-visualizations", tags=["forecast-visualizations"])


VALID_PRODUCTS = {"daily_1_day", "weekly_7_day"}


def build_visualization_service(session: Session) -> ForecastVisualizationService:
    settings = get_settings()
    visualization_repository = VisualizationRepository(session)
    return ForecastVisualizationService(
        cleaned_dataset_repository=CleanedDatasetRepository(session),
        forecast_repository=ForecastRepository(session),
        weekly_forecast_repository=WeeklyForecastRepository(session),
        visualization_repository=visualization_repository,
        historical_demand_service=HistoricalDemandService(CleanedDatasetRepository(session), settings.source_name),
        source_service=ForecastVisualizationSourceService(),
        snapshot_service=VisualizationSnapshotService(
            visualization_repository=visualization_repository,
            fallback_age_hours=settings.visualization_fallback_age_hours,
        ),
        settings=settings,
        logger=logging.getLogger("forecast_visualization.api"),
    )


@router.get('/current', response_model=ForecastVisualizationRead)
def get_current_forecast_visualization(
    forecast_product: str = Query(alias="forecastProduct"),
    service_category: list[str] | None = Query(default=None, alias="serviceCategory"),
    exclude_service_category: list[str] | None = Query(default=None, alias="excludeServiceCategory"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_visualization_reader),
) -> ForecastVisualizationRead:
    if forecast_product not in VALID_PRODUCTS:
        raise HTTPException(status_code=422, detail="forecastProduct must be one of daily_1_day or weekly_7_day")
    service = build_visualization_service(session)
    try:
        return service.get_current_visualization(
            forecast_product=forecast_product,
            service_categories=service_category,
            excluded_service_categories=exclude_service_category,
        )
    except Exception:
        logging.getLogger('forecast_visualization.api').exception(
            'Failed to build current visualization',
            extra={
                'forecast_product': forecast_product,
                'service_categories': service_category or [],
                'excluded_service_categories': exclude_service_category or [],
            },
        )
        raise


@router.get('/service-categories', response_model=ServiceCategoryOptionsRead)
def list_visualization_service_categories(
    forecast_product: str = Query(alias="forecastProduct"),
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_visualization_reader),
) -> ServiceCategoryOptionsRead:
    if forecast_product not in VALID_PRODUCTS:
        raise HTTPException(status_code=422, detail="forecastProduct must be one of daily_1_day or weekly_7_day")
    service = build_visualization_service(session)
    return service.list_service_categories(forecast_product=forecast_product)


@router.post('/{visualization_load_id}/render-events', status_code=status.HTTP_202_ACCEPTED)
def record_visualization_render_event(
    visualization_load_id: str,
    payload: VisualizationRenderEvent,
    session: Session = Depends(get_db_session),
    _claims: dict = Depends(require_visualization_writer),
) -> Response:
    service = build_visualization_service(session)
    try:
        service.record_render_event(visualization_load_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Visualization load not found") from exc
    return Response(status_code=status.HTTP_202_ACCEPTED)
