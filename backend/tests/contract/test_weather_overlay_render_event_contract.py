from __future__ import annotations

from datetime import datetime

from app.api.routes import weather_overlay as weather_overlay_route
from app.repositories.weather_overlay_repository import WeatherOverlayRepository
from app.services.weather_overlay_alignment import WeatherOverlayAlignmentService
from app.services.weather_overlay_service import WeatherOverlayService


class FakeGeoMetClient:
    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime):
        return [{"timestamp": horizon_start, "temperature_c": 1.5, "snowfall_mm": 0.0}]


def _override_service():
    return WeatherOverlayService(
        repository=WeatherOverlayRepository(),
        geomet_client=FakeGeoMetClient(),
        alignment_service=WeatherOverlayAlignmentService(),
    )


def test_post_render_event_success_and_errors(app_client, operational_manager_headers, viewer_headers):
    WeatherOverlayRepository.reset_for_tests()
    original = weather_overlay_route.build_weather_overlay_service
    weather_overlay_route.build_weather_overlay_service = _override_service
    try:
        overlay = app_client.get(
            "/api/v1/forecast-explorer/weather-overlay",
            params={
                "geographyId": "citywide",
                "timeRangeStart": "2026-03-20T00:00:00Z",
                "timeRangeEnd": "2026-03-20T02:00:00Z",
                "weatherMeasure": "temperature",
            },
            headers=operational_manager_headers,
        )
        assert overlay.status_code == 200
        request_id = overlay.json()["overlayRequestId"]

        accepted = app_client.post(
            f"/api/v1/forecast-explorer/weather-overlay/{request_id}/render-events",
            json={"renderStatus": "rendered", "reportedAt": "2026-03-20T03:00:00Z"},
            headers=operational_manager_headers,
        )
        assert accepted.status_code == 202

        invalid = app_client.post(
            f"/api/v1/forecast-explorer/weather-overlay/{request_id}/render-events",
            json={"renderStatus": "failed-to-render", "reportedAt": "2026-03-20T03:00:00Z"},
            headers=operational_manager_headers,
        )
        assert invalid.status_code == 422

        forbidden = app_client.post(
            f"/api/v1/forecast-explorer/weather-overlay/{request_id}/render-events",
            json={"renderStatus": "rendered", "reportedAt": "2026-03-20T03:00:00Z"},
            headers=viewer_headers,
        )
        assert forbidden.status_code == 403
    finally:
        weather_overlay_route.build_weather_overlay_service = original
