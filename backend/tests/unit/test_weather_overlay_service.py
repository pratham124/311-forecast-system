from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.weather_overlay_repository import WeatherOverlayRepository
from app.services.weather_overlay_alignment import WeatherOverlayAlignmentService
from app.services.weather_overlay_service import WeatherOverlayService


class FakeGeoMetClient:
    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime):
        return [
            {"timestamp": horizon_start, "temperature_c": 2.5, "precipitation_mm": 0.0},
            {"timestamp": horizon_end - timedelta(hours=1), "temperature_c": 3.0, "precipitation_mm": 1.2},
        ]


def test_alignment_rules_and_snowfall_mapping():
    alignment = WeatherOverlayAlignmentService()
    supported = alignment.resolve("citywide")
    assert supported.supported is True
    assert supported.station_id == "edmonton-hourly"

    unsupported = alignment.resolve("unsupported")
    assert unsupported.supported is False
    assert unsupported.alignment_status == "misaligned"

    WeatherOverlayRepository.reset_for_tests()
    service = WeatherOverlayService(
        repository=WeatherOverlayRepository(),
        geomet_client=FakeGeoMetClient(),
        alignment_service=alignment,
    )
    response = service.get_overlay(
        geography_id="citywide",
        time_range_start=datetime(2026, 3, 20, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 20, 2, tzinfo=timezone.utc),
        weather_measure="snowfall",
    )
    assert response.overlay_status == "visible"
    assert response.observations[0].value == 0.0
    assert response.observations[1].value == 1.2
