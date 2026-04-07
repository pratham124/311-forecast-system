from __future__ import annotations

import logging

from app.core.logging import summarize_user_guide_error, summarize_user_guide_event, summarize_user_guide_success
from app.core.metrics import record_user_guide_support_signal
from app.repositories.user_guide_repository import UserGuideRepository
from app.schemas.user_guide import GuideRenderOutcomeRequest, GuideSection, UserGuideView


def normalize_failure_message(category: str) -> str:
    if category == "guide_render_failed":
        return "The user guide could not be displayed. This was not caused by normal guide navigation."
    return "The user guide is unavailable right now. This was not caused by normal guide navigation."


def normalize_sections(sections: list[GuideSection]) -> list[GuideSection]:
    return sorted(sections, key=lambda section: (section.order_index, section.label.lower(), section.section_id))


class UserGuideService:
    def __init__(
        self,
        *,
        repository: UserGuideRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self.repository = repository
        self.logger = logger or logging.getLogger("user_guide")

    def get_current_user_guide(self, *, user_id: str, entry_point: str, correlation_id: str | None = None) -> UserGuideView:
        access_event = self.repository.create_access_event(user_id=user_id, entry_point=entry_point, correlation_id=correlation_id)
        self.logger.info(
            "%s",
            summarize_user_guide_event(
                "user_guide.request_started",
                guide_access_event_id=access_event.guide_access_event_id,
                entry_point=entry_point,
                user_id=user_id,
            ),
        )
        try:
            guide = self.repository.get_current_guide()
            if guide is None:
                message = normalize_failure_message("guide_unavailable")
                self.repository.finalize_access_event(
                    access_event.guide_access_event_id,
                    outcome="retrieval_failed",
                    failure_category="guide_unavailable",
                    failure_message=message,
                )
                record_user_guide_support_signal("guide_unavailable")
                self.logger.info(
                    "%s",
                    summarize_user_guide_error(
                        "user_guide.unavailable",
                        guide_access_event_id=access_event.guide_access_event_id,
                        entry_point=entry_point,
                    ),
                )
                return UserGuideView(
                    guideAccessEventId=access_event.guide_access_event_id,
                    status="unavailable",
                    statusMessage=message,
                    entryPoint=entry_point,
                )

            sections = normalize_sections(guide.sections)
            self.repository.finalize_access_event(
                access_event.guide_access_event_id,
                outcome="retrieved",
                guide_content_id=guide.guide_content_id,
            )
            self.logger.info(
                "%s",
                summarize_user_guide_success(
                    "user_guide.retrieved",
                    guide_access_event_id=access_event.guide_access_event_id,
                    guide_content_id=guide.guide_content_id,
                    section_count=len(sections),
                ),
            )
            return UserGuideView(
                guideAccessEventId=access_event.guide_access_event_id,
                status="available",
                title=guide.title,
                publishedAt=guide.published_at,
                body=guide.body,
                sections=sections,
                entryPoint=entry_point,
            )
        except Exception as exc:
            message = normalize_failure_message("guide_unavailable")
            self.repository.finalize_access_event(
                access_event.guide_access_event_id,
                outcome="retrieval_failed",
                failure_category="guide_unavailable",
                failure_message=str(exc),
            )
            record_user_guide_support_signal("guide_error")
            self.logger.exception(
                "%s",
                summarize_user_guide_error(
                    "user_guide.request_failed",
                    guide_access_event_id=access_event.guide_access_event_id,
                    failure_reason=str(exc),
                ),
            )
            return UserGuideView(
                guideAccessEventId=access_event.guide_access_event_id,
                status="error",
                statusMessage=message,
                entryPoint=entry_point,
            )

    def record_render_outcome(self, guide_access_event_id: str, payload: GuideRenderOutcomeRequest) -> None:
        access_event = self.repository.require_access_event(guide_access_event_id)
        if access_event.outcome not in {"retrieved", "rendered", "render_failed"} or not access_event.guide_content_id:
            raise ValueError("Guide access event is not eligible for render reporting")
        self.repository.record_render_outcome(guide_access_event_id, payload)
        if payload.render_outcome == "render_failed":
            failure_message = payload.failure_message or normalize_failure_message("guide_render_failed")
            self.repository.finalize_access_event(
                guide_access_event_id,
                outcome="render_failed",
                guide_content_id=access_event.guide_content_id,
                failure_category="guide_render_failed",
                failure_message=failure_message,
            )
            record_user_guide_support_signal("render_failed")
            self.logger.info(
                "%s",
                summarize_user_guide_error(
                    "user_guide.render_failed",
                    guide_access_event_id=guide_access_event_id,
                    failure_reason=failure_message,
                ),
            )
            return

        self.repository.finalize_access_event(
            guide_access_event_id,
            outcome="rendered",
            guide_content_id=access_event.guide_content_id,
        )
        self.logger.info(
            "%s",
            summarize_user_guide_success("user_guide.rendered", guide_access_event_id=guide_access_event_id),
        )
