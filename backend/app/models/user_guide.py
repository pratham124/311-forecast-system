from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class GuideAccessEvent(Base):
    __tablename__ = "guide_access_events"

    guide_access_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    guide_content_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    entry_point: Mapped[str] = mapped_column(String(128), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, default="retrieval_failed")
    failure_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)


class GuideRenderOutcomeRecord(Base):
    __tablename__ = "guide_render_outcome_records"

    guide_render_outcome_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    guide_access_event_id: Mapped[str] = mapped_column(
        ForeignKey("guide_access_events.guide_access_event_id"),
        nullable=False,
        unique=True,
    )
    render_outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
