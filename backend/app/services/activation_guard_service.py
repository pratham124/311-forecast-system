from __future__ import annotations

from app.repositories.models import CandidateDataset, CurrentDatasetMarker, DatasetVersion


class ActivationGuardService:
    def assert_not_current(self, candidate: CandidateDataset | None, dataset_version: DatasetVersion | None) -> None:
        if candidate is not None and candidate.is_current:
            raise AssertionError("Candidate datasets must never be current")
        if dataset_version is not None and dataset_version.is_current:
            raise AssertionError("Failed runs must not activate a dataset version")

    def assert_marker_unchanged(
        self,
        before: CurrentDatasetMarker | None,
        after: CurrentDatasetMarker | None,
    ) -> None:
        before_id = before.dataset_version_id if before is not None else None
        after_id = after.dataset_version_id if after is not None else None
        if before_id != after_id:
            raise AssertionError("Current dataset marker changed unexpectedly")
