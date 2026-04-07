from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.weather_overlay_repository import WeatherOverlayRepository
from app.services.weather_overlay_alignment import WeatherOverlayAlignmentService
from app.services.weather_overlay_service import WeatherOverlayService
from app.clients.geomet_client import GeoMetClientError
from app.schemas.weather_overlay import WeatherOverlayRenderEvent


class FakeGeoMetClient:
    def __init__(self, mode: str = "ok") -> None:
        self.mode = mode

    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime):
        if self.mode == "error":
            raise GeoMetClientError("failed")
        if self.mode == "empty":
            return []
        return [
            {"timestamp": horizon_start + timedelta(hours=1), "temperature_c": 2.0, "snowfall_mm": 0.0},
            {"timestamp": horizon_start + timedelta(hours=2), "temperature_c": 3.0, "snowfall_mm": 0.1},
        ]


def _service(mode: str = "ok") -> WeatherOverlayService:
    return WeatherOverlayService(
        repository=WeatherOverlayRepository(),
        geomet_client=FakeGeoMetClient(mode=mode),
        alignment_service=WeatherOverlayAlignmentService(),
    )


def test_overlay_visible_unavailable_and_retrieval_failure():
    WeatherOverlayRepository.reset_for_tests()
    start = datetime(2026, 3, 20, tzinfo=timezone.utc)
    end = datetime(2026, 3, 20, 3, tzinfo=timezone.utc)

    visible = _service("ok").get_overlay(
        geography_id="citywide",
        time_range_start=start,
        time_range_end=end,
        weather_measure="temperature",
    )
    assert visible.overlay_status == "visible"
    assert len(visible.observations) == 2

    unavailable = _service("empty").get_overlay(
        geography_id="citywide",
        time_range_start=start,
        time_range_end=end,
        weather_measure="temperature",
    )
    assert unavailable.overlay_status == "unavailable"

    failed = _service("error").get_overlay(
        geography_id="citywide",
        time_range_start=start,
        time_range_end=end,
        weather_measure="temperature",
    )
    assert failed.overlay_status == "retrieval-failed"


def test_overlay_misaligned_superseded_and_failed_to_render_event():
    WeatherOverlayRepository.reset_for_tests()
    service = _service("ok")
    start = datetime(2026, 3, 20, tzinfo=timezone.utc)
    end = datetime(2026, 3, 20, 3, tzinfo=timezone.utc)

    misaligned = service.get_overlay(
        geography_id="not-supported",
        time_range_start=start,
        time_range_end=end,
        weather_measure="temperature",
    )
    assert misaligned.overlay_status == "misaligned"

    first = service.get_overlay(
        geography_id="citywide",
        time_range_start=start,
        time_range_end=end,
        weather_measure="temperature",
    )
    second = service.get_overlay(
        geography_id="citywide",
        time_range_start=start,
        time_range_end=end,
        weather_measure="snowfall",
    )
    assert second.overlay_status == "visible"
    superseded_state = WeatherOverlayRepository().get_state(first.overlay_request_id)
    assert superseded_state is not None
    assert superseded_state.overlay_status == "superseded"

    service.record_render_event(
        second.overlay_request_id,
        payload=WeatherOverlayRenderEvent(
            renderStatus="failed-to-render",
            reportedAt="2026-03-20T04:00:00Z",
            failureReason="chart failed",
        ),
    )
    failed_render_state = WeatherOverlayRepository().get_state(second.overlay_request_id)
    assert failed_render_state is not None
    assert failed_render_state.overlay_status == "failed-to-render"
