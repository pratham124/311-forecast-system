from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.surge_evaluation_repository import SurgeCandidateBundle
from app.services.forecast_confidence_service import (
    ForecastConfidenceService,
    build_fallback_confidence_read,
    build_signals_missing_confidence,
    build_unavailable_confidence_read,
    confidence_signal_resolution_status,
)


class StubSettings:
    forecast_confidence_signal_lookback_hours = 48
    forecast_confidence_normal_message = 'Forecast confidence is normal for the current selection.'
    forecast_confidence_signals_missing_message = 'Forecast confidence could not be fully assessed with the currently available signals.'
    forecast_confidence_dismissed_message = 'Recent confidence warnings were reviewed and dismissed for the current selection.'
    forecast_confidence_missing_inputs_message = 'Forecast confidence is reduced because some visualization inputs are missing.'
    forecast_confidence_anomaly_message = 'Forecast confidence is reduced because recent surge conditions were confirmed for the selected service areas.'
    forecast_confidence_combined_message = 'Forecast confidence is reduced because some visualization inputs are missing and recent surge conditions were confirmed for the selected service areas.'


class StubSurgeStateRepository:
    def __init__(self, *, states: dict[str, str] | None = None, error_categories: set[str] | None = None) -> None:
        self.states = states or {}
        self.error_categories = error_categories or set()

    def get_state(self, *, service_category: str, forecast_product: str = "daily"):
        if service_category in self.error_categories:
            raise RuntimeError("state lookup failed")
        current_state = self.states.get(service_category)
        if current_state is None:
            return None
        return type("State", (), {"current_state": current_state, "forecast_product": forecast_product})()


class StubSurgeEvaluationRepository:
    def __init__(self, *, bundles: dict[str, list[SurgeCandidateBundle]] | None = None, error_categories: set[str] | None = None) -> None:
        self.bundles = bundles or {}
        self.error_categories = error_categories or set()

    def list_candidate_bundles_for_window(self, *, service_category: str, detected_at_start: datetime, detected_at_end: datetime):
        if service_category in self.error_categories:
            raise RuntimeError("candidate lookup failed")
        return self.bundles.get(service_category, [])


def _bundle(*, candidate_status: str, outcome: str | None = None, failure_reason: str | None = None) -> SurgeCandidateBundle:
    candidate = type("Candidate", (), {"candidate_status": candidate_status})()
    confirmation = None
    if outcome is not None or failure_reason is not None:
        confirmation = type("Confirmation", (), {"outcome": outcome, "failure_reason": failure_reason})()
    return SurgeCandidateBundle(candidate=candidate, confirmation=confirmation)


def _build_service(*, state_repo=None, evaluation_repo=None) -> ForecastConfidenceService:
    return ForecastConfidenceService(
        surge_state_repository=state_repo,
        surge_evaluation_repository=evaluation_repo,
        settings=StubSettings(),
        logger=__import__("logging").getLogger("test.forecast_confidence"),
    )


def test_missing_visualization_inputs_degrade_confidence() -> None:
    service = _build_service()

    assessment = service.assess_confidence(
        visualization_load_id="load-1",
        forecast_product="daily_1_day",
        service_categories=["Roads"],
        degradation_type="history_missing",
        now=datetime(2026, 4, 11, 12, tzinfo=timezone.utc),
    )

    assert assessment.assessment_status == "degraded_confirmed"
    assert assessment.reason_categories == ("missing_inputs",)
    assert assessment.supporting_signals == ("history_missing",)


def test_active_surge_and_confirmed_candidate_degrade_confidence() -> None:
    service = _build_service(
        state_repo=StubSurgeStateRepository(states={"Roads": "active_surge"}),
        evaluation_repo=StubSurgeEvaluationRepository(
            bundles={"Roads": [_bundle(candidate_status="flagged", outcome="confirmed")]},
        ),
    )

    assessment = service.assess_confidence(
        visualization_load_id="load-2",
        forecast_product="daily_1_day",
        service_categories=["Roads"],
        degradation_type=None,
        now=datetime(2026, 4, 11, 12, tzinfo=timezone.utc),
    )

    assert assessment.assessment_status == "degraded_confirmed"
    assert assessment.reason_categories == ("anomaly",)
    assert assessment.supporting_signals == ("active_surge_state", "recent_confirmed_surge")


def test_missing_inputs_and_anomaly_use_combined_message() -> None:
    service = _build_service(
        state_repo=StubSurgeStateRepository(states={"Roads": "active_surge"}),
        evaluation_repo=StubSurgeEvaluationRepository(),
    )

    assessment = service.assess_confidence(
        visualization_load_id="load-2b",
        forecast_product="daily_1_day",
        service_categories=["Roads", " "],
        degradation_type="history_missing",
        now=datetime(2026, 4, 11, 12, tzinfo=timezone.utc),
    )

    assert assessment.assessment_status == "degraded_confirmed"
    assert assessment.message == StubSettings.forecast_confidence_combined_message


