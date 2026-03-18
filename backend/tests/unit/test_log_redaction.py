from __future__ import annotations

import pytest

from app.core.logging import redact_value, sanitize_mapping


@pytest.mark.unit
def test_secret_values_are_masked() -> None:
    assert redact_value("super-secret-token").startswith("su***")


@pytest.mark.unit
def test_sensitive_keys_are_redacted_in_logs() -> None:
    payload = sanitize_mapping({"token": "abc12345", "records": 3})
    assert payload["token"] != "abc12345"
    assert payload["records"] == 3
