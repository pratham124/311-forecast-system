from __future__ import annotations

import pytest

from app.services.forecast_accuracy_alignment_service import ForecastAccuracyAlignmentService


def test_alignment_service_rejects_empty_overlap() -> None:
    service = ForecastAccuracyAlignmentService()
    with pytest.raises(ValueError, match="No overlapping forecast and actual buckets"):
        service.align(
            forecast_rows=[],
            actual_rows=[],
        )
