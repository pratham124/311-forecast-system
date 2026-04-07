from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.schemas.user_guide import GuideRenderOutcomeRequest, GuideSection
from app.services.user_guide_service import UserGuideService, normalize_failure_message, normalize_sections


def test_normalize_failure_message_uses_user_safe_copy():
    assert "not caused by normal guide navigation" in normalize_failure_message("guide_unavailable")
    assert "could not be displayed" in normalize_failure_message("guide_render_failed")


def test_normalize_sections_orders_by_index_then_label():
    sections = [
        GuideSection(sectionId="b", label="Beta", orderIndex=2),
        GuideSection(sectionId="a", label="Alpha", orderIndex=1),
        GuideSection(sectionId="a2", label="Another", orderIndex=1),
    ]
    ordered = normalize_sections(sections)
    assert [section.section_id for section in ordered] == ["a", "a2", "b"]


def test_get_current_user_guide_handles_unexpected_retrieval_error():
    repo = MagicMock()
    access = MagicMock()
    access.guide_access_event_id = "evt-1"
    repo.create_access_event.return_value = access
    repo.get_current_guide.side_effect = RuntimeError("storage error")

    service = UserGuideService(repository=repo, logger=MagicMock())
    result = service.get_current_user_guide(user_id="u1", entry_point="app")

    assert result.status == "error"
    assert result.status_message is not None
    repo.finalize_access_event.assert_called_once()
    call_kwargs = repo.finalize_access_event.call_args.kwargs
    assert call_kwargs["outcome"] == "retrieval_failed"
    assert call_kwargs["failure_category"] == "guide_unavailable"


def test_record_render_outcome_rejects_ineligible_access_event():
    repo = MagicMock()
    access = MagicMock()
    access.outcome = "retrieval_failed"
    access.guide_content_id = "guide-1"
    repo.require_access_event.return_value = access

    service = UserGuideService(repository=repo, logger=MagicMock())
    with pytest.raises(ValueError, match="not eligible"):
        service.record_render_outcome(
            "evt-1",
            GuideRenderOutcomeRequest(renderOutcome="rendered"),
        )


def test_record_render_outcome_rejects_when_guide_content_id_missing():
    repo = MagicMock()
    access = MagicMock()
    access.outcome = "retrieved"
    access.guide_content_id = None
    repo.require_access_event.return_value = access

    service = UserGuideService(repository=repo, logger=MagicMock())
    with pytest.raises(ValueError, match="not eligible"):
        service.record_render_outcome(
            "evt-1",
            GuideRenderOutcomeRequest(renderOutcome="rendered"),
        )
