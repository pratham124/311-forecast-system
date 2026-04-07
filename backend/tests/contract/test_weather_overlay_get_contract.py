from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.api.routes import weather_overlay as weather_overlay_route
from app.clients.geomet_client import GeoMetClientError
from app.repositories.weather_overlay_repository import WeatherOverlayRepository
from app.services.weather_overlay_alignment import WeatherOverlayAlignmentService
from app.services.weather_overlay_service import WeatherOverlayService


class FakeGeoMetClient:
    def __init__(self, mode: str = "ok") -> None:
        self.mode = mode

    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime):
        if self.mode == "error":
            raise GeoMetClientError("boom")
        if self.mode == "empty":
            return []
        return [
            {"timestamp": horizon_start, "temperature_c": 3.5, "snowfall_mm": 0.2, "precipitation_mm": 0.1},
            {"timestamp": horizon_end - timedelta(hours=1), "temperature_c": 4.0, "snowfall_mm": 0.0, "precipitation_mm": 0.3},
        ]


def _override_service(mode: str = "ok"):
    repo = WeatherOverlayRepository()
    return WeatherOverlayService(
        repository=repo,
        geomet_client=FakeGeoMetClient(mode=mode),
        alignment_service=WeatherOverlayAlignmentService(),
    )


def test_get_weather_overlay_visible_and_disabled(app_client, operational_manager_headers):
    WeatherOverlayRepository.reset_for_tests()
    original = weather_overlay_route.build_weather_overlay_service
    weather_overlay_route.build_weather_overlay_service = lambda: _override_service("ok")
    try:
        response = app_client.get(
            "/api/v1/forecast-explorer/weather-overlay",
            params={
                "geographyId": "citywide",
                "timeRangeStart": "2026-03-20T00:00:00Z",
                "timeRangeEnd": "2026-03-20T02:00:00Z",
                "weatherMeasure": "temperature",
            },
            headers=operational_manager_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["overlayStatus"] == "visible"
        assert len(body["observations"]) == 2

        precipitation = app_client.get(
            "/api/v1/forecast-explorer/weather-overlay",
            params={
                "geographyId": "citywide",
                "timeRangeStart": "2026-03-20T00:00:00Z",
                "timeRangeEnd": "2026-03-20T02:00:00Z",
                "weatherMeasure": "precipitation",
            },
            headers=operational_manager_headers,
        )
        assert precipitation.status_code == 200
        assert precipitation.json()["overlayStatus"] == "visible"
        assert precipitation.json()["observations"][0]["value"] == 0.1

        disabled = app_client.get(
            "/api/v1/forecast-explorer/weather-overlay",
            params={
                "geographyId": "citywide",
                "timeRangeStart": "2026-03-20T00:00:00Z",
                "timeRangeEnd": "2026-03-20T02:00:00Z",
            },
            headers=operational_manager_headers,
        )
        assert disabled.status_code == 200
        assert disabled.json()["overlayStatus"] == "disabled"
    finally:
        weather_overlay_route.build_weather_overlay_service = original


def test_get_weather_overlay_auth_and_validation(app_client, viewer_headers, operational_manager_headers):
    response = app_client.get(
        "/api/v1/forecast-explorer/weather-overlay",
        params={
            "geographyId": "citywide",
            "timeRangeStart": "2026-03-20T00:00:00Z",
            "timeRangeEnd": "2026-03-20T02:00:00Z",
            "weatherMeasure": "temperature",
        },
    )
    assert response.status_code == 401

    forbidden = app_client.get(
        "/api/v1/forecast-explorer/weather-overlay",
        params={
            "geographyId": "citywide",
            "timeRangeStart": "2026-03-20T00:00:00Z",
            "timeRangeEnd": "2026-03-20T02:00:00Z",
            "weatherMeasure": "temperature",
        },
        headers=viewer_headers,
    )
    assert forbidden.status_code == 403

    invalid = app_client.get(
        "/api/v1/forecast-explorer/weather-overlay",
        params={
            "geographyId": "citywide",
            "timeRangeStart": "2026-03-20T02:00:00Z",
            "timeRangeEnd": "2026-03-20T00:00:00Z",
            "weatherMeasure": "wind",
        },
        headers=operational_manager_headers,
    )
    assert invalid.status_code == 422
