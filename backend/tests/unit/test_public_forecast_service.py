from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.public_forecast import PublicForecastDisplayEventRequest
from app.services.public_forecast_sanitization_service import SanitizedPublicForecast
from app.services.public_forecast_service import PublicForecastService, _coverage_message, _demand_level
from app.services.public_forecast_source_service import PublicForecastBucketRow, ResolvedPublicForecastSource


class FakeRepository:
    def __init__(self) -> None:
        self.request_id = "request-1"
        self.finalized: list[dict[str, object]] = []
        self.display_events: list[dict[str, object]] = []

    def create_request(self, *, client_correlation_id: str | None, approved_forecast_version_id: str | None = None, approved_forecast_product: str | None = None):
        class Record:
            public_forecast_request_id = "request-1"

        return Record()

    def finalize_request(self, public_forecast_request_id: str, **kwargs):
        self.finalized.append({"id": public_forecast_request_id, **kwargs})
        return type("Record", (), {"public_forecast_request_id": public_forecast_request_id})()

    def record_sanitization_outcome(self, **kwargs):
        return kwargs

    def create_payload(self, **kwargs):
        return kwargs

    def require_request(self, public_forecast_request_id: str):
        if public_forecast_request_id != "request-1":
            raise LookupError("missing")
        return object()

    def record_display_event(self, **kwargs):
        self.display_events.append(kwargs)
        return kwargs


class StaticSourceService:
    def __init__(self, source):
        self.source = source

    def resolve_current_source(self, forecast_product: str = "daily"):
        if isinstance(self.source, Exception):
            raise self.source
        return self.source


class StaticSanitizationService:
    def __init__(self, result: SanitizedPublicForecast):
        self.result = result

    def sanitize(self, source):
        return self.result


def test_service_assembles_available_view():
    repository = FakeRepository()
    source = ResolvedPublicForecastSource(
        forecast_product="daily",
        approved_forecast_version_id="forecast-1",
        forecast_window_label="2026-03-20 to 2026-03-21",
        published_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
        source_cleaned_dataset_version_id="dataset-1",
        category_rows=[PublicForecastBucketRow(service_category="Roads", forecast_demand_value=12)],
        source_category_count=1,
    )
    sanitization = SanitizedPublicForecast(
        sanitization_status="passed_as_is",
        restricted_detail_detected=False,
        removed_detail_count=0,
        sanitization_summary=None,
        failure_reason=None,
        category_rows=source.category_rows,
        removed_categories=[],
    )
    service = PublicForecastService(
        repository=repository,
        source_service=StaticSourceService(source),
        sanitization_service=StaticSanitizationService(sanitization),
    )
    view = service.get_current_public_forecast(client_correlation_id="client-1")
    assert view.status == "available"
    assert view.category_summaries is not None
    assert view.category_summaries[0].service_category == "Roads"


def test_service_maps_missing_source_to_unavailable():
    service = PublicForecastService(
        repository=FakeRepository(),
        source_service=StaticSourceService(None),
        sanitization_service=StaticSanitizationService(
            SanitizedPublicForecast(
                sanitization_status="failed",
                restricted_detail_detected=False,
                removed_detail_count=0,
                sanitization_summary=None,
                failure_reason="no-op",
                category_rows=[],
                removed_categories=[],
            )
        ),
    )
    view = service.get_current_public_forecast(client_correlation_id=None)
    assert view.status == "unavailable"


def test_service_maps_blocked_sanitization_to_error():
    repository = FakeRepository()
    source = ResolvedPublicForecastSource(
        forecast_product="daily",
        approved_forecast_version_id="forecast-1",
        forecast_window_label="2026-03-20 to 2026-03-21",
        published_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
        source_cleaned_dataset_version_id="dataset-1",
        category_rows=[],
        source_category_count=0,
    )
    service = PublicForecastService(
        repository=repository,
        source_service=StaticSourceService(source),
        sanitization_service=StaticSanitizationService(
            SanitizedPublicForecast(
                sanitization_status="blocked",
                restricted_detail_detected=True,
                removed_detail_count=1,
                sanitization_summary=None,
                failure_reason="Forecast data could not be prepared safely for public display.",
                category_rows=[],
                removed_categories=["Transit"],
            )
        ),
    )
    view = service.get_current_public_forecast(client_correlation_id=None)
    assert view.status == "error"


def test_service_records_display_events():
    repository = FakeRepository()
    service = PublicForecastService(
        repository=repository,
        source_service=StaticSourceService(None),
        sanitization_service=StaticSanitizationService(
            SanitizedPublicForecast(
                sanitization_status="failed",
                restricted_detail_detected=False,
                removed_detail_count=0,
                sanitization_summary=None,
                failure_reason="x",
                category_rows=[],
                removed_categories=[],
            )
        ),
    )
    service.record_display_event("request-1", PublicForecastDisplayEventRequest(displayOutcome="rendered"))
    assert repository.display_events[0]["display_outcome"] == "rendered"


def test_service_uses_higher_weekly_demand_thresholds():
    repository = FakeRepository()
    source = ResolvedPublicForecastSource(
        forecast_product="weekly",
        approved_forecast_version_id="forecast-weekly-1",
        forecast_window_label="Week of 2026-03-23 to 2026-03-30",
        published_at=datetime(2026, 3, 23, tzinfo=timezone.utc),
        source_cleaned_dataset_version_id="dataset-1",
        category_rows=[PublicForecastBucketRow(service_category="Roads", forecast_demand_value=90)],
        source_category_count=1,
    )
    sanitization = SanitizedPublicForecast(
        sanitization_status="passed_as_is",
        restricted_detail_detected=False,
        removed_detail_count=0,
        sanitization_summary=None,
        failure_reason=None,
        category_rows=source.category_rows,
        removed_categories=[],
    )
    service = PublicForecastService(
        repository=repository,
        source_service=StaticSourceService(source),
        sanitization_service=StaticSanitizationService(sanitization),
    )
    view = service.get_current_public_forecast(client_correlation_id=None, forecast_product="weekly")
    assert view.category_summaries is not None
    assert view.category_summaries[0].demand_level_summary == "Moderate demand expected"


def test_public_forecast_service_helper_branches():
    assert _coverage_message([]) == "Some forecast categories are unavailable in the current public view."
    assert _coverage_message(["Roads", "Waste", "Transit", "Parks"]) == (
        "Some categories are not shown in this public forecast: Roads, Waste, Transit, and more."
    )

    assert _demand_level(450, "weekly") == "Very high demand expected"
    assert _demand_level(250, "weekly") == "High demand expected"
    assert _demand_level(10, "weekly") == "Lower demand expected"
    assert _demand_level(120, "daily") == "Very high demand expected"
    assert _demand_level(60, "daily") == "High demand expected"
    assert _demand_level(10, "daily") == "Lower demand expected"
