from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import Base
from app.models import GuideAccessEvent, GuideRenderOutcomeRecord
from app.schemas.user_guide import GuideRenderOutcomeRequest, GuideSection, GuideSourceDocument


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


DEFAULT_GUIDE_SOURCE = GuideSourceDocument(
    guide_content_id="guide-current",
    title="Operations Analytics User Guide",
    published_at=datetime(2026, 3, 13, 15, 0, tzinfo=timezone.utc),
    body=(
        "Use the navigation on the left to move between forecasting, comparisons, historical analysis, "
        "ingestion monitoring, alerts operations, and troubleshooting. Each section explains the primary "
        "workflow, expected outcomes, and what to do when data is unavailable."
    ),
    sections=[
        GuideSection(
            sectionId="overview",
            label="Overview",
            orderIndex=0,
            anchorTarget="overview",
            contentExcerpt="Start here for the system layout, roles, and where to find the latest forecast surfaces.",
        ),
        GuideSection(
            sectionId="forecasts",
            label="Forecasts",
            orderIndex=1,
            anchorTarget="forecasts",
            contentExcerpt="Open the Forecasts page to review current demand, history, and fallback messaging.",
        ),
        GuideSection(
            sectionId="comparisons",
            label="Comparisons",
            orderIndex=2,
            anchorTarget="comparisons",
            contentExcerpt="Use the Comparisons page to contrast demand outcomes across categories and time windows.",
        ),
        GuideSection(
            sectionId="historical-demand",
            label="Historical Demand",
            orderIndex=3,
            anchorTarget="historical-demand",
            contentExcerpt=(
                "Apply category, and time-range filters to explore historical demand "
                "patterns, and use no-data or high-volume warnings to adjust your request."
            ),
        ),
        GuideSection(
            sectionId="ingestion-monitoring",
            label="Ingestion Monitoring",
            orderIndex=4,
            anchorTarget="ingestion-monitoring",
            contentExcerpt=(
                "Track scheduled 311 ingestion runs, validate run outcomes, and confirm current dataset state "
                "before reviewing downstream analytics."
            ),
        ),
        GuideSection(
            sectionId="alerts-operations",
            label="Alerts and Notifications",
            orderIndex=5,
            anchorTarget="alerts-operations",
            contentExcerpt=(
                "Review threshold and surge alert behavior, duplicate-suppression rules, delivery outcomes, "
                "and drill-down context for follow-up actions."
            ),
        ),
        GuideSection(
            sectionId="troubleshooting",
            label="Troubleshooting",
            orderIndex=6,
            anchorTarget="troubleshooting",
            contentExcerpt="If a view is unavailable, refresh once, confirm your session, and report the issue if it persists.",
        ),
    ],
)


class UserGuideRepository:
    _override_source: GuideSourceDocument | None = DEFAULT_GUIDE_SOURCE
    _override_error: Exception | None = None

    def __init__(self, session: Session) -> None:
        self.session = session
        bind = self.session.get_bind()
        if bind is not None:
            Base.metadata.create_all(bind=bind, tables=[GuideAccessEvent.__table__, GuideRenderOutcomeRecord.__table__])

    @classmethod
    def reset_for_tests(cls) -> None:
        cls._override_source = DEFAULT_GUIDE_SOURCE
        cls._override_error = None

    @classmethod
    def set_source_for_tests(cls, source: GuideSourceDocument | None) -> None:
        cls._override_source = source
        cls._override_error = None

    @classmethod
    def set_error_for_tests(cls, error: Exception | None) -> None:
        cls._override_error = error

    def get_current_guide(self) -> GuideSourceDocument | None:
        if self._override_error is not None:
            raise self._override_error
        return self._override_source

    def create_access_event(self, *, user_id: str, entry_point: str, correlation_id: str | None = None) -> GuideAccessEvent:
        record = GuideAccessEvent(user_id=user_id, entry_point=entry_point, correlation_id=correlation_id)
        self.session.add(record)
        self.session.flush()
        return record

    def finalize_access_event(
        self,
        guide_access_event_id: str,
        *,
        outcome: str,
        guide_content_id: str | None = None,
        failure_category: str | None = None,
        failure_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> GuideAccessEvent:
        record = self.require_access_event(guide_access_event_id)
        record.guide_content_id = guide_content_id
        record.outcome = outcome
        record.failure_category = failure_category
        record.failure_message = failure_message
        record.completed_at = completed_at or _utc_now()
        self.session.flush()
        return record

    def record_render_outcome(
        self,
        guide_access_event_id: str,
        payload: GuideRenderOutcomeRequest,
    ) -> GuideRenderOutcomeRecord:
        record = self.session.scalar(
            select(GuideRenderOutcomeRecord).where(GuideRenderOutcomeRecord.guide_access_event_id == guide_access_event_id)
        )
        if record is None:
            record = GuideRenderOutcomeRecord(
                guide_access_event_id=guide_access_event_id,
                render_outcome=payload.render_outcome,
                failure_message=payload.failure_message,
                reported_at=_utc_now(),
            )
            self.session.add(record)
        else:
            record.render_outcome = payload.render_outcome
            record.failure_message = payload.failure_message
            record.reported_at = _utc_now()
        self.session.flush()
        return record

    def require_access_event(self, guide_access_event_id: str) -> GuideAccessEvent:
        record = self.session.get(GuideAccessEvent, guide_access_event_id)
        if record is None:
            raise LookupError("Guide access event not found")
        return record
