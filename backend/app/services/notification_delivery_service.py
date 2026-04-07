from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.clients.notification_service import NotificationServiceClient


@dataclass(slots=True)
class DeliverySummary:
    overall_delivery_status: str
    delivered_at: datetime | None
    follow_up_reason: str | None
    attempts: list[dict[str, str | None | int | datetime]]


class NotificationDeliveryService:
    def __init__(self, client: NotificationServiceClient) -> None:
        self.client = client

    def deliver(self, *, channels: list[str], message: str) -> DeliverySummary:
        attempts: list[dict[str, str | None | int | datetime]] = []
        succeeded = 0
        failed = 0
        for index, channel in enumerate(channels, start=1):
            result = self.client.send(channel_type=channel, message=message)
            attempts.append(
                {
                    "channel_type": channel,
                    "attempt_number": index,
                    "attempted_at": datetime.utcnow(),
                    "status": result.status,
                    "failure_reason": result.failure_reason,
                    "provider_reference": result.provider_reference,
                }
            )
            if result.status == "succeeded":
                succeeded += 1
            else:
                failed += 1

        delivered_at = datetime.utcnow() if succeeded > 0 else None
        if succeeded == len(channels) and succeeded > 0:
            status = "delivered"
            follow_up_reason = None
        elif succeeded > 0:
            status = "partial_delivery"
            follow_up_reason = None
        elif failed > 0:
            status = "manual_review_required"
            follow_up_reason = "No channel delivery succeeded"
        else:
            status = "retry_pending"
            follow_up_reason = "No channels configured"
        return DeliverySummary(
            overall_delivery_status=status,
            delivered_at=delivered_at,
            follow_up_reason=follow_up_reason,
            attempts=attempts,
        )
