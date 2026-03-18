from __future__ import annotations

import pytest

from app.services.failure_notification_service import FailureNotificationService
from app.repositories.failure_notification_repository import FailureNotificationRepository


@pytest.mark.unit
def test_failure_notification_created_with_required_fields(session) -> None:
    service = FailureNotificationService(FailureNotificationRepository(session))
    notification = service.create_notification("run-1", "auth_failure", "invalid credentials")

    assert notification.run_id == "run-1"
    assert notification.failure_category == "auth_failure"
    assert notification.run_status == "failed"
    assert notification.message == "invalid credentials"


@pytest.mark.unit
def test_failure_notification_list_filters_by_run(session) -> None:
    service = FailureNotificationService(FailureNotificationRepository(session))
    service.create_notification("run-1", "auth_failure", "invalid credentials")
    service.create_notification("run-2", "storage_failure", "disk full")

    items = service.list_notifications(run_id="run-2")
    assert len(items) == 1
    assert items[0].run_id == "run-2"
