from __future__ import annotations

from app.core.logging import sanitize_mapping
from app.repositories.failure_notification_repository import FailureNotificationRepository
from app.models import FailureNotificationRecord


class FailureNotificationService:
    def __init__(self, repository: FailureNotificationRepository) -> None:
        self.repository = repository

    def create_notification(self, run_id: str, failure_category: str, summary: str) -> FailureNotificationRecord:
        sanitized = sanitize_mapping({"message": summary})
        return self.repository.create(
            run_id=run_id,
            failure_category=failure_category,
            message=sanitized["message"],
        )

    def list_notifications(self, run_id: str | None = None) -> list[FailureNotificationRecord]:
        return self.repository.list(run_id=run_id)
