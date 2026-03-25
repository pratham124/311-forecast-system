from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import get_settings
from app.repositories.visualization_repository import VisualizationRepository
from app.services.forecast_visualization_service import ForecastVisualizationService
from app.services.forecast_visualization_sources import ForecastVisualizationSourceService
from app.services.historical_demand_service import HistoricalDemandService
from app.services.visualization_snapshot_service import VisualizationSnapshotService
from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository

from tests.integration.test_forecast_visualization_success import _build_service, _seed


def test_visualization_uses_fallback_snapshot_when_current_forecast_missing(session):
    _seed(session, include_history=True)
    service = _build_service(session)
    successful = service.get_current_visualization(forecast_product="daily_1_day", service_category="Roads")
    session.commit()
    forecast_repository = ForecastRepository(session)
    marker = forecast_repository.get_current_marker(get_settings().forecast_product_name)
    session.delete(marker)
    session.commit()
    fallback = service.get_current_visualization(forecast_product="daily_1_day", service_category="Roads")
    session.commit()
    assert fallback.view_status == "fallback_shown"
    assert fallback.fallback is not None
    load = VisualizationRepository(session).require_load_record(fallback.visualization_load_id)
    assert load.status == "fallback_shown"


def test_visualization_returns_unavailable_without_fallback(session):
    service = _build_service(session)
    response = service.get_current_visualization(forecast_product="daily_1_day", service_category="Roads")
    session.commit()
    assert response.view_status == "unavailable"
    assert response.summary is not None
