from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import ValidationRun
from app.pipelines.ingestion.validation_pipeline import ValidationPipeline
from app.repositories.dataset_repository import DatasetRepository


@pytest.mark.integration
def test_validation_pipeline_marks_run_failed_when_cleaned_dataset_approval_raises(session, monkeypatch) -> None:
    source_dataset = DatasetRepository(session).create_dataset_version(
        source_name="edmonton_311",
        run_id="run-1",
        candidate_id=None,
        record_count=1,
        records=[{"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads"}],
        validation_status="pending",
        dataset_kind="source",
    )
    pipeline = ValidationPipeline(session)

    def boom(**kwargs):
        raise RuntimeError("forced storage failure")

    monkeypatch.setattr(pipeline.approved_pipeline, "approve", boom)

    validation_run_id = pipeline.run(
        ingestion_run_id="run-1",
        source_dataset_version_id=source_dataset.dataset_version_id,
        records=[{"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads"}],
    )

    run = session.scalars(select(ValidationRun).where(ValidationRun.validation_run_id == validation_run_id)).one()

    assert run.status == "failed"
    assert run.failure_stage == "storage"
    assert run.summary == "forced storage failure"
