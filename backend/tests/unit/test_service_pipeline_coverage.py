from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.pipelines.ingestion.approved_pipeline import ApprovedPipeline
from app.pipelines.ingestion.blocked_outcome_pipeline import BlockedOutcomePipeline
from app.pipelines.ingestion.rejection_pipeline import RejectionPipeline
from app.services.activation_guard_service import ActivationGuardService
from app.services.approval_status_service import ApprovalStatusService
from app.services.candidate_dataset_service import CandidateDatasetService
from app.services.cleaned_dataset_service import CleanedDatasetService
from app.services.dataset_validation_service import DatasetValidationService
from app.services.duplicate_analysis_service import DuplicateAnalysisService, DuplicateGroupCandidate
from app.services.duplicate_resolution_service import DuplicateResolutionService
from app.services.failure_notification_service import FailureNotificationService
from app.services.ingestion_logging_service import IngestionLoggingService
from app.services.ingestion_query_service import IngestionQueryService
from app.services.operational_status_service import OperationalStatusService
from app.services.operator_visibility_metrics_service import OperatorVisibilityMetricsService
from app.services.validation_metrics_service import ValidationMetricsService
from app.services.validation_status_service import ValidationStatusService


class RepoStub:
    def __init__(self, **values):
        self.__dict__.update(values)
        self.calls = []

    def __getattr__(self, name):
        value = self.__dict__.get(name)
        if callable(value):
            return value
        raise AttributeError(name)


def test_activation_guard_service_covers_both_assertions():
    service = ActivationGuardService()

    service.assert_not_current(None, None)
    service.assert_marker_unchanged(None, None)

    with pytest.raises(AssertionError):
        service.assert_not_current(SimpleNamespace(is_current=True), None)

    with pytest.raises(AssertionError):
        service.assert_not_current(None, SimpleNamespace(is_current=True))

    service.assert_marker_unchanged(
        SimpleNamespace(dataset_version_id="same"),
        SimpleNamespace(dataset_version_id="same"),
    )

    with pytest.raises(AssertionError):
        service.assert_marker_unchanged(
            SimpleNamespace(dataset_version_id="before"),
            SimpleNamespace(dataset_version_id="after"),
        )


def test_approval_status_service_covers_missing_and_success_paths():
    now = datetime.now(timezone.utc)
    marker = SimpleNamespace(dataset_version_id="dataset-1", updated_at=now)
    dataset = SimpleNamespace(
        dataset_version_id="dataset-1",
        source_dataset_version_id="source-1",
        activated_at=None,
        approved_by_validation_run_id="validation-1",
        record_count=5,
        duplicate_group_count=None,
    )

    repo = RepoStub(
        get_current_marker=lambda source_name: marker,
        get_dataset_version=lambda dataset_version_id: dataset,
    )
    result = ApprovalStatusService(repo).get_current_approved_dataset("edmonton")
    assert result.dataset_version_id == "dataset-1"
    assert result.approved_at == now
    assert result.duplicate_group_count == 0

    missing_marker_repo = RepoStub(
        get_current_marker=lambda source_name: None,
        get_dataset_version=lambda dataset_version_id: dataset,
    )
    with pytest.raises(HTTPException):
        ApprovalStatusService(missing_marker_repo).get_current_approved_dataset("edmonton")

    missing_dataset_repo = RepoStub(
        get_current_marker=lambda source_name: marker,
        get_dataset_version=lambda dataset_version_id: None,
    )
    with pytest.raises(HTTPException):
        ApprovalStatusService(missing_dataset_repo).get_current_approved_dataset("edmonton")


def test_candidate_dataset_service_create_and_validate_paths():
    created = SimpleNamespace(candidate_dataset_id="candidate-1")
    updated = SimpleNamespace(candidate_dataset_id="candidate-1", validation_status="passed")

    class DatasetRepo:
        def create_candidate(self, **kwargs):
            self.create_kwargs = kwargs
            return created

        def update_candidate_status(self, candidate_id, status):
            self.update_call = (candidate_id, status)
            return updated

    class ValidationService:
        def __init__(self, passed, reason):
            self.passed = passed
            self.reason = reason

        def validate(self, records):
            return SimpleNamespace(passed=self.passed, reason=self.reason)

    dataset_repo = DatasetRepo()
    service = CandidateDatasetService(dataset_repo, ValidationService(True, None))
    assert service.create_candidate("run-1", [{"a": 1}, {"a": 2}]) is created
    assert dataset_repo.create_kwargs == {
        "run_id": "run-1",
        "record_count": 2,
        "validation_status": "pending",
    }

    candidate, reason = service.validate_candidate("candidate-1", [{"a": 1}])
    assert candidate is updated
    assert reason is None
    assert dataset_repo.update_call == ("candidate-1", "passed")

    service = CandidateDatasetService(dataset_repo, ValidationService(False, "bad schema"))
    candidate, reason = service.validate_candidate("candidate-1", [{"a": 1}])
    assert candidate is updated
    assert reason == "bad schema"
    assert dataset_repo.update_call == ("candidate-1", "failed")


