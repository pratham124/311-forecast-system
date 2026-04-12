from __future__ import annotations

import importlib.util
from pathlib import Path

from app.core import config as config_module
from app.core.logging import (
    summarize_forecast_confidence_event,
    summarize_forecast_confidence_failure,
    summarize_forecast_confidence_success,
    summarize_forecast_confidence_warning,
)


def test_get_settings_includes_uc16_confidence_defaults(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///./confidence-test.db")
    config_module.get_settings.cache_clear()

    settings = config_module.get_settings()

    assert settings.forecast_confidence_signal_lookback_hours == 48
    assert "confidence" in settings.forecast_confidence_normal_message.lower()
    assert "confidence" in settings.forecast_confidence_signals_missing_message.lower()
    config_module.get_settings.cache_clear()


def test_forecast_confidence_logging_helpers_set_expected_outcomes() -> None:
    assert summarize_forecast_confidence_event("forecast_confidence.event", scope="roads")["message"] == "forecast_confidence.event"
    assert summarize_forecast_confidence_success("forecast_confidence.success", scope="roads")["outcome"] == "success"
    assert summarize_forecast_confidence_warning("forecast_confidence.warning", scope="roads")["outcome"] == "warning"
    assert summarize_forecast_confidence_failure("forecast_confidence.failure", scope="roads")["outcome"] == "failure"


def test_uc16_migration_adds_and_drops_confidence_columns() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "versions"
        / "022_uc16_forecast_confidence.py"
    )
    spec = importlib.util.spec_from_file_location("uc16_migration", migration_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    added: list[str] = []
    dropped: list[str] = []

    class FakeBatchOperation:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def add_column(self, column):
            added.append(column.name)

        def drop_column(self, name):
            dropped.append(name)

    class FakeOp:
        def batch_alter_table(self, _table_name):
            return FakeBatchOperation()

    module.op = FakeOp()

    module.upgrade()
    module.downgrade()

    assert "confidence_assessment_status" in added
    assert "confidence_render_failure_reason" in added
    assert "confidence_assessment_status" in dropped
    assert "confidence_render_failure_reason" in dropped
