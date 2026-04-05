from __future__ import annotations

from sqlalchemy import select

from app.models import PublicForecastDisplayEvent, PublicForecastPortalRequest, PublicForecastSanitizationOutcome
from app.services.public_forecast_source_service import PublicForecastSourceService


def test_public_forecast_unavailable_persists_terminal_request(app_client, session):
    response = app_client.get("/api/v1/public/forecast-categories/current?forecastProduct=daily", headers={"X-Client-Correlation-Id": "missing-1"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"

    request = session.scalar(select(PublicForecastPortalRequest))
    assert request is not None
    assert request.portal_status == "unavailable"
    assert request.client_correlation_id == "missing-1"
    assert request.public_forecast_request_id == body["publicForecastRequestId"]

    sanitization = session.scalar(select(PublicForecastSanitizationOutcome))
    assert sanitization is not None
    assert sanitization.sanitization_status == "failed"


def test_public_forecast_error_persists_failed_request(app_client, session, monkeypatch):
    monkeypatch.setattr(
        PublicForecastSourceService,
        "resolve_current_source",
        lambda self, forecast_product="daily": (_ for _ in ()).throw(RuntimeError("boom")),
    )
    response = app_client.get("/api/v1/public/forecast-categories/current?forecastProduct=daily")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"

    request = session.scalar(select(PublicForecastPortalRequest))
    assert request is not None
    assert request.portal_status == "error"
    assert request.failure_reason == "boom"


def test_public_forecast_render_failure_event_is_persisted(app_client, session):
    from tests.contract.test_public_forecast_api import _seed_daily_public_forecast

    _seed_daily_public_forecast(session)
    response = app_client.get("/api/v1/public/forecast-categories/current?forecastProduct=daily")
    request_id = response.json()["publicForecastRequestId"]
    event_response = app_client.post(
        f"/api/v1/public/forecast-categories/{request_id}/display-events",
        json={"displayOutcome": "render_failed", "failureReason": "component crashed"},
    )
    assert event_response.status_code == 202

    event = session.scalar(select(PublicForecastDisplayEvent))
    assert event is not None
    assert event.public_forecast_request_id == request_id
    assert event.display_outcome == "render_failed"
    assert event.failure_reason == "component crashed"
