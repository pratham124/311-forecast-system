from __future__ import annotations

import json
from datetime import datetime, timezone

from app.core.config import get_settings
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.surge_configuration_repository import SurgeConfigurationRepository
from app.repositories.surge_state_repository import SurgeStateRepository
from app.repositories.visualization_repository import VisualizationRepository
from app.schemas.forecast_visualization import VisualizationRenderEvent

from tests.integration.test_forecast_visualization_success import _build_service, _seed


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


def test_visualization_persists_degraded_confidence_from_active_surge(session) -> None:
    _seed(session, include_history=True)
    _seed_active_surge_state(session)

    service = _build_service(session)
    response = service.get_current_visualization(forecast_product="daily_1_day", service_category="Roads")
    session.commit()

    assert response.forecast_confidence is not None
    assert response.forecast_confidence.assessment_status == "degraded_confirmed"
    assert "anomaly" in response.forecast_confidence.reason_categories

    record = VisualizationRepository(session).require_load_record(response.visualization_load_id)
    assert record.confidence_assessment_status == "degraded_confirmed"
    assert record.confidence_indicator_state == "display_required"
    assert json.loads(record.confidence_reason_categories_json or "[]") == ["anomaly"]


def test_visualization_fallback_replaces_snapshot_confidence_with_signals_missing(session) -> None:
    _seed(session, include_history=True)
    _seed_active_surge_state(session)
    service = _build_service(session)

    successful = service.get_current_visualization(forecast_product="daily_1_day", service_category="Roads")
    session.commit()
    assert successful.forecast_confidence is not None
    assert successful.forecast_confidence.assessment_status == "degraded_confirmed"

    marker = ForecastRepository(session).get_current_marker(get_settings().forecast_product_name)
    session.delete(marker)
    session.commit()

    fallback = service.get_current_visualization(forecast_product="daily_1_day", service_category="Roads")
    session.commit()

    assert fallback.view_status == "fallback_shown"
    assert fallback.forecast_confidence is not None
    assert fallback.forecast_confidence.assessment_status == "signals_missing"
    assert fallback.forecast_confidence.supporting_signals == ["fallback_confidence_unresolved"]


def test_confidence_render_events_persist_without_changing_chart_status(session) -> None:
    _seed(session, include_history=True)
    _seed_active_surge_state(session)
    service = _build_service(session)

    response = service.get_current_visualization(forecast_product="daily_1_day", service_category="Roads")
    session.commit()

    service.record_confidence_render_event(
        response.visualization_load_id,
        VisualizationRenderEvent.model_validate({"renderStatus": "render_failed", "failureReason": "banner crashed"}),
    )
    session.commit()

    record = VisualizationRepository(session).require_load_record(response.visualization_load_id)
    assert record.status == "success"
    assert record.confidence_render_status == "render_failed"
    assert record.confidence_indicator_state == "render_failed"
    assert record.confidence_render_failure_reason == "banner crashed"
