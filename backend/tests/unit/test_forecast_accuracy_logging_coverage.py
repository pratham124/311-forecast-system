from __future__ import annotations

from app.core.logging import (
    configure_logging,
    redact_value,
    sanitize_mapping,
    summarize_evaluation_event,
    summarize_evaluation_failure,
    summarize_evaluation_partial_success,
    summarize_evaluation_success,
    summarize_forecast_accuracy_event,
    summarize_forecast_accuracy_failure,
    summarize_forecast_accuracy_success,
    summarize_historical_demand_event,
    summarize_historical_demand_failure,
    summarize_historical_demand_no_data,
    summarize_historical_demand_success,
    summarize_historical_demand_warning,
    summarize_public_forecast_error,
    summarize_public_forecast_event,
    summarize_public_forecast_success,
    summarize_status,
    summarize_threshold_alert_event,
    summarize_threshold_alert_failure,
    summarize_threshold_alert_success,
    summarize_threshold_alert_warning,
    summarize_user_guide_error,
    summarize_user_guide_event,
    summarize_user_guide_success,
    summarize_visualization_event,
)


def test_logging_helpers_cover_redaction_and_wrapper_functions() -> None:
    assert redact_value(None) is None
    assert redact_value("abcd") == "***"
    assert redact_value("abcdef") == "ab***ef"
    assert redact_value({"token": "abcdef"}) == {"token": "ab***ef"}
    assert redact_value(["abcdef", None]) == ["ab***ef", None]
    assert redact_value(3) == 3

    sanitized = sanitize_mapping(
        {
            "authorization": "Bearer abcdef",
            "nested": {"password": "secretpw", "safe": 1},
            "items": [{"api_key": "apikey123"}, 2],
            "plain": "ok",
        }
    )
    assert sanitized["authorization"].startswith("Be***")
    assert sanitized["nested"]["password"].startswith("se***")
    assert sanitized["nested"]["safe"] == 1
    assert sanitized["items"][0]["api_key"].startswith("ap***")
    assert sanitized["items"][1] == 2
    assert sanitized["plain"] == "ok"

    assert summarize_status("msg", password="abcdef") == {"password": "ab***ef", "message": "msg"}
    assert configure_logging().name == "forecast_system"
    assert summarize_visualization_event("viz")["message"] == "viz"

    assert summarize_evaluation_success("eval")["outcome"] == "success"
    assert summarize_evaluation_partial_success("eval")["outcome"] == "partial_success"
    assert summarize_evaluation_failure("eval")["outcome"] == "failure"
    assert summarize_evaluation_event("eval", outcome="partial_success")["outcome"] == "partial_success"
    assert summarize_evaluation_event("eval", outcome="failure")["outcome"] == "failure"
    assert summarize_evaluation_event("eval")["outcome"] == "success"

    assert summarize_historical_demand_event("hist")["message"] == "hist"
    assert summarize_historical_demand_success("hist")["outcome"] == "success"
    assert summarize_historical_demand_warning("hist")["outcome"] == "warning"
    assert summarize_historical_demand_no_data("hist")["outcome"] == "no_data"
    assert summarize_historical_demand_failure("hist")["outcome"] == "failure"

    assert summarize_public_forecast_event("pub")["message"] == "pub"
    assert summarize_public_forecast_success("pub")["outcome"] == "success"
    assert summarize_public_forecast_error("pub")["outcome"] == "error"

    assert summarize_user_guide_event("guide")["message"] == "guide"
    assert summarize_user_guide_success("guide")["outcome"] == "success"
    assert summarize_user_guide_error("guide")["outcome"] == "error"

    assert summarize_threshold_alert_event("alert")["message"] == "alert"
    assert summarize_threshold_alert_success("alert")["outcome"] == "success"
    assert summarize_threshold_alert_warning("alert")["outcome"] == "warning"
    assert summarize_threshold_alert_failure("alert")["outcome"] == "failure"

    assert summarize_forecast_accuracy_event("fa")["message"] == "fa"
    assert summarize_forecast_accuracy_success("fa")["outcome"] == "success"
    assert summarize_forecast_accuracy_failure("fa")["outcome"] == "failure"