def test_cleaned_dataset_service_stores_and_activates_dataset():
    dataset_version = SimpleNamespace(dataset_version_id="dataset-1")

    class DatasetRepo:
        def create_dataset_version(self, **kwargs):
            self.create_kwargs = kwargs
            return dataset_version

        def activate_dataset(self, source_name, dataset_version_id, ingestion_run_id):
            self.activate_call = (source_name, dataset_version_id, ingestion_run_id)

    class CleanedRepo:
        def upsert_current_cleaned_records(self, **kwargs):
            self.upsert_kwargs = kwargs

        def count_current_cleaned_records(self, source_name):
            self.count_source_name = source_name
            return 7

    cleaned_repo = CleanedRepo()
    service = CleanedDatasetService(DatasetRepo(), validation_repository=object(), cleaned_dataset_repository=cleaned_repo)
    result = service.store_and_approve_cleaned_dataset(
        source_name="edmonton",
        ingestion_run_id="run-1",
        source_dataset_version_id="source-1",
        validation_run_id="validation-1",
        cleaned_records=[{"a": 1}, {"a": 2}],
        duplicate_group_count=3,
    )
    assert result is dataset_version
    assert service.dataset_repository.create_kwargs["record_count"] == 0
    assert service.dataset_repository.create_kwargs["records"] is None
    assert service.dataset_repository.create_kwargs["validation_status"] == "approved"
    assert service.dataset_repository.activate_call == ("edmonton", "dataset-1", "run-1")
    assert cleaned_repo.upsert_kwargs["approved_dataset_version_id"] == "dataset-1"
    assert cleaned_repo.count_source_name == "edmonton"
    assert dataset_version.record_count == 7


def test_dataset_validation_service_maps_schema_result(monkeypatch):
    service = DatasetValidationService()
    monkeypatch.setattr(
        service.schema_validation_service,
        "validate",
        lambda records: SimpleNamespace(passed=False, issue_summary="missing field"),
    )
    result = service.validate([{"a": 1}])
    assert result.passed is False
    assert result.reason == "missing field"


def test_duplicate_analysis_and_resolution_cover_threshold_and_merge():
    analysis_service = DuplicateAnalysisService()
    passed = analysis_service.analyze(
        [{"service_request_id": "1"}, {"service_request_id": "2"}],
        threshold_percentage=10.0,
    )
    assert passed.status == "passed"
    assert passed.issue_summary is None

    duplicate_records = [
        {"service_request_id": "1", "status": "open", "note": ""},
        {"service_request_id": "1", "status": "", "note": "first"},
        {"service_request_id": "2", "status": "closed", "note": "keep"},
    ]
    review = analysis_service.analyze(duplicate_records, threshold_percentage=10.0)
    assert review.status == "review_needed"
    assert review.duplicate_group_count == 1
    assert review.duplicate_record_count == 1

    resolution_service = DuplicateResolutionService()
    cleaned, resolutions = resolution_service.resolve(duplicate_records, review.groups)
    assert len(cleaned) == 2
    assert resolutions[0].resolution_status == "consolidated"
    assert resolutions[0].cleaned_record["status"] == "open"
    assert resolutions[0].cleaned_record["note"] == "first"


