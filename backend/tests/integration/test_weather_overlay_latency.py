from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter

from app.repositories.weather_overlay_repository import WeatherOverlayRepository
from app.services.weather_overlay_alignment import WeatherOverlayAlignmentService
from app.services.weather_overlay_service import WeatherOverlayService


class FastGeoMetClient:
    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime):
        return [{"timestamp": horizon_start, "temperature_c": 1.0, "snowfall_mm": 0.0}]


def test_supported_selection_returns_under_5_seconds():
    WeatherOverlayRepository.reset_for_tests()
    service = WeatherOverlayService(
        repository=WeatherOverlayRepository(),
        geomet_client=FastGeoMetClient(),
        alignment_service=WeatherOverlayAlignmentService(),
    )

    start_time = perf_counter()
    response = service.get_overlay(
        geography_id="citywide",
        time_range_start=datetime(2026, 3, 20, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 20, 1, tzinfo=timezone.utc),
        weather_measure="temperature",
    )
    elapsed = perf_counter() - start_time

    assert response.overlay_status == "visible"
    assert elapsed < 5.0
