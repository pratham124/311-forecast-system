from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.repositories.user_guide_repository import UserGuideRepository


@patch("app.repositories.user_guide_repository.Base.metadata.create_all")
def test_user_guide_repository_skips_create_all_when_session_has_no_bind(mock_create_all: MagicMock) -> None:
    session = MagicMock()
    session.get_bind.return_value = None
    UserGuideRepository(session)
    mock_create_all.assert_not_called()


def test_get_current_guide_raises_configured_test_error() -> None:
    UserGuideRepository.set_error_for_tests(RuntimeError("forced retrieval failure"))
    try:
        repo = UserGuideRepository(MagicMock())
        with pytest.raises(RuntimeError, match="forced retrieval failure"):
            repo.get_current_guide()
    finally:
        UserGuideRepository.reset_for_tests()
