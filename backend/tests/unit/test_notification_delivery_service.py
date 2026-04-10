from __future__ import annotations

from app.clients.notification_service import NotificationAttemptResult
from app.services.notification_delivery_service import NotificationDeliveryService


class FakeClient:
    def __init__(self, attempts: list[NotificationAttemptResult]) -> None:
        self.attempts = list(attempts)

    def deliver(self, *, channel_type: str, payload: dict[str, object]) -> NotificationAttemptResult:
        return self.attempts.pop(0)


def test_notification_delivery_service_aggregates_all_outcomes() -> None:
    delivered = NotificationDeliveryService(
        FakeClient([NotificationAttemptResult(channel_type="email", status="succeeded")]),
    ).deliver(channels=["email"], payload={})
    partial = NotificationDeliveryService(
        FakeClient(
            [
                NotificationAttemptResult(channel_type="email", status="succeeded"),
                NotificationAttemptResult(channel_type="sms", status="failed", failure_reason="gateway timeout"),
            ]
        ),
    ).deliver(channels=["email", "sms"], payload={})
    retry_pending = NotificationDeliveryService(
        FakeClient([NotificationAttemptResult(channel_type="sms", status="failed", failure_reason="retry later")]),
    ).deliver(channels=["sms"], payload={})
    manual_review = NotificationDeliveryService(
        FakeClient([NotificationAttemptResult(channel_type="sms", status="failed", failure_reason="provider unavailable")]),
    ).deliver(channels=["sms"], payload={})

    assert delivered.overall_delivery_status == "delivered"
    assert partial.overall_delivery_status == "partial_delivery"
    assert retry_pending.overall_delivery_status == "retry_pending"
    assert manual_review.overall_delivery_status == "manual_review_required"
