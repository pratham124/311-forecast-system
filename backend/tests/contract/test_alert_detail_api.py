from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.routes import alert_details as alert_details_route
from app.repositories.alert_detail_repository import AlertDetailRepository
from app.schemas.alert_details import (
    AlertAnomaliesComponentRead,
    AlertDetailRead,
    AlertDetailRenderEventResponse,
    AlertDistributionComponentRead,
    AlertDistributionPointRead,
    AlertDriversComponentRead,
    AlertScopeRead,
)


pytestmark = pytest.mark.contract


def _detail(*, alert_source: str, view_status: str, failure_reason: str | None = None) -> AlertDetailRead:
    return AlertDetailRead(
        alert_detail_load_id="detail-load-1",
        alert_source=alert_source,
        alert_id=f"{alert_source}-1",
        correlation_id=f"{alert_source}-corr-1",
        alert_triggered_at=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
        overall_delivery_status="partial_delivery",
        forecast_product="daily",
        forecast_reference_id="forecast-1",
        forecast_window_type="hourly",
        window_start=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
        window_end=datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
        primary_metric_label="Forecast",
        primary_metric_value=12.0,
        secondary_metric_label="Threshold",
        secondary_metric_value=8.0,
        scope=AlertScopeRead(service_category="Roads"),
        view_status=view_status,
        failure_reason=failure_reason,
        distribution=AlertDistributionComponentRead(
            status="available",
            granularity="hourly",
            summary_value=12.0,
            points=[
                AlertDistributionPointRead(
                    label="2026-04-01T10:00:00+00:00",
                    bucket_start=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
                    bucket_end=datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
                    p10=9.0,
                    p50=12.0,
                    p90=16.0,
                    is_alerted_bucket=True,
                )
            ],
        ),
        drivers=AlertDriversComponentRead(
            status="unavailable",
            unavailable_reason="No compatible forecast model is currently available.",
        ),
        anomalies=AlertAnomaliesComponentRead(
            status="unavailable",
            unavailable_reason="No recent surge anomalies were recorded.",
        ),
    )


def test_alert_detail_api_requires_auth_and_validates_inputs(app_client, viewer_headers, planner_headers, session) -> None:
    repository = AlertDetailRepository(session)
    load = repository.create_load(
        alert_source="threshold_alert",
        alert_id="threshold-event-1",
        requested_by_subject="different-user",
    )
    session.commit()

    assert app_client.get("/api/v1/alert-details/threshold_alert/threshold-event-1").status_code == 401
    assert app_client.get(
        "/api/v1/alert-details/threshold_alert/threshold-event-1",
        headers=viewer_headers,
    ).status_code == 403
    assert app_client.post(
        f"/api/v1/alert-details/{load.alert_detail_load_id}/render-events",
        json={"renderStatus": "rendered"},
    ).status_code == 401
    assert app_client.post(
        f"/api/v1/alert-details/{load.alert_detail_load_id}/render-events",
        json={"renderStatus": "rendered"},
        headers=viewer_headers,
    ).status_code == 403

    unsupported = app_client.get(
        "/api/v1/alert-details/not_supported/threshold-event-1",
        headers=planner_headers,
    )
    assert unsupported.status_code == 422

    validation = app_client.post(
        f"/api/v1/alert-details/{load.alert_detail_load_id}/render-events",
        json={"renderStatus": "render_failed"},
        headers=planner_headers,
    )
    assert validation.status_code == 422
    assert "failureReason" in validation.text

    forbidden = app_client.post(
        f"/api/v1/alert-details/{load.alert_detail_load_id}/render-events",
        json={"renderStatus": "rendered"},
        headers=planner_headers,
    )
    assert forbidden.status_code == 403

    missing = app_client.post(
        "/api/v1/alert-details/missing-load/render-events",
        json={"renderStatus": "rendered"},
        headers=planner_headers,
    )
    assert missing.status_code == 404


def test_alert_detail_contract_payloads_and_not_found(app_client, planner_headers, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def get_alert_detail(self, *, alert_source: str, alert_id: str, claims: dict) -> AlertDetailRead:
            assert claims["roles"] == ["CityPlanner"]
            if alert_id == "missing-alert":
                raise HTTPException(status_code=404, detail="Alert event not found")
            if alert_id == "error-alert":
                return _detail(
                    alert_source=alert_source,
                    view_status="error",
                    failure_reason="Forecast version not found.",
                )
            return _detail(alert_source=alert_source, view_status="partial")

        def record_render_event(self, *, alert_detail_load_id: str, payload, claims: dict) -> AlertDetailRenderEventResponse:
            assert alert_detail_load_id == "detail-load-1"
            assert claims["roles"] == ["CityPlanner"]
            return AlertDetailRenderEventResponse(
                alert_detail_load_id=alert_detail_load_id,
                recorded_outcome_status=payload.render_status,
                message="Render event recorded.",
            )

    monkeypatch.setattr(alert_details_route, "build_alert_detail_service", lambda *args, **kwargs: FakeService())

    partial = app_client.get(
        "/api/v1/alert-details/threshold_alert/partial-alert",
        headers=planner_headers,
    )
    assert partial.status_code == 200
    partial_body = partial.json()
    assert partial_body["alertSource"] == "threshold_alert"
    assert partial_body["viewStatus"] == "partial"
    assert partial_body["distribution"]["status"] == "available"
    assert partial_body["drivers"]["status"] == "unavailable"

    error = app_client.get(
        "/api/v1/alert-details/surge_alert/error-alert",
        headers=planner_headers,
    )
    assert error.status_code == 200
    error_body = error.json()
    assert error_body["alertSource"] == "surge_alert"
    assert error_body["viewStatus"] == "error"
    assert error_body["failureReason"] == "Forecast version not found."

    missing = app_client.get(
        "/api/v1/alert-details/threshold_alert/missing-alert",
        headers=planner_headers,
    )
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Alert event not found"

    render_event = app_client.post(
        "/api/v1/alert-details/detail-load-1/render-events",
        json={"renderStatus": "rendered"},
        headers=planner_headers,
    )
    assert render_event.status_code == 202
    assert render_event.json() == {
        "alertDetailLoadId": "detail-load-1",
        "recordedOutcomeStatus": "rendered",
        "message": "Render event recorded.",
    }
