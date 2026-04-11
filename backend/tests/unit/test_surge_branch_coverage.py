from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models import (
    IngestionRun,
    SurgeCandidate,
    SurgeDetectionConfiguration,
    SurgeEvaluationRun,
    SurgeNotificationChannelAttempt,
    SurgeNotificationEvent,
)
from app.pipelines.surge_alert_evaluation_pipeline import SurgeAlertEvaluationPipeline
from app.repositories.surge_evaluation_repository import SurgeEvaluationRepository
from app.repositories.surge_notification_event_repository import SurgeNotificationEventRepository
from app.services.surge_alert_review_service import SurgeAlertReviewService
from app.services.surge_confirmation_service import SurgeConfirmationService
from app.services.surge_detection_service import SurgeDetectionError, SurgeDetectionService, SurgeMetrics
from app.services.surge_scope_service import SurgeScopeService
from app.services import surge_alert_trigger_service as trigger_module


def _transition() -> SimpleNamespace:
    return SimpleNamespace(
        current_state="normal",
        notification_armed=True,
        active_since=None,
        returned_to_normal_at=None,
    )


@pytest.mark.unit
def test_surge_pipeline_handles_missing_forecast_bucket_branch() -> None:
    finalized: list[dict[str, object]] = []
    reconciled: list[dict[str, object]] = []
    pipeline = SurgeAlertEvaluationPipeline(
        scope_service=SimpleNamespace(
            list_scopes=lambda **kwargs: [
                SimpleNamespace(
                    service_category="Roads",
                    evaluation_window_start=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
                    evaluation_window_end=datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
                    actual_demand_value=5.0,
                    forecast_run_id=None,
                    forecast_version_id=None,
                    forecast_p50_value=None,
                )
            ]
        ),
        configuration_repository=SimpleNamespace(
            find_active_configuration=lambda **kwargs: SimpleNamespace(
                configuration=SimpleNamespace(
                    surge_detection_configuration_id="cfg-1",
                    rolling_baseline_window_count=7,
                    z_score_threshold=2.0,
                    percent_above_forecast_floor=100.0,
                ),
                notification_channels=["email"],
            )
        ),
        evaluation_repository=SimpleNamespace(
            create_run=lambda **kwargs: SimpleNamespace(surge_evaluation_run_id="run-1"),
            create_candidate=lambda **kwargs: SimpleNamespace(
                surge_candidate_id="candidate-1",
                failure_reason=kwargs["failure_reason"],
            ),
            create_confirmation_outcome=lambda **kwargs: SimpleNamespace(surge_confirmation_outcome_id="confirmation-1"),
            finalize_run=lambda run_id, **kwargs: finalized.append({"run_id": run_id, **kwargs}) or SimpleNamespace(
                surge_evaluation_run_id=run_id,
                status=kwargs["status"],
                failure_summary=kwargs["failure_summary"],
            ),
        ),
        state_repository=SimpleNamespace(
            get_state=lambda **kwargs: None,
            reconcile_state=lambda **kwargs: reconciled.append(kwargs),
        ),
        event_repository=SimpleNamespace(create_event=lambda **kwargs: None, add_attempt=lambda **kwargs: None),
        detection_service=SimpleNamespace(compute_metrics=lambda **kwargs: None),
        confirmation_service=SimpleNamespace(evaluate=lambda **kwargs: None),
        state_service=SimpleNamespace(transition=lambda **kwargs: _transition()),
        delivery_service=SimpleNamespace(deliver=lambda **kwargs: None),
        logger=SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None),
    )

    completed = pipeline.run(ingestion_run_id="ing-1", trigger_source="ingestion_completion")

    assert completed.status == "completed_with_failures"
    assert completed.failure_summary == "Roads: missing forecast bucket"
    assert finalized[0]["candidate_count"] == 1
    assert reconciled[0]["last_confirmation_outcome_id"] == "confirmation-1"


