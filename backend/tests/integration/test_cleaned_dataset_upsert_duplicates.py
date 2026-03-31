from __future__ import annotations

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository

import pytest


@pytest.mark.integration
def test_upsert_current_cleaned_records_duplicate_service_request_ids_same_batch(session) -> None:
    records = [
        {"service_request_id": "dup-sr-1", "requested_at": "2026-01-01T10:00:00.000", "category": "First"},
        {"service_request_id": "dup-sr-1", "requested_at": "2026-01-02T10:00:00.000", "category": "Second"},
    ]
    version = DatasetRepository(session).create_dataset_version(
        source_name="edmonton_311",
        run_id="run-dup-test",
        candidate_id=None,
        record_count=len(records),
        records=records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-dup-test",
    )
    repo = CleanedDatasetRepository(session)
    repo.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id="run-dup-test",
        source_dataset_version_id=version.dataset_version_id,
        approved_dataset_version_id=version.dataset_version_id,
        approved_by_validation_run_id="validation-dup-test",
        cleaned_records=records,
    )
    session.commit()

    assert repo.count_current_cleaned_records("edmonton_311") == 1
    loaded = repo.list_current_cleaned_records("edmonton_311")
    assert len(loaded) == 1
    assert loaded[0]["category"] == "Second"
