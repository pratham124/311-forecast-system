from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from app.core.logging import summarize_status
from app.pipelines.ingestion.run_ingestion import IngestionPipeline
from app.repositories.approval_status_repository import ApprovalStatusRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.review_needed_repository import ReviewNeededRepository
from app.repositories.validation_repository import ValidationRepository
from app.services.approval_status_service import ApprovalStatusService
from app.services.candidate_dataset_service import CandidateDatasetService
from app.services.dataset_validation_service import ValidationResult
from app.services.duplicate_analysis_service import DuplicateAnalysisService
from app.services.ingestion_logging_service import IngestionLoggingService
from app.services.operational_status_service import OperationalStatusService
from app.services.operator_visibility_metrics_service import OperatorVisibilityMetricsService
from app.services.schema_validation_service import SchemaValidationService
from app.services.validation_status_service import ValidationStatusService
from app.clients.edmonton_311 import Edmonton311Client, Edmonton311FetchResult




class NoCursorClient(Edmonton311Client):
    def __init__(self) -> None:
        pass

    def fetch_records(self, cursor: str | None) -> Edmonton311FetchResult:
        return Edmonton311FetchResult(
            result_type="new_data",
            records=[{"service_request_id": "1", "requested_at": "2026-03-02T00:00:00Z", "category": "Roads"}],
            cursor_value=None,
        )


class StubValidationService:
    def __init__(self, passed: bool, reason: str | None) -> None:
        self.result = ValidationResult(passed=passed, reason=reason)

    def validate(self, records):
        return self.result


@pytest.mark.unit
def test_summarize_status_adds_message_and_sanitizes_sensitive_fields() -> None:
    result = summarize_status("validation.completed", token="abcd1234", count=3)

    assert result["message"] == "validation.completed"
    assert result["token"] != "abcd1234"
    assert result["count"] == 3


@pytest.mark.unit
def test_candidate_dataset_service_covers_create_and_validation_paths(session) -> None:
    repository = DatasetRepository(session)
    passed_service = CandidateDatasetService(repository, StubValidationService(True, None))
    failed_service = CandidateDatasetService(repository, StubValidationService(False, "bad data"))

    candidate = passed_service.create_candidate("run-1", [{"service_request_id": "1"}])
    updated_candidate, reason = passed_service.validate_candidate(candidate.candidate_dataset_id, [{"service_request_id": "1"}])
    failed_candidate, failed_reason = failed_service.validate_candidate(candidate.candidate_dataset_id, [{"service_request_id": "1"}])

    assert candidate.validation_status == "failed"
    assert updated_candidate is not None
    assert reason is None
    assert failed_candidate is not None
    assert failed_reason == "bad data"


@pytest.mark.unit
def test_duplicate_analysis_covers_empty_record_path() -> None:
    outcome = DuplicateAnalysisService().analyze([], threshold_percentage=20)

    assert outcome.total_record_count == 0
    assert outcome.duplicate_percentage == 0.0
    assert outcome.status == "passed"


@pytest.mark.unit
def test_schema_validation_covers_blank_type_and_format_failures() -> None:
    service = SchemaValidationService()

    blank = service.validate([
        {"service_request_id": "SR-1", "requested_at": "", "category": "Roads"},
    ])
    wrong_type = service.validate([
        {"service_request_id": "SR-1", "requested_at": 123, "category": "Roads"},
    ])
    bad_format = service.validate([
        {"service_request_id": "SR-1", "requested_at": "not-a-date", "category": "Roads"},
    ])

    assert blank.completeness_check == "failed"
    assert wrong_type.type_check == "failed"
    assert bad_format.format_check == "failed"


@pytest.mark.unit
def test_approval_status_service_raises_for_missing_marker_and_dataset(session) -> None:
    service = ApprovalStatusService(ApprovalStatusRepository(session))

    with pytest.raises(HTTPException) as missing_marker:
        service.get_current_approved_dataset("edmonton_311")
    assert missing_marker.value.status_code == 404

    repository = DatasetRepository(session)
    version = repository.create_dataset_version("edmonton_311", "run-1", None, 1)
    repository.activate_dataset("edmonton_311", version.dataset_version_id, "run-1")
    session.delete(version)
    session.flush()

    with pytest.raises(HTTPException) as missing_dataset:
        service.get_current_approved_dataset("edmonton_311")
    assert missing_dataset.value.status_code == 404


