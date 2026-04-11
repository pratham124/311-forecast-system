from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.surge_configuration_repository import SurgeConfigurationRepository
from app.repositories.surge_state_repository import SurgeStateRepository

from tests.contract.test_forecast_visualization_api import _seed_daily_visualization


def _seed_active_surge_state(session, *, service_category: str = "Roads") -> None:
    configuration = SurgeConfigurationRepository(session).create_configuration(
        service_category=service_category,
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        rolling_baseline_window_count=7,
        notification_channels=["dashboard"],
        operational_manager_id="manager-1",
    )
    evaluated_at = datetime(2026, 4, 11, 10, tzinfo=timezone.utc)
    SurgeStateRepository(session).reconcile_state(
        surge_detection_configuration_id=configuration.surge_detection_configuration_id,
        service_category=service_category,
        current_state="active_surge",
        notification_armed=False,
        active_since=evaluated_at,
        returned_to_normal_at=None,
        last_surge_candidate_id=None,
        last_confirmation_outcome_id=None,
        last_notification_event_id=None,
        last_evaluated_at=evaluated_at,
    )
    session.commit()


def test_get_current_visualization_includes_forecast_confidence_payload(app_client, operational_manager_headers, session) -> None:
    _seed_daily_visualization(session)

    response = app_client.get(
        "/api/v1/forecast-visualizations/current",
        params={"forecastProduct": "daily_1_day"},
        headers=operational_manager_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["forecastConfidence"]["assessmentStatus"] == "normal"
    assert body["forecastConfidence"]["indicatorState"] == "not_required"


def test_get_current_visualization_uses_degraded_confidence_for_active_surge(app_client, operational_manager_headers, session) -> None:
    _seed_daily_visualization(session)
    _seed_active_surge_state(session)

    response = app_client.get(
        "/api/v1/forecast-visualizations/current",
        params=[("forecastProduct", "daily_1_day"), ("serviceCategory", "Roads")],
        headers=operational_manager_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["forecastConfidence"]["assessmentStatus"] == "degraded_confirmed"
    assert "anomaly" in body["forecastConfidence"]["reasonCategories"]


def test_post_confidence_render_event_contract(app_client, operational_manager_headers, viewer_headers, session) -> None:
    _seed_daily_visualization(session)
    load = app_client.get(
        "/api/v1/forecast-visualizations/current",
        params={"forecastProduct": "daily_1_day"},
        headers=operational_manager_headers,
    ).json()
    visualization_load_id = load["visualizationLoadId"]

    rendered = app_client.post(
        f"/api/v1/forecast-visualizations/{visualization_load_id}/confidence-render-events",
        headers=operational_manager_headers,
        json={"renderStatus": "rendered"},
    )
    assert rendered.status_code == 202

    missing = app_client.post(
        "/api/v1/forecast-visualizations/missing/confidence-render-events",
        headers=operational_manager_headers,
        json={"renderStatus": "rendered"},
    )
    assert missing.status_code == 404

    unauthorized = app_client.post(
        f"/api/v1/forecast-visualizations/{visualization_load_id}/confidence-render-events",
        json={"renderStatus": "rendered"},
    )
    assert unauthorized.status_code == 401

    forbidden = app_client.post(
        f"/api/v1/forecast-visualizations/{visualization_load_id}/confidence-render-events",
        headers=viewer_headers,
        json={"renderStatus": "rendered"},
    )
    assert forbidden.status_code == 403

    invalid = app_client.post(
        f"/api/v1/forecast-visualizations/{visualization_load_id}/confidence-render-events",
        headers=operational_manager_headers,
        json={"renderStatus": "render_failed"},
    )
    assert invalid.status_code == 422