@pytest.mark.unit
def test_surge_pipeline_handles_below_threshold_branch() -> None:
    finalized: list[dict[str, object]] = []
    reconciled: list[dict[str, object]] = []
    metrics = SurgeMetrics(
        actual_demand_value=3.0,
        forecast_p50_value=2.0,
        residual_value=1.0,
        residual_z_score=1.0,
        percent_above_forecast=50.0,
        rolling_baseline_mean=0.0,
        rolling_baseline_stddev=1.0,
    )
    pipeline = SurgeAlertEvaluationPipeline(
        scope_service=SimpleNamespace(
            list_scopes=lambda **kwargs: [
                SimpleNamespace(
                    service_category="Roads",
                    evaluation_window_start=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
                    evaluation_window_end=datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
                    actual_demand_value=3.0,
                    forecast_run_id="forecast-run-1",
                    forecast_version_id="forecast-version-1",
                    forecast_p50_value=2.0,
                )
            ]
        ),
        configuration_repository=SimpleNamespace(
            find_active_configuration=lambda **kwargs: SimpleNamespace(
                configuration=SimpleNamespace(
                    surge_detection_configuration_id="cfg-1",
                    rolling_baseline_window_count=7,
                    z_score_threshold=2.0,
                    percent_above_forecast_floor=100.0,
                ),
                notification_channels=["email"],
            )
        ),
        evaluation_repository=SimpleNamespace(
            create_run=lambda **kwargs: SimpleNamespace(surge_evaluation_run_id="run-1"),
            create_candidate=lambda **kwargs: SimpleNamespace(surge_candidate_id="candidate-1"),
            create_confirmation_outcome=lambda **kwargs: SimpleNamespace(surge_confirmation_outcome_id="confirmation-1"),
            finalize_run=lambda run_id, **kwargs: finalized.append({"run_id": run_id, **kwargs}) or SimpleNamespace(
                surge_evaluation_run_id=run_id,
                status=kwargs["status"],
                failure_summary=kwargs["failure_summary"],
            ),
        ),
        state_repository=SimpleNamespace(
            get_state=lambda **kwargs: None,
            reconcile_state=lambda **kwargs: reconciled.append(kwargs),
        ),
        event_repository=SimpleNamespace(create_event=lambda **kwargs: None, add_attempt=lambda **kwargs: None),
        detection_service=SimpleNamespace(compute_metrics=lambda **kwargs: metrics),
        confirmation_service=SimpleNamespace(evaluate=lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not confirm"))),
        state_service=SimpleNamespace(transition=lambda **kwargs: _transition()),
        delivery_service=SimpleNamespace(deliver=lambda **kwargs: None),
        logger=SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None),
    )

    completed = pipeline.run(ingestion_run_id="ing-1", trigger_source="ingestion_completion")

    assert completed.status == "completed"
    assert finalized[0]["candidate_count"] == 1
    assert reconciled[0]["last_confirmation_outcome_id"] is None
    assert reconciled[0]["last_notification_event_id"] is None


@pytest.mark.unit
def test_surge_pipeline_skips_scope_without_active_configuration() -> None:
    finalized: list[dict[str, object]] = []
    pipeline = SurgeAlertEvaluationPipeline(
        scope_service=SimpleNamespace(
            list_scopes=lambda **kwargs: [
                SimpleNamespace(
                    service_category="Roads",
                    evaluation_window_start=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
                    evaluation_window_end=datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
                    actual_demand_value=3.0,
                    forecast_run_id="forecast-run-1",
                    forecast_version_id="forecast-version-1",
                    forecast_p50_value=2.0,
                )
            ]
        ),
        configuration_repository=SimpleNamespace(find_active_configuration=lambda **kwargs: None),
        evaluation_repository=SimpleNamespace(
            create_run=lambda **kwargs: SimpleNamespace(surge_evaluation_run_id="run-1"),
            create_candidate=lambda **kwargs: (_ for _ in ()).throw(AssertionError("should skip candidate creation")),
            create_confirmation_outcome=lambda **kwargs: (_ for _ in ()).throw(AssertionError("should skip confirmation")),
            finalize_run=lambda run_id, **kwargs: finalized.append({"run_id": run_id, **kwargs}) or SimpleNamespace(
                surge_evaluation_run_id=run_id,
                status=kwargs["status"],
                failure_summary=kwargs["failure_summary"],
            ),
        ),
        state_repository=SimpleNamespace(get_state=lambda **kwargs: None, reconcile_state=lambda **kwargs: None),
        event_repository=SimpleNamespace(create_event=lambda **kwargs: None, add_attempt=lambda **kwargs: None),
        detection_service=SimpleNamespace(compute_metrics=lambda **kwargs: None),
        confirmation_service=SimpleNamespace(evaluate=lambda **kwargs: None),
        state_service=SimpleNamespace(transition=lambda **kwargs: _transition()),
        delivery_service=SimpleNamespace(deliver=lambda **kwargs: None),
        logger=SimpleNamespace(info=lambda *args, **kwargs: None, warning=lambda *args, **kwargs: None),
    )

    completed = pipeline.run(ingestion_run_id="ing-1", trigger_source="ingestion_completion")

    assert completed.status == "completed"
    assert finalized == [{
        "run_id": "run-1",
        "status": "completed",
        "evaluated_scope_count": 1,
        "candidate_count": 0,
        "confirmed_count": 0,
        "notification_created_count": 0,
        "failure_summary": None,
    }]