@pytest.mark.unit
def test_approval_status_repository_can_find_validation_run_by_approved_dataset(session) -> None:
    dataset_repository = DatasetRepository(session)
    validation_repository = ValidationRepository(session)
    source_dataset = dataset_repository.create_dataset_version("edmonton_311", "run-1", None, 1)
    approved_dataset = dataset_repository.create_dataset_version(
        "edmonton_311",
        "run-1",
        None,
        1,
        dataset_kind="cleaned",
        source_dataset_version_id=source_dataset.dataset_version_id,
    )
    run = validation_repository.create_run("run-1", source_dataset.dataset_version_id, 20)
    validation_repository.finalize_run(
        run.validation_run_id,
        status="approved",
        approved_dataset_version_id=approved_dataset.dataset_version_id,
    )

    found = ApprovalStatusRepository(session).get_validation_run_by_approved_dataset(approved_dataset.dataset_version_id)

    assert found is not None
    assert found.validation_run_id == run.validation_run_id


@pytest.mark.unit
def test_review_needed_repository_list_filters_by_validation_run_id(session) -> None:
    dataset_repository = DatasetRepository(session)
    validation_repository = ValidationRepository(session)
    review_repository = ReviewNeededRepository(session)

    source_one = dataset_repository.create_dataset_version("edmonton_311", "run-1", None, 1)
    source_two = dataset_repository.create_dataset_version("edmonton_311", "run-2", None, 1)
    run_one = validation_repository.create_run("run-1", source_one.dataset_version_id, 20)
    run_two = validation_repository.create_run("run-2", source_two.dataset_version_id, 20)
    analysis_one = validation_repository.record_duplicate_analysis(
        run_one.validation_run_id,
        status="review_needed",
        total_record_count=3,
        duplicate_record_count=1,
        duplicate_percentage=33.33,
        threshold_percentage=20,
        duplicate_group_count=1,
    )
    analysis_two = validation_repository.record_duplicate_analysis(
        run_two.validation_run_id,
        status="review_needed",
        total_record_count=4,
        duplicate_record_count=2,
        duplicate_percentage=50,
        threshold_percentage=20,
        duplicate_group_count=1,
    )
    review_repository.create(run_one.validation_run_id, analysis_one.duplicate_analysis_id, "first")
    review_repository.create(run_two.validation_run_id, analysis_two.duplicate_analysis_id, "second")

    all_items = review_repository.list()
    filtered = review_repository.list(run_one.validation_run_id)

    assert len(all_items) == 2
    assert len(filtered) == 1
    assert filtered[0][0].validation_run_id == run_one.validation_run_id


@pytest.mark.unit
def test_validation_repository_finalize_run_raises_for_missing_run(session) -> None:
    with pytest.raises(ValueError):
        ValidationRepository(session).finalize_run("missing", status="failed")


@pytest.mark.unit
def test_operational_and_visibility_metric_helpers_cover_remaining_paths() -> None:
    started_at = datetime.utcnow()
    on_time = started_at + timedelta(seconds=120)
    late = started_at + timedelta(seconds=121)

    assert OperationalStatusService().blocked_summary("failed", "storage unavailable") == "failed: storage unavailable"
    assert OperatorVisibilityMetricsService().visible_within_target(started_at, on_time) is True
    assert OperatorVisibilityMetricsService().visible_within_target(started_at, late) is False


@pytest.mark.unit
def test_validation_status_service_reports_running_visibility(session) -> None:
    dataset_repository = DatasetRepository(session)
    validation_repository = ValidationRepository(session)
    source_dataset = dataset_repository.create_dataset_version("edmonton_311", "run-1", None, 1)
    run = validation_repository.create_run("run-1", source_dataset.dataset_version_id, 20)

    status_payload = ValidationStatusService(
        ApprovalStatusRepository(session),
        ReviewNeededRepository(session),
    ).get_validation_run_status(run.validation_run_id)

    assert status_payload.visibility_state == "in_progress"
    assert status_payload.status == "running"


@pytest.mark.unit
def test_run_ingestion_handles_missing_validation_run_record(session, monkeypatch) -> None:
    pipeline = IngestionPipeline(
        session,
        NoCursorClient(),
        IngestionLoggingService(__import__("logging").getLogger("test")),
    )
    monkeypatch.setattr(pipeline.validation_pipeline, "run", lambda *args, **kwargs: "missing-run")
    monkeypatch.setattr(pipeline.validation_pipeline.validation_repository, "get_run", lambda run_id: None)

    result = pipeline.run()

    assert result.status == "success"
    assert result.result_type == "new_data"
    assert result.candidate_dataset_id is not None
