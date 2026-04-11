from __future__ import annotations

from app.services.notification_delivery_service import DeliveryOutcome, NotificationDeliveryService


class SurgeNotificationDeliveryService:
    def __init__(self, delivery_service: NotificationDeliveryService) -> None:
        self.delivery_service = delivery_service

    def deliver(self, *, channels: list[str], payload: dict[str, object]) -> DeliveryOutcome:
        return self.delivery_service.deliver(channels=channels, payload=payload)
