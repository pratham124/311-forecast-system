from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.repositories.dataset_repository import DatasetRepository
from app.services.activation_guard_service import ActivationGuardService


@pytest.mark.unit
def test_activation_guard_rejects_marker_change(seed_current_dataset, session) -> None:
    repository = DatasetRepository(session)
    before = repository.get_current("edmonton_311")
    before_snapshot = SimpleNamespace(dataset_version_id=before.dataset_version_id)
    second = repository.create_dataset_version("edmonton_311", "run-2", None, 5)
    repository.activate_dataset("edmonton_311", second.dataset_version_id, "run-2")
    after = repository.get_current("edmonton_311")

    with pytest.raises(AssertionError):
        ActivationGuardService().assert_marker_unchanged(before_snapshot, after)


@pytest.mark.unit
def test_candidate_datasets_are_never_current(session) -> None:
    candidate = DatasetRepository(session).create_candidate("run-1", 2, "pending")
    assert candidate.is_current is False
