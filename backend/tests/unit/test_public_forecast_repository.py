from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.repositories.public_forecast_repository import PublicForecastRepository


@pytest.mark.unit
def test_public_forecast_repository_updates_existing_sanitization_outcome(session) -> None:
    repo = PublicForecastRepository(session)
    request = repo.create_request(client_correlation_id="client-1")

    original = repo.record_sanitization_outcome(
        public_forecast_request_id=request.public_forecast_request_id,
        sanitization_status="passed_as_is",
        restricted_detail_detected=False,
        removed_detail_count=0,
    )
    updated = repo.record_sanitization_outcome(
        public_forecast_request_id=request.public_forecast_request_id,
        sanitization_status="sanitized",
        restricted_detail_detected=True,
        removed_detail_count=2,
        sanitization_summary="Removed 2 restricted records.",
        failure_reason="redacted",
    )

    assert original.public_forecast_sanitization_outcome_id == updated.public_forecast_sanitization_outcome_id
    assert updated.sanitization_status == "sanitized"
    assert updated.restricted_detail_detected is True
    assert updated.removed_detail_count == 2
    assert updated.sanitization_summary == "Removed 2 restricted records."
    assert updated.failure_reason == "redacted"


@pytest.mark.unit
def test_public_forecast_repository_records_display_event_without_payload(session) -> None:
    repo = PublicForecastRepository(session)
    request = repo.create_request(client_correlation_id=None)

    event = repo.record_display_event(
        public_forecast_request_id=request.public_forecast_request_id,
        display_outcome="render_failed",
        failure_reason="chart error",
    )

    assert event.public_forecast_payload_id is None
    assert event.failure_reason == "chart error"


@pytest.mark.unit
def test_public_forecast_repository_raises_for_missing_request(session) -> None:
    with pytest.raises(LookupError):
        PublicForecastRepository(session).require_request("missing")
