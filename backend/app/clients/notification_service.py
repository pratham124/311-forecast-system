from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NotificationAttemptResult:
    channel_type: str
    status: str
    failure_reason: str | None = None
    provider_reference: str | None = None


class NotificationDeliveryClient:
    def deliver(self, *, channel_type: str, payload: dict[str, object]) -> NotificationAttemptResult:
        return NotificationAttemptResult(
            channel_type=channel_type,
            status="succeeded",
            provider_reference=f"{channel_type}-accepted",
        )
