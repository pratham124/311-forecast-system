from __future__ import annotations

import pytest

from app.services.duplicate_analysis_service import DuplicateAnalysisService
from app.services.duplicate_resolution_service import DuplicateResolutionService


@pytest.mark.unit
def test_duplicate_analysis_calculates_percentage_and_groups() -> None:
    records = [
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads"},
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads"},
        {"service_request_id": "SR-2", "requested_at": "2026-03-16T11:00:00Z", "category": "Transit"},
    ]

    outcome = DuplicateAnalysisService().analyze(records, threshold_percentage=50)

    assert outcome.status == "passed"
    assert outcome.duplicate_group_count == 1
    assert outcome.duplicate_record_count == 1
    assert outcome.duplicate_percentage == pytest.approx(33.33, rel=0.001)


@pytest.mark.unit
def test_duplicate_resolution_consolidates_to_one_record_per_group() -> None:
    records = [
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads", "district": "NW"},
        {"service_request_id": "SR-1", "requested_at": "2026-03-16T10:00:00Z", "category": "Roads", "district": ""},
        {"service_request_id": "SR-2", "requested_at": "2026-03-16T11:00:00Z", "category": "Transit", "district": "SE"},
    ]
    analysis = DuplicateAnalysisService().analyze(records, threshold_percentage=50)

    cleaned_records, resolutions = DuplicateResolutionService().resolve(records, analysis.groups)

    assert len(cleaned_records) == 2
    assert len(resolutions) == 1
    assert resolutions[0].group_key == "SR-1"
    assert resolutions[0].cleaned_record["district"] == "NW"
