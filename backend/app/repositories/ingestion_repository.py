from __future__ import annotations

from typing import Protocol

from app.models import (
    CandidateDataset,
    CurrentDatasetMarker,
    DatasetRecord,
    DatasetVersion,
    FailureNotificationRecord,
    IngestionRun,
    SuccessfulPullCursor,
)


class CursorRepositoryProtocol(Protocol):
    def get(self, source_name: str) -> SuccessfulPullCursor | None: ...
    def upsert(self, source_name: str, cursor_value: str, run_id: str) -> SuccessfulPullCursor: ...


class DatasetRepositoryProtocol(Protocol):
    def create_candidate(self, run_id: str, record_count: int, validation_status: str) -> CandidateDataset: ...
    def update_candidate_status(self, candidate_id: str, validation_status: str) -> CandidateDataset | None: ...
    def create_dataset_version(
        self,
        source_name: str,
        run_id: str,
        candidate_id: str | None,
        record_count: int,
        records: list[dict[str, object]] | None = None,
    ) -> DatasetVersion: ...
    def activate_dataset(self, source_name: str, dataset_version_id: str, run_id: str) -> CurrentDatasetMarker: ...
    def get_current(self, source_name: str) -> CurrentDatasetMarker | None: ...
    def list_dataset_records(self, dataset_version_id: str) -> list[DatasetRecord]: ...


class RunRepositoryProtocol(Protocol):
    def create_run(self, trigger_type: str, cursor_used: str | None) -> IngestionRun: ...
    def finalize_run(
        self,
        run_id: str,
        status: str,
        result_type: str,
        records_received: int | None = None,
        candidate_dataset_id: str | None = None,
        dataset_version_id: str | None = None,
        cursor_advanced: bool = False,
        failure_reason: str | None = None,
    ) -> IngestionRun: ...
    def get_run(self, run_id: str) -> IngestionRun | None: ...


class FailureNotificationRepositoryProtocol(Protocol):
    def create(self, run_id: str, failure_category: str, message: str) -> FailureNotificationRecord: ...
    def list(self, run_id: str | None = None) -> list[FailureNotificationRecord]: ...
