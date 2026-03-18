from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FailureNotification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: str
    run_id: str
    failure_category: str
    run_status: str
    recorded_at: datetime
    message: str


class FailureNotificationList(BaseModel):
    items: list[FailureNotification]
