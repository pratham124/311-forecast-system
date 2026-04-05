from __future__ import annotations

from sqlalchemy import select

from app.models import PublicForecastDisplayEvent, PublicForecastPortalRequest, PublicForecastSanitizationOutcome, PublicForecastVisualizationPayload
from tests.contract.test_public_forecast_api import _seed_daily_public_forecast, _seed_weekly_public_forecast


def test_public_forecast_success_persists_request_payload_and_display_event(app_client, session):
    _seed_daily_public_forecast(session)
    response = app_client.get("/api/v1/public/forecast-categories/current?forecastProduct=daily", headers={"X-Client-Correlation-Id": "success-1"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"

    request = session.scalar(select(PublicForecastPortalRequest))
    assert request is not None
    assert request.portal_status == "available"
    assert request.client_correlation_id == "success-1"
    assert request.public_forecast_request_id == body["publicForecastRequestId"]

    payload = session.scalar(select(PublicForecastVisualizationPayload))
    assert payload is not None
    assert payload.coverage_status == "complete"

    sanitization = session.scalar(select(PublicForecastSanitizationOutcome))
    assert sanitization is not None
    assert sanitization.sanitization_status == "passed_as_is"

    event_response = app_client.post(
        f"/api/v1/public/forecast-categories/{body['publicForecastRequestId']}/display-events",
        json={"displayOutcome": "rendered"},
    )
    assert event_response.status_code == 202
    event = session.scalar(select(PublicForecastDisplayEvent))
    assert event is not None
    assert event.display_outcome == "rendered"


def test_public_weekly_forecast_success_uses_weekly_marker(app_client, session):
    _seed_weekly_public_forecast(session)
    response = app_client.get("/api/v1/public/forecast-categories/current?forecastProduct=weekly", headers={"X-Client-Correlation-Id": "weekly-1"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["forecastWindowLabel"].startswith("2026-03-23")
