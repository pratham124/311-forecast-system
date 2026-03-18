from __future__ import annotations

import pytest

from app.repositories.cursor_repository import CursorRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.failure_notification_repository import FailureNotificationRepository
from app.repositories.run_repository import RunRepository


@pytest.mark.unit
def test_cursor_repository_updates_existing_record(session) -> None:
    repo = CursorRepository(session)
    original = repo.upsert("edmonton_311", "2026-03-01T00:00:00Z", "run-1")
    updated = repo.upsert("edmonton_311", "2026-03-02T00:00:00Z", "run-2")

    assert original.source_name == updated.source_name
    assert updated.cursor_value == "2026-03-02T00:00:00Z"
    assert updated.updated_by_run_id == "run-2"


@pytest.mark.unit
def test_dataset_repository_returns_none_for_missing_candidate(session) -> None:
    assert DatasetRepository(session).update_candidate_status("missing", "passed") is None


@pytest.mark.unit
def test_dataset_repository_raises_for_missing_dataset_version(session) -> None:
    with pytest.raises(ValueError):
        DatasetRepository(session).activate_dataset("edmonton_311", "missing", "run-1")


@pytest.mark.unit
def test_failure_notification_repository_lists_all_when_no_run_filter(session) -> None:
    repo = FailureNotificationRepository(session)
    repo.create("run-1", "auth_failure", "bad auth")
    repo.create("run-2", "storage_failure", "disk full")

    assert len(repo.list()) == 2


@pytest.mark.unit
def test_run_repository_raises_for_unknown_run(session) -> None:
    with pytest.raises(ValueError):
        RunRepository(session).finalize_run("missing", "failed", "auth_failure")

