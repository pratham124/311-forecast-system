from __future__ import annotations

from datetime import datetime, timezone

from app.api.routes import weather_overlay as route
from app.models.weather_overlay import OverlaySelection, OverlayStateRecord
from app.repositories.weather_overlay_repository import WeatherOverlayRepository
from app.schemas.weather_overlay import WeatherOverlayRenderEvent, WeatherOverlayResponse
from app.services.weather_overlay_alignment import WeatherOverlayAlignmentService
from app.services.weather_overlay_service import WeatherOverlayService


class NoopGeoMet:
    def fetch_forecast_hourly_conditions(self, horizon_start: datetime, horizon_end: datetime):
        return []


def test_route_build_service_and_validation_paths(app_client, operational_manager_headers):
    service = route.build_weather_overlay_service()
    assert isinstance(service, WeatherOverlayService)

    invalid_measure = app_client.get(
        "/api/v1/forecast-explorer/weather-overlay",
        params={
            "geographyId": "citywide",
            "timeRangeStart": "2026-03-20T00:00:00Z",
            "timeRangeEnd": "2026-03-20T01:00:00Z",
            "weatherMeasure": "wind",
        },
        headers=operational_manager_headers,
    )
    assert invalid_measure.status_code == 422


def test_route_render_event_404_and_409_paths(app_client, operational_manager_headers):
    not_found = app_client.post(
        "/api/v1/forecast-explorer/weather-overlay/does-not-exist/render-events",
        json={"renderStatus": "rendered", "reportedAt": "2026-03-20T03:00:00Z"},
        headers=operational_manager_headers,
    )
    assert not_found.status_code == 404

    disabled = app_client.get(
        "/api/v1/forecast-explorer/weather-overlay",
        params={
            "geographyId": "citywide",
            "timeRangeStart": "2026-03-20T00:00:00Z",
            "timeRangeEnd": "2026-03-20T01:00:00Z",
        },
        headers=operational_manager_headers,
    )
    assert disabled.status_code == 200
    request_id = disabled.json()["overlayRequestId"]

    conflict = app_client.post(
        f"/api/v1/forecast-explorer/weather-overlay/{request_id}/render-events",
        json={"renderStatus": "rendered", "reportedAt": "2026-03-20T03:00:00Z"},
        headers=operational_manager_headers,
    )
    assert conflict.status_code == 409


def test_repository_mark_superseded_noop_and_event_filtering():
    WeatherOverlayRepository.reset_for_tests()
    repo = WeatherOverlayRepository()

    # Cover no-op branch when record does not exist.
    repo.mark_superseded("missing")

    state = WeatherOverlayResponse(
        overlayRequestId="req-1",
        geographyId="citywide",
        timeRangeStart="2026-03-20T00:00:00Z",
        timeRangeEnd="2026-03-20T01:00:00Z",
        weatherMeasure="temperature",
        overlayStatus="visible",
        baseForecastPreserved=True,
        userVisible=True,
        observations=[],
        stateSource="overlay-assembly",
    )
    repo.save_state(state)

    repo.append_render_event(
        "req-1",
        WeatherOverlayRenderEvent(renderStatus="rendered", reportedAt="2026-03-20T03:00:00Z"),
    )
    repo.append_render_event(
        "req-2",
        WeatherOverlayRenderEvent(renderStatus="rendered", reportedAt="2026-03-20T04:00:00Z"),
    )

    req1_events = repo.list_render_events("req-1")
    missing_events = repo.list_render_events("none")
    assert len(req1_events) == 1
    assert req1_events[0].overlay_request_id == "req-1"
    assert missing_events == []


def test_service_record_render_event_errors_and_map_observation_branches():
    WeatherOverlayRepository.reset_for_tests()
    repo = WeatherOverlayRepository()
    service = WeatherOverlayService(
        repository=repo,
        geomet_client=NoopGeoMet(),
        alignment_service=WeatherOverlayAlignmentService(),
    )

    # LookupError path
    try:
        service.record_render_event(
            "missing",
            WeatherOverlayRenderEvent(renderStatus="rendered", reportedAt="2026-03-20T03:00:00Z"),
        )
        assert False, "expected LookupError"
    except LookupError:
        pass

    disabled = WeatherOverlayResponse(
        overlayRequestId="disabled-1",
        geographyId="citywide",
        timeRangeStart="2026-03-20T00:00:00Z",
        timeRangeEnd="2026-03-20T01:00:00Z",
        weatherMeasure=None,
        overlayStatus="disabled",
        baseForecastPreserved=True,
        userVisible=True,
        observations=[],
        stateSource="selection-read-model",
    )
    repo.save_state(disabled)

    # ValueError path
    try:
        service.record_render_event(
            "disabled-1",
            WeatherOverlayRenderEvent(renderStatus="rendered", reportedAt="2026-03-20T03:00:00Z"),
        )
        assert False, "expected ValueError"
    except ValueError:
        pass

    # _map_observations branches
    start = datetime(2026, 3, 20, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 3, 20, 3, 0, tzinfo=timezone.utc)
    mapped = WeatherOverlayService._map_observations(
        rows=[
            {"timestamp": 123, "temperature_c": 1},  # non-datetime non-str -> skip
            {"timestamp": "not-a-date", "temperature_c": 1},  # parse fail -> skip
            {"timestamp": "2026-03-19T23:00:00Z", "temperature_c": 1},  # out of range -> skip
            {"timestamp": "2026-03-20T00:30:00Z", "temperature_c": None},  # missing value -> skip
            {"timestamp": "2026-03-20T01:00:00Z", "snowfall_mm": "bad"},  # cast fail -> skip
            {"timestamp": datetime(2026, 3, 20, 1, 0), "snowfall_mm": 2.0},  # naive datetime path
            {"timestamp": "2026-03-20T02:00:00Z", "snowfall_mm": None, "precipitation_mm": 0.7},  # snowfall fallback
        ],
        weather_measure="snowfall",
        start=start,
        end=end,
    )
    assert len(mapped) == 2
    assert mapped[0].value == 2.0
    assert mapped[1].value == 0.7

    mapped_precipitation = WeatherOverlayService._map_observations(
        rows=[{"timestamp": "2026-03-20T01:30:00Z", "precipitation_mm": 1.4}],
        weather_measure="precipitation",
        start=start,
        end=end,
    )
    assert len(mapped_precipitation) == 1
    assert mapped_precipitation[0].value == 1.4


def test_overlay_models_dataclass_instantiation():
    requested_at = datetime(2026, 3, 20, 0, 0, tzinfo=timezone.utc)
    selection = OverlaySelection(
        overlay_request_id="req",
        geography_id="citywide",
        time_range_start=requested_at,
        time_range_end=datetime(2026, 3, 20, 1, 0, tzinfo=timezone.utc),
        overlay_enabled=True,
        weather_measure="temperature",
        requested_at=requested_at,
    )
    state_record = OverlayStateRecord(
        overlay_request_id="req",
        overlay_status="visible",
        geography_id="citywide",
        time_range_start=requested_at,
        time_range_end=datetime(2026, 3, 20, 1, 0, tzinfo=timezone.utc),
        weather_measure="temperature",
    )
    assert selection.overlay_request_id == "req"
    assert state_record.state_source == "overlay-assembly"