@pytest.mark.unit
def test_surge_evaluation_repository_missing_and_filter_paths(session) -> None:
    repository = SurgeEvaluationRepository(session)
    with pytest.raises(ValueError):
        repository.finalize_run(
            "missing",
            status="completed",
            evaluated_scope_count=0,
            candidate_count=0,
            confirmed_count=0,
            notification_created_count=0,
        )

    now = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    session.add_all(
        [
            IngestionRun(run_id="ing-1", trigger_type="manual", status="success", started_at=now),
            IngestionRun(run_id="ing-2", trigger_type="manual", status="success", started_at=now),
        ]
    )
    first = repository.create_run(ingestion_run_id="ing-1", trigger_source="ingestion_completion")
    second = repository.create_run(ingestion_run_id="ing-2", trigger_source="ingestion_completion")
    first.started_at = now
    second.started_at = now + timedelta(minutes=1)
    repository.create_candidate(
        surge_evaluation_run_id=first.surge_evaluation_run_id,
        surge_detection_configuration_id=None,
        forecast_run_id=None,
        forecast_version_id=None,
        service_category="Roads",
        evaluation_window_start=now,
        evaluation_window_end=now + timedelta(hours=1),
        actual_demand_value=1.0,
        forecast_p50_value=None,
        residual_value=None,
        residual_z_score=None,
        percent_above_forecast=None,
        rolling_baseline_mean=None,
        rolling_baseline_stddev=None,
        candidate_status="detector_failed",
        detected_at=now,
        correlation_id="corr",
        failure_reason="boom",
    )
    repository.finalize_run(
        first.surge_evaluation_run_id,
        status="completed_with_failures",
        evaluated_scope_count=1,
        candidate_count=1,
        confirmed_count=0,
        notification_created_count=0,
        failure_summary="boom",
    )
    repository.finalize_run(
        second.surge_evaluation_run_id,
        status="completed",
        evaluated_scope_count=0,
        candidate_count=0,
        confirmed_count=0,
        notification_created_count=0,
    )
    session.commit()

    assert repository.get_run(first.surge_evaluation_run_id) is not None
    assert len(repository.list_runs(ingestion_run_id="ing-1")) == 1
    assert len(repository.list_runs(status="completed")) == 1
    assert repository.get_run_detail("missing") is None
    assert repository.get_candidate_bundle("missing") is None
    detail = repository.get_run_detail(first.surge_evaluation_run_id)
    assert detail is not None
    assert detail.candidates[0].confirmation is None