def test_filtered_candidates_are_dismissed_when_no_stronger_signal_exists() -> None:
    service = _build_service(
        state_repo=StubSurgeStateRepository(),
        evaluation_repo=StubSurgeEvaluationRepository(
            bundles={"Roads": [_bundle(candidate_status="flagged", outcome="filtered")]},
        ),
    )

    assessment = service.assess_confidence(
        visualization_load_id="load-3",
        forecast_product="daily_1_day",
        service_categories=["Roads"],
        degradation_type=None,
        now=datetime(2026, 4, 11, 12, tzinfo=timezone.utc),
    )

    assert assessment.assessment_status == "dismissed"
    assert assessment.reason_categories == ("anomaly",)
    assert assessment.supporting_signals == ("filtered_surge_candidate",)


def test_signal_lookup_failures_fall_back_to_signals_missing() -> None:
    service = _build_service(
        state_repo=StubSurgeStateRepository(error_categories={"Roads"}),
        evaluation_repo=StubSurgeEvaluationRepository(),
    )

    assessment = service.assess_confidence(
        visualization_load_id="load-4",
        forecast_product="daily_1_day",
        service_categories=["Roads"],
        degradation_type=None,
        now=datetime(2026, 4, 11, 12, tzinfo=timezone.utc),
    )

    assert assessment.assessment_status == "signals_missing"
    assert assessment.supporting_signals == ("surge_signal_unavailable",)


def test_failed_candidates_and_confirmation_failures_mark_signals_missing() -> None:
    service = _build_service(
        state_repo=StubSurgeStateRepository(),
        evaluation_repo=StubSurgeEvaluationRepository(
            bundles={
                "Roads": [
                    _bundle(candidate_status="detector_failed", outcome="failed"),
                    _bundle(candidate_status=None, failure_reason="confirmation failed"),
                ],
            },
        ),
    )

    assessment = service.assess_confidence(
        visualization_load_id="load-4b",
        forecast_product="daily_1_day",
        service_categories=["Roads"],
        degradation_type=None,
        now=datetime(2026, 4, 11, 12, tzinfo=timezone.utc),
    )

    assert assessment.assessment_status == "signals_missing"
    assert assessment.supporting_signals == ("surge_signal_unavailable",)


def test_unconfirmed_candidates_do_not_change_confidence() -> None:
    service = _build_service(
        state_repo=StubSurgeStateRepository(),
        evaluation_repo=StubSurgeEvaluationRepository(
            bundles={"Roads": [_bundle(candidate_status="flagged")]},
        ),
    )

    assessment = service.assess_confidence(
        visualization_load_id="load-4c",
        forecast_product="daily_1_day",
        service_categories=["Roads"],
        degradation_type=None,
        now=datetime(2026, 4, 11, 12, tzinfo=timezone.utc),
    )

    assert assessment.assessment_status == "normal"
    assert assessment.supporting_signals == ()


def test_weekly_visualizations_skip_daily_anomaly_logic() -> None:
    service = _build_service(
        state_repo=StubSurgeStateRepository(states={"Roads": "active_surge"}),
        evaluation_repo=StubSurgeEvaluationRepository(
            bundles={"Roads": [_bundle(candidate_status="flagged", outcome="confirmed")]},
        ),
    )

    assessment = service.assess_confidence(
        visualization_load_id="load-5",
        forecast_product="weekly_7_day",
        service_categories=["Roads"],
        degradation_type=None,
        now=datetime(2026, 4, 11, 12, tzinfo=timezone.utc),
    )

    assert assessment.assessment_status == "normal"
    assert assessment.supporting_signals == ()


def test_confidence_helpers_return_neutral_non_warning_payloads() -> None:
    fallback = build_fallback_confidence_read()
    unavailable = build_unavailable_confidence_read()
    missing = build_signals_missing_confidence(message="Signals missing.", supporting_signals=["demo"])

    assert fallback.assessment_status == "signals_missing"
    assert unavailable.assessment_status == "signals_missing"
    assert missing.signal_resolution_status == "missing"
    assert confidence_signal_resolution_status("dismissed") == "dismissed"
    assert confidence_signal_resolution_status("normal") == "resolved"


def test_default_messages_and_deduping_cover_blank_signals() -> None:
    partial_settings = type("PartialSettings", (), {"forecast_confidence_signal_lookback_hours": 24})()
    service = ForecastConfidenceService(
        surge_state_repository=None,
        surge_evaluation_repository=None,
        settings=partial_settings,
        logger=__import__("logging").getLogger("test.forecast_confidence.partial"),
    )

    missing = build_signals_missing_confidence(message="Signals missing.", supporting_signals=["demo", "", "demo"])

    assert service._build_degraded_message(["missing_inputs", "anomaly"]) == (
        "Forecast confidence is reduced because some visualization inputs are missing and recent surge conditions were confirmed for the selected service areas."
    )
    assert missing.supporting_signals == ("demo",)
