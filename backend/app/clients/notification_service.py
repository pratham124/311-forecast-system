from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NotificationAttemptResult:
    channel_type: str
    status: str
    failure_reason: str | None = None
    provider_reference: str | None = None


class NotificationServiceClient:
    """Simple abstraction for UC-10 alert delivery.

    The current implementation marks dashboard channel as always successful and
    simulates transient failure on unknown channels.
    """

    def send(self, *, channel_type: str, message: str) -> NotificationAttemptResult:
        if channel_type in {"dashboard", "email", "sms"}:
            return NotificationAttemptResult(channel_type=channel_type, status="succeeded", provider_reference="local")
        return NotificationAttemptResult(
            channel_type=channel_type,
            status="failed",
            failure_reason=f"Unsupported channel '{channel_type}'",
        )