@pytest.mark.unit
def test_surge_notification_event_repository_filter_and_missing_paths(session) -> None:
    now = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    session.add(IngestionRun(run_id="ing-1", trigger_type="manual", status="success", started_at=now))
    config = SurgeDetectionConfiguration(
        surge_detection_configuration_id="cfg-1",
        service_category="Roads",
        forecast_product="daily",
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        rolling_baseline_window_count=7,
        notification_channels_json='["email"]',
        operational_manager_id="manager-1",
        status="active",
        effective_from=now,
    )
    evaluation = SurgeEvaluationRun(
        surge_evaluation_run_id="run-1",
        ingestion_run_id="ing-1",
        trigger_source="ingestion_completion",
        started_at=now,
        status="completed",
    )
    candidate = SurgeCandidate(
        surge_candidate_id="candidate-1",
        surge_evaluation_run_id="run-1",
        surge_detection_configuration_id="cfg-1",
        forecast_run_id=None,
        forecast_version_id=None,
        service_category="Roads",
        evaluation_window_start=now,
        evaluation_window_end=now + timedelta(hours=1),
        actual_demand_value=5.0,
        forecast_p50_value=2.0,
        residual_value=3.0,
        residual_z_score=4.0,
        percent_above_forecast=150.0,
        rolling_baseline_mean=0.0,
        rolling_baseline_stddev=1.0,
        candidate_status="flagged",
        detected_at=now,
        correlation_id="corr",
        failure_reason=None,
    )
    event = SurgeNotificationEvent(
        surge_notification_event_id="event-1",
        surge_evaluation_run_id="run-1",
        surge_candidate_id="candidate-1",
        surge_detection_configuration_id="cfg-1",
        service_category="Roads",
        forecast_product="daily",
        evaluation_window_start=now,
        evaluation_window_end=now + timedelta(hours=1),
        actual_demand_value=5.0,
        forecast_p50_value=2.0,
        residual_value=3.0,
        residual_z_score=4.0,
        percent_above_forecast=150.0,
        overall_delivery_status="delivered",
        created_at=now,
        delivered_at=now,
        follow_up_reason=None,
        correlation_id="corr",
    )
    attempt = SurgeNotificationChannelAttempt(
        surge_notification_event_id="event-1",
        channel_type="email",
        attempt_number=1,
        attempted_at=now,
        status="succeeded",
        failure_reason=None,
        provider_reference="provider-1",
    )
    session.add_all([config, evaluation, candidate, event, attempt])
    session.commit()

    repository = SurgeNotificationEventRepository(session)
    assert len(repository.list_events(overall_delivery_status="delivered")) == 1
    assert repository.get_event_bundle("missing") is None
    bundle = repository.get_event_bundle("event-1")
    assert bundle is not None
    assert bundle.attempts[0].provider_reference == "provider-1"


@pytest.mark.unit
def test_surge_alert_review_service_not_found_paths() -> None:
    service = SurgeAlertReviewService(
        evaluation_repository=SimpleNamespace(get_run_detail=lambda _id: None, list_runs=lambda **kwargs: []),
        event_repository=SimpleNamespace(get_event_bundle=lambda _id: None, list_events=lambda **kwargs: []),
    )

    with pytest.raises(HTTPException) as evaluation_exc:
        service.get_evaluation("missing")
    with pytest.raises(HTTPException) as event_exc:
        service.get_event("missing")

    assert evaluation_exc.value.status_code == 404
    assert event_exc.value.status_code == 404


@pytest.mark.unit
def test_surge_alert_trigger_service_resolution_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = object()

    class ForecastRepoMissing:
        def __init__(self, _session):
            pass

        def get_forecast_version(self, _forecast_version_id):
            return None

    monkeypatch.setattr(trigger_module, "ForecastRepository", ForecastRepoMissing)
    monkeypatch.setattr(trigger_module, "DatasetRepository", lambda _session: None)
    with pytest.raises(ValueError, match="Forecast version not found"):
        trigger_module.run_surge_alert_evaluation_for_forecast(fake_session, forecast_version_id="forecast-1")

    class ForecastRepoNoDataset:
        def __init__(self, _session):
            pass

        def get_forecast_version(self, _forecast_version_id):
            return SimpleNamespace(source_cleaned_dataset_version_id=None)

    monkeypatch.setattr(trigger_module, "ForecastRepository", ForecastRepoNoDataset)
    with pytest.raises(ValueError, match="not linked"):
        trigger_module.run_surge_alert_evaluation_for_forecast(fake_session, forecast_version_id="forecast-1")

    class ForecastRepoResolved:
        def __init__(self, _session):
            pass

        def get_forecast_version(self, _forecast_version_id):
            return SimpleNamespace(source_cleaned_dataset_version_id="dataset-1")

    class DatasetRepoMissing:
        def __init__(self, _session):
            pass

        def get_dataset_version(self, _dataset_version_id):
            return None

    monkeypatch.setattr(trigger_module, "ForecastRepository", ForecastRepoResolved)
    monkeypatch.setattr(trigger_module, "DatasetRepository", DatasetRepoMissing)
    with pytest.raises(ValueError, match="could not be resolved"):
        trigger_module.run_surge_alert_evaluation_for_forecast(fake_session, forecast_version_id="forecast-1")


