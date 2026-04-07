from __future__ import annotations

from datetime import datetime, timezone

from app.models.forecast_models import ForecastBucket
from app.models.weekly_forecast_models import WeeklyForecastBucket
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.weekly_forecast_repository import WeeklyForecastRepository
from app.services.forecast_scope_service import ForecastScopeService


def test_scope_service_uses_hourly_for_daily_forecast(session) -> None:
    session.add(
        ForecastBucket(
            forecast_version_id="daily-version-1",
            bucket_start=datetime(2026, 4, 7, 10, tzinfo=timezone.utc),
            bucket_end=datetime(2026, 4, 7, 11, tzinfo=timezone.utc),
            service_category="Roads",
            geography_key=None,
            point_forecast=10,
            quantile_p10=8,
            quantile_p50=10,
            quantile_p90=12,
            baseline_value=9,
        )
    )
    session.commit()

    service = ForecastScopeService(
        forecast_repository=ForecastRepository(session),
        weekly_forecast_repository=WeeklyForecastRepository(session),
    )
    scopes = service.list_scopes(forecast_product="daily", forecast_reference_id="daily-version-1")

    assert len(scopes) == 1
    assert scopes[0].forecast_window_type == "hourly"


def test_scope_service_uses_daily_for_weekly_forecast(session) -> None:
    session.add(
        WeeklyForecastBucket(
            weekly_forecast_version_id="weekly-version-1",
            forecast_date_local=datetime(2026, 4, 7, tzinfo=timezone.utc),
            service_category="Roads",
            geography_key="Ward 1",
            point_forecast=20,
            quantile_p10=18,
            quantile_p50=20,
            quantile_p90=24,
            baseline_value=19,
        )
    )
    session.commit()

    service = ForecastScopeService(
        forecast_repository=ForecastRepository(session),
        weekly_forecast_repository=WeeklyForecastRepository(session),
    )
    scopes = service.list_scopes(forecast_product="weekly", forecast_reference_id="weekly-version-1")

    assert len(scopes) == 1
    assert scopes[0].forecast_window_type == "daily"
    assert scopes[0].geography_value == "Ward 1"