def test_logging_and_failure_notification_services():
    messages = []

    class Logger:
        def info(self, message, *args):
            messages.append((message, args))

    payload = IngestionLoggingService(Logger()).log("started", token="secret", source="edmonton")
    assert payload["token"] == "se***et"
    assert payload["source"] == "edmonton"
    assert messages[0][0] == "%s %s"

    class FailureRepo:
        def create(self, **kwargs):
            self.create_kwargs = kwargs
            return SimpleNamespace(**kwargs)

        def list(self, run_id=None):
            return [SimpleNamespace(run_id=run_id)]

    repo = FailureRepo()
    service = FailureNotificationService(repo)
    created = service.create_notification("run-1", "network", "token leaked")
    assert created.message == "token leaked"
    assert service.list_notifications("run-1")[0].run_id == "run-1"


def test_ingestion_query_service_covers_success_and_404_paths():
    now = datetime.now(timezone.utc)
    run = SimpleNamespace(
        run_id="run-1",
        status="completed",
        result_type="success",
        started_at=now,
        completed_at=now,
        cursor_used="cursor-1",
        cursor_advanced=True,
        candidate_dataset_id="candidate-1",
        dataset_version_id="dataset-1",
        records_received=7,
        failure_reason=None,
    )
    marker = SimpleNamespace(
        source_name="edmonton",
        dataset_version_id="dataset-1",
        updated_at=now,
        updated_by_run_id="run-1",
        record_count=7,
    )
    notification = {
        "notification_id": "note-1",
        "run_id": "run-1",
        "failure_category": "network",
        "run_status": "failed",
        "recorded_at": now,
        "message": "message",
    }

    service = IngestionQueryService(
        run_repository=RepoStub(get_run=lambda run_id: run),
        dataset_repository=RepoStub(get_current=lambda source_name: marker),
        failure_repository=RepoStub(list=lambda run_id=None: [notification]),
    )
    assert service.get_run_status("run-1").run_id == "run-1"
    assert service.get_current_dataset("edmonton").dataset_version_id == "dataset-1"
    assert service.list_failure_notifications("run-1").items[0].run_id == "run-1"

    missing_run = IngestionQueryService(
        run_repository=RepoStub(get_run=lambda run_id: None),
        dataset_repository=RepoStub(get_current=lambda source_name: marker),
        failure_repository=RepoStub(list=lambda run_id=None: []),
    )
    with pytest.raises(HTTPException):
        missing_run.get_run_status("missing")

    missing_dataset = IngestionQueryService(
        run_repository=RepoStub(get_run=lambda run_id: run),
        dataset_repository=RepoStub(get_current=lambda source_name: None),
        failure_repository=RepoStub(list=lambda run_id=None: []),
    )
    with pytest.raises(HTTPException):
        missing_dataset.get_current_dataset("edmonton")


def test_small_metric_services_cover_true_and_false_paths():
    now = datetime.now(timezone.utc)
    assert OperationalStatusService().blocked_summary("review_needed", "duplicates") == "review_needed: duplicates"
    assert OperatorVisibilityMetricsService().visible_within_target(now, now + timedelta(seconds=10)) is True
    assert OperatorVisibilityMetricsService().visible_within_target(now, now + timedelta(minutes=3)) is False
    assert ValidationMetricsService().completed_within_target(now, now + timedelta(minutes=5)) is True
    assert ValidationMetricsService().completed_within_target(now, now + timedelta(minutes=20)) is False


def test_validation_status_service_covers_state_mapping_and_review_list():
    now = datetime.now(timezone.utc)
    approved_run = SimpleNamespace(
        validation_run_id="validation-1",
        ingestion_run_id="run-1",
        source_dataset_version_id="source-1",
        approved_dataset_version_id="approved-1",
        status="approved",
        failure_stage=None,
        duplicate_percentage=12.5,
        started_at=now,
        completed_at=now,
        review_reason=None,
        summary="ok",
    )
    review_record = SimpleNamespace(
        review_record_id="review-1",
        validation_run_id="validation-1",
        recorded_at=now,
        reason="Too many duplicates",
    )
    analysis = SimpleNamespace(duplicate_percentage=12.5, threshold_percentage=10.0)

    service = ValidationStatusService(
        approval_repository=RepoStub(get_validation_run=lambda validation_run_id: approved_run),
        review_needed_repository=RepoStub(list=lambda validation_run_id=None: [(review_record, analysis)]),
    )
    assert service.get_validation_run_status("validation-1").visibility_state == "approved_active"
    assert service.list_review_needed(None).items[0].reason == "Too many duplicates"

    blocked_service = ValidationStatusService(
        approval_repository=RepoStub(
            get_validation_run=lambda validation_run_id: SimpleNamespace(**{**approved_run.__dict__, "status": "failed"})
        ),
        review_needed_repository=RepoStub(list=lambda validation_run_id=None: []),
    )
    assert blocked_service.get_validation_run_status("validation-1").visibility_state == "blocked"

    running_service = ValidationStatusService(
        approval_repository=RepoStub(
            get_validation_run=lambda validation_run_id: SimpleNamespace(**{**approved_run.__dict__, "status": "running"})
        ),
        review_needed_repository=RepoStub(list=lambda validation_run_id=None: []),
    )
    assert running_service.get_validation_run_status("validation-1").visibility_state == "in_progress"

    missing_service = ValidationStatusService(
        approval_repository=RepoStub(get_validation_run=lambda validation_run_id: None),
        review_needed_repository=RepoStub(list=lambda validation_run_id=None: []),
    )
    with pytest.raises(HTTPException):
        missing_service.get_validation_run_status("missing")


