from __future__ import annotations

import pytest

from app.repositories.ingestion_repository import (
    CursorRepositoryProtocol,
    DatasetRepositoryProtocol,
    FailureNotificationRepositoryProtocol,
    RunRepositoryProtocol,
)


@pytest.mark.unit
def test_ingestion_repository_protocols_are_importable() -> None:
    assert CursorRepositoryProtocol.__name__ == "CursorRepositoryProtocol"
    assert DatasetRepositoryProtocol.__name__ == "DatasetRepositoryProtocol"
    assert RunRepositoryProtocol.__name__ == "RunRepositoryProtocol"
    assert FailureNotificationRepositoryProtocol.__name__ == "FailureNotificationRepositoryProtocol"


@pytest.mark.unit
def test_ingestion_repository_protocol_annotations_expose_expected_methods() -> None:
    assert "get" in CursorRepositoryProtocol.__dict__
    assert "create_dataset_version" in DatasetRepositoryProtocol.__dict__
    assert "finalize_run" in RunRepositoryProtocol.__dict__
    assert "list" in FailureNotificationRepositoryProtocol.__dict__
