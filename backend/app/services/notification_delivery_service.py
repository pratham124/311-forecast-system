from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.clients.notification_service import NotificationAttemptResult, NotificationDeliveryClient


@dataclass
class DeliveryOutcome:
    overall_delivery_status: str
    delivered_at: datetime | None
    follow_up_reason: str | None
    attempts: list[NotificationAttemptResult]


class NotificationDeliveryService:
    def __init__(self, client: NotificationDeliveryClient) -> None:
        self.client = client

    def deliver(self, *, channels: list[str], payload: dict[str, object]) -> DeliveryOutcome:
        attempts = [self.client.deliver(channel_type=channel, payload=payload) for channel in channels]
        succeeded = [attempt for attempt in attempts if attempt.status == "succeeded"]
        failed = [attempt for attempt in attempts if attempt.status != "succeeded"]
        delivered_at = datetime.utcnow() if succeeded else None
        if succeeded and not failed:
            return DeliveryOutcome("delivered", delivered_at, None, attempts)
        if succeeded and failed:
            return DeliveryOutcome("partial_delivery", delivered_at, "One or more channels failed", attempts)
        retryable = any((attempt.failure_reason or "").lower().startswith("retry") for attempt in failed)
        if retryable:
            return DeliveryOutcome("retry_pending", None, "Delivery retry remains queued", attempts)
        return DeliveryOutcome("manual_review_required", None, "No configured channel succeeded", attempts)