def test_uc02_pipelines_call_repositories_with_expected_payloads():
    cleaned_dataset_service = RepoStub(
        store_and_approve_cleaned_dataset=lambda **kwargs: SimpleNamespace(dataset_version_id="approved-1", kwargs=kwargs)
    )
    validation_calls = []
    validation_repository = RepoStub(finalize_run=lambda *args, **kwargs: validation_calls.append((args, kwargs)))
    training_events = []

    training_service = RepoStub(
        start_run=lambda **kwargs: training_events.append(("start", kwargs)) or SimpleNamespace(forecast_model_run_id="model-run-1"),
        execute_run=lambda run_id: training_events.append(("execute", run_id)),
    )

    pipeline = ApprovedPipeline(cleaned_dataset_service, validation_repository, training_service)
    approved_id = pipeline.approve(
        source_name="edmonton",
        ingestion_run_id="run-1",
        source_dataset_version_id="source-1",
        validation_run_id="validation-1",
        cleaned_records=[{"id": 1}],
        duplicate_group_count=2,
    )
    assert approved_id == "approved-1"
    assert validation_calls[0][1]["status"] == "approved"
    assert training_events == [
        ("start", {"trigger_type": "approval"}),
        ("execute", "model-run-1"),
    ]

    pipeline_without_training = ApprovedPipeline(cleaned_dataset_service, validation_repository, None)
    assert pipeline_without_training.approve(
        source_name="edmonton",
        ingestion_run_id="run-1",
        source_dataset_version_id="source-1",
        validation_run_id="validation-3",
        cleaned_records=[{"id": 3}],
        duplicate_group_count=1,
    ) == "approved-1"

    failing_training_events = []
    failing_training_service = RepoStub(
        start_run=lambda **kwargs: failing_training_events.append(("start", kwargs)) or (_ for _ in ()).throw(RuntimeError("boom")),
    )
    pipeline_with_failed_training = ApprovedPipeline(cleaned_dataset_service, validation_repository, failing_training_service)
    assert pipeline_with_failed_training.approve(
        source_name="edmonton",
        ingestion_run_id="run-1",
        source_dataset_version_id="source-1",
        validation_run_id="validation-2",
        cleaned_records=[{"id": 2}],
        duplicate_group_count=0,
    ) == "approved-1"
    assert failing_training_events == [("start", {"trigger_type": "approval"})]

    review_calls = []
    review_repo = RepoStub(create=lambda *args: review_calls.append(args))
    blocked_calls = []
    blocked_validation_repo = RepoStub(finalize_run=lambda *args, **kwargs: blocked_calls.append((args, kwargs)))
    blocked = BlockedOutcomePipeline(blocked_validation_repo, review_repo)
    blocked.hold_for_review("validation-1", "duplicate-1", 12.5, "review this")
    blocked.fail("validation-1", "duplicate_analysis", "broken")
    assert review_calls == [("validation-1", "duplicate-1", "review this")]
    assert blocked_calls[0][1]["status"] == "review_needed"
    assert blocked_calls[1][1]["status"] == "failed"

    rejection_calls = []
    rejection = RejectionPipeline(RepoStub(finalize_run=lambda *args, **kwargs: rejection_calls.append((args, kwargs))))
    rejection.reject("validation-2", "bad schema")
    assert rejection_calls[0][1]["status"] == "rejected"
    assert rejection_calls[0][1]["failure_stage"] == "schema_validation"