@pytest.mark.unit
def test_surge_alert_trigger_service_success_path(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = object()
    calls: list[dict[str, object]] = []

    class ForecastRepoResolved:
        def __init__(self, _session):
            pass

        def get_forecast_version(self, _forecast_version_id):
            return SimpleNamespace(source_cleaned_dataset_version_id="dataset-1")

    class DatasetRepoResolved:
        def __init__(self, _session):
            pass

        def get_dataset_version(self, _dataset_version_id):
            return SimpleNamespace(ingestion_run_id="ing-1")

    monkeypatch.setattr(trigger_module, "ForecastRepository", ForecastRepoResolved)
    monkeypatch.setattr(trigger_module, "DatasetRepository", DatasetRepoResolved)
    monkeypatch.setattr(
        trigger_module,
        "run_surge_alert_evaluation",
        lambda session, **kwargs: calls.append({"session": session, **kwargs}) or SimpleNamespace(surge_evaluation_run_id="run-1"),
    )

    run = trigger_module.run_surge_alert_evaluation_for_forecast(fake_session, forecast_version_id="forecast-1")

    assert run.surge_evaluation_run_id == "run-1"
    assert calls == [{
        "session": fake_session,
        "ingestion_run_id": "ing-1",
        "trigger_source": "ingestion_completion",
    }]


@pytest.mark.unit
def test_surge_detection_service_branch_paths() -> None:
    service = SurgeDetectionService(SimpleNamespace(list_current_cleaned_records=lambda *args, **kwargs: []), "edmonton_311")

    with pytest.raises(SurgeDetectionError, match="at least 2"):
        service.compute_metrics(
            service_category="Roads",
            evaluation_window_start=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
            evaluation_window_end=datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
            actual_demand_value=4.0,
            forecast_p50_value=2.0,
            rolling_baseline_window_count=1,
        )

    service._load_previous_counts = lambda **kwargs: [1.0]  # type: ignore[method-assign]
    with pytest.raises(SurgeDetectionError, match="Insufficient historical observations"):
        service.compute_metrics(
            service_category="Roads",
            evaluation_window_start=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
            evaluation_window_end=datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
            actual_demand_value=4.0,
            forecast_p50_value=2.0,
            rolling_baseline_window_count=2,
        )

    service._load_previous_counts = lambda **kwargs: [1.0, 4.0]  # type: ignore[method-assign]
    metrics = service.compute_metrics(
        service_category="Roads",
        evaluation_window_start=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
        evaluation_window_end=datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
        actual_demand_value=5.0,
        forecast_p50_value=2.0,
        rolling_baseline_window_count=2,
    )
    zero_forecast = service.compute_metrics(
        service_category="Roads",
        evaluation_window_start=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
        evaluation_window_end=datetime(2026, 4, 1, 11, tzinfo=timezone.utc),
        actual_demand_value=5.0,
        forecast_p50_value=0.0,
        rolling_baseline_window_count=2,
    )

    assert metrics.residual_z_score > 0
    assert metrics.percent_above_forecast == 150.0
    assert zero_forecast.percent_above_forecast is None


@pytest.mark.unit
def test_surge_detection_service_load_previous_counts_and_parse_paths() -> None:
    evaluation_window_start = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    evaluation_window_end = datetime(2026, 4, 1, 11, tzinfo=timezone.utc)
    records = [
        {"category": "Waste", "requested_at": "2026-04-01T08:30:00Z"},
        {"category": "Roads", "requested_at": ""},
        {"category": "Roads", "requested_at": "not-a-date"},
        {"category": "Roads", "requested_at": "2026-04-01T08:15:00Z"},
    ]
    service = SurgeDetectionService(SimpleNamespace(list_current_cleaned_records=lambda *args, **kwargs: records), "edmonton_311")

    counts = service._load_previous_counts(
        service_category="Roads",
        evaluation_window_start=evaluation_window_start,
        evaluation_window_end=evaluation_window_end,
        rolling_baseline_window_count=2,
    )

    assert counts == [1.0, 0.0]
    assert service._parse_timestamp("") is None
    assert service._parse_timestamp("bad") is None


@pytest.mark.unit
def test_surge_scope_service_error_and_parse_paths() -> None:
    invalid_run_service = SurgeScopeService(
        run_repository=SimpleNamespace(get_run=lambda _run_id: None),
        dataset_repository=SimpleNamespace(list_dataset_records=lambda _dataset_version_id: []),
        forecast_repository=SimpleNamespace(get_current_marker=lambda _product: None),
    )
    with pytest.raises(ValueError, match="successful ingestion run"):
        invalid_run_service.list_scopes(ingestion_run_id="ing-1")

    base_service = SurgeScopeService(
        run_repository=SimpleNamespace(get_run=lambda _run_id: SimpleNamespace(status="success", dataset_version_id="dataset-1")),
        dataset_repository=SimpleNamespace(list_dataset_records=lambda _dataset_version_id: []),
        forecast_repository=SimpleNamespace(get_current_marker=lambda _product: None),
    )
    with pytest.raises(ValueError, match="No active daily forecast"):
        base_service.list_scopes(ingestion_run_id="ing-1")

    missing_version_service = SurgeScopeService(
        run_repository=SimpleNamespace(get_run=lambda _run_id: SimpleNamespace(status="success", dataset_version_id="dataset-1")),
        dataset_repository=SimpleNamespace(list_dataset_records=lambda _dataset_version_id: []),
        forecast_repository=SimpleNamespace(
            get_current_marker=lambda _product: SimpleNamespace(forecast_version_id="forecast-1"),
            get_forecast_version=lambda _forecast_id: None,
        ),
    )
    with pytest.raises(ValueError, match="could not be resolved"):
        missing_version_service.list_scopes(ingestion_run_id="ing-1")

    evaluation_hour = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    service = SurgeScopeService(
        run_repository=SimpleNamespace(get_run=lambda _run_id: SimpleNamespace(status="success", dataset_version_id="dataset-1")),
        dataset_repository=SimpleNamespace(
            list_dataset_records=lambda _dataset_version_id: [
                {"requested_at": "", "category": "Roads"},
                {"requested_at": "bad", "category": "Roads"},
                {"requested_at": "2026-04-01T10:15:00Z", "category": ""},
                {"requested_at": "2026-04-01T10:15:00Z", "category": "Roads"},
            ]
        ),
        forecast_repository=SimpleNamespace(
            get_current_marker=lambda _product: SimpleNamespace(forecast_version_id="forecast-1"),
            get_forecast_version=lambda _forecast_id: SimpleNamespace(forecast_run_id="forecast-run-1", forecast_version_id="forecast-1"),
            list_buckets=lambda _forecast_id: [],
        ),
    )

    scopes = service.list_scopes(ingestion_run_id="ing-1")

    assert len(scopes) == 1
    assert scopes[0].forecast_p50_value is None
    assert scopes[0].evaluation_window_end == evaluation_hour + timedelta(hours=1)
    assert service._parse_timestamp("") is None
    assert service._parse_timestamp("bad") is None
    assert service._coerce_utc(datetime(2026, 4, 1, 10)) == datetime(2026, 4, 1, 10, tzinfo=timezone.utc)

    bad_payload_row = SimpleNamespace(record_payload="{bad", requested_at="2026-04-01T10:00:00Z", category="Roads")
    assert service._normalize_record(bad_payload_row) == {
        "requested_at": "2026-04-01T10:00:00Z",
        "category": "Roads",
    }
    non_string_payload_row = SimpleNamespace(record_payload={"bad": "payload"}, requested_at="2026-04-01T10:00:00Z", category="Roads")
    assert service._normalize_record(non_string_payload_row) == {
        "requested_at": "2026-04-01T10:00:00Z",
        "category": "Roads",
    }
    assert service._normalize_record({"requested_at": "2026-04-01T10:00:00Z", "category": "Roads"})["category"] == "Roads"
