from __future__ import annotations

import logging

import pytest

from app.core.logging import configure_logging, redact_value, sanitize_mapping, summarize_status


@pytest.mark.unit
def test_secret_values_are_masked() -> None:
    assert redact_value("super-secret-token").startswith("su***")


@pytest.mark.unit
def test_short_string_and_none_are_masked() -> None:
    assert redact_value("abcd") == "***"
    assert redact_value(None) is None


@pytest.mark.unit
def test_redact_value_handles_dicts_lists_and_passthrough_values() -> None:
    payload = {"token": "abc12345", "nested": {"secret": "hidden-value"}}
    values = [payload, "plain-text", 3]

    redacted_list = redact_value(values)

    assert redacted_list[0]["token"] != "abc12345"
    assert redacted_list[0]["nested"]["secret"] != "hidden-value"
    assert redacted_list[1].startswith("pl***")
    assert redacted_list[2] == 3


@pytest.mark.unit
def test_sensitive_keys_are_redacted_in_logs() -> None:
    payload = sanitize_mapping({"token": "abc12345", "records": 3})
    assert payload["token"] != "abc12345"
    assert payload["records"] == 3


@pytest.mark.unit
def test_sanitize_mapping_covers_nested_lists_and_plain_values() -> None:
    payload = sanitize_mapping(
        {
            "records": [{"api_key": "secret-key", "count": 1}, "keep-me"],
            "status": "ok",
        }
    )

    assert payload["records"][0]["api_key"] != "secret-key"
    assert payload["records"][1] == "keep-me"
    assert payload["status"] == "ok"


@pytest.mark.unit
def test_summarize_status_and_configure_logging() -> None:
    summary = summarize_status("validation.completed", password="abcd1234", count=2)
    logger = configure_logging()

    assert summary["message"] == "validation.completed"
    assert summary["password"] != "abcd1234"
    assert summary["count"] == 2
    assert isinstance(logger, logging.Logger)
    assert logger.name == "forecast_system"
