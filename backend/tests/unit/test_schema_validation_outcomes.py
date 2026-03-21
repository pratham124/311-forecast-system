from __future__ import annotations

import pytest

from app.services.schema_validation_service import SchemaValidationService


@pytest.mark.unit
def test_schema_validation_rejects_missing_required_fields() -> None:
    outcome = SchemaValidationService().validate([
        {"service_request_id": "SR-1", "category": "Roads"},
    ])

    assert outcome.passed is False
    assert outcome.status == "rejected"
    assert outcome.required_field_check == "failed"
    assert "missing fields" in outcome.issue_summary


@pytest.mark.unit
def test_schema_validation_accepts_well_formed_records() -> None:
    outcome = SchemaValidationService().validate([
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads"},
    ])

    assert outcome.passed is True
    assert outcome.status == "passed"
    assert outcome.issue_summary is None
