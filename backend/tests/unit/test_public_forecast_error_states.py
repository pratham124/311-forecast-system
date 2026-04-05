from __future__ import annotations

import pytest

from app.schemas.public_forecast import (
    PublicForecastCategorySummary,
    PublicForecastDisplayEventRequest,
    PublicForecastView,
)


def test_category_summary_requires_value_or_summary():
    with pytest.raises(ValueError):
        PublicForecastCategorySummary(serviceCategory="Roads")


def test_error_state_requires_status_message():
    with pytest.raises(ValueError):
        PublicForecastView(publicForecastRequestId="request-1", status="error")


def test_unavailable_state_requires_status_message():
    with pytest.raises(ValueError):
        PublicForecastView(publicForecastRequestId="request-1", status="unavailable")


def test_render_failed_event_requires_failure_reason():
    with pytest.raises(ValueError):
        PublicForecastDisplayEventRequest(displayOutcome="render_failed")


def test_available_state_rejects_blocked_sanitization():
    with pytest.raises(ValueError):
        PublicForecastView(
            publicForecastRequestId="request-1",
            status="available",
            forecastWindowLabel="2026-03-20 to 2026-03-21",
            publishedAt="2026-03-20T00:00:00Z",
            coverageStatus="complete",
            sanitizationStatus="blocked",
            categorySummaries=[{"serviceCategory": "Roads", "forecastDemandValue": 12}],
        )


def test_available_incomplete_state_requires_coverage_message():
    with pytest.raises(ValueError):
        PublicForecastView(
            publicForecastRequestId="request-1",
            status="available",
            forecastWindowLabel="2026-03-20 to 2026-03-21",
            publishedAt="2026-03-20T00:00:00Z",
            coverageStatus="incomplete",
            sanitizationStatus="passed_as_is",
            categorySummaries=[{"serviceCategory": "Roads", "forecastDemandValue": 12}],
        )


def test_available_state_requires_all_payload_fields():
    with pytest.raises(ValueError):
        PublicForecastView(
            publicForecastRequestId="request-1",
            status="available",
            forecastWindowLabel="2026-03-20 to 2026-03-21",
        )
