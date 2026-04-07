from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.user_guide import GuideRenderOutcomeRequest, GuideSection, UserGuideView


def test_user_guide_view_requires_available_fields():
    with pytest.raises(ValidationError):
        UserGuideView(
            guideAccessEventId="evt-1",
            status="available",
            entryPoint="app_user_guide_page",
        )


def test_user_guide_view_requires_status_message_for_unavailable():
    with pytest.raises(ValidationError):
        UserGuideView(
            guideAccessEventId="evt-1",
            status="unavailable",
            entryPoint="app_user_guide_page",
        )


def test_render_outcome_requires_failure_message_for_failed_render():
    with pytest.raises(ValidationError):
        GuideRenderOutcomeRequest(renderOutcome="render_failed")


def test_valid_available_view_schema():
    view = UserGuideView(
        guideAccessEventId="evt-1",
        status="available",
        title="Guide",
        publishedAt=datetime(2026, 3, 13, tzinfo=timezone.utc),
        body="Body",
        sections=[GuideSection(sectionId="overview", label="Overview", orderIndex=0)],
        entryPoint="app_user_guide_page",
    )
    assert view.status == "available"
