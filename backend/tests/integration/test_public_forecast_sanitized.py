from __future__ import annotations

from sqlalchemy import select

from app.models import PublicForecastSanitizationOutcome, PublicForecastVisualizationPayload
from tests.contract.test_public_forecast_api import _seed_daily_public_forecast


def test_public_forecast_sanitized_response_persists_incomplete_coverage(app_client, session):
    _seed_daily_public_forecast(session, include_restricted_bucket=True)
    response = app_client.get("/api/v1/public/forecast-categories/current", headers={"X-Client-Correlation-Id": "sanitized-1"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["coverageStatus"] == "incomplete"
    assert body["sanitizationStatus"] == "sanitized"

    sanitization = session.scalar(select(PublicForecastSanitizationOutcome))
    assert sanitization is not None
    assert sanitization.removed_detail_count == 1
    assert sanitization.public_forecast_request_id == body["publicForecastRequestId"]

    payload = session.scalar(select(PublicForecastVisualizationPayload))
    assert payload is not None
    assert payload.coverage_status == "incomplete"
    assert "Transit" in (payload.coverage_message or "")
