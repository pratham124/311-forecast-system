from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.repositories.dataset_repository import DatasetRepository
from app.repositories.historical_demand_repository import HistoricalDemandRepository


def _dataset_version_id(session) -> str:
    records = [
        {"service_request_id": "r1", "requested_at": "2026-03-05T10:00:00Z", "category": "Roads", "ward": "W1"},
    ]
    version = DatasetRepository(session).create_dataset_version(
        source_name="edmonton_311",
        run_id="run-repo",
        candidate_id=None,
        record_count=len(records),
        records=records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="val-repo",
    )
    DatasetRepository(session).activate_dataset("edmonton_311", version.dataset_version_id, "run-repo")
    session.commit()
    return version.dataset_version_id


@pytest.mark.integration
def test_get_result_bundle_returns_none_when_no_result(session) -> None:
    repo = HistoricalDemandRepository(session)
    assert repo.get_result_bundle("00000000-0000-0000-0000-000000000000") is None


@pytest.mark.integration
def test_require_request_raises_lookup_error(session) -> None:
    repo = HistoricalDemandRepository(session)
    with pytest.raises(LookupError, match="not found"):
        repo.require_request("00000000-0000-0000-0000-000000000000")


@pytest.mark.integration
def test_get_result_bundle_returns_ordered_points(session) -> None:
    vid = _dataset_version_id(session)
    repo = HistoricalDemandRepository(session)
    req = repo.create_request(
        requested_by_actor="city_planner",
        source_cleaned_dataset_version_id=vid,
        service_category_filter="Roads",
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
        geography_filter_type="ward",
        geography_filter_value="W1",
        warning_status="not_needed",
    )
    res = repo.create_result(
        analysis_request_id=req.analysis_request_id,
        source_cleaned_dataset_version_id=vid,
        aggregation_granularity="daily",
        result_mode="chart_and_table",
        service_category_filter="Roads",
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
        geography_filter_type="ward",
        geography_filter_value="W1",
        record_count=2,
    )
    b1 = datetime(2026, 3, 5, tzinfo=timezone.utc)
    b2 = datetime(2026, 3, 6, tzinfo=timezone.utc)
    repo.replace_summary_points(
        res.analysis_result_id,
        [
            {
                "bucket_start": b2,
                "bucket_end": datetime(2026, 3, 7, tzinfo=timezone.utc),
                "service_category": "Roads",
                "geography_key": "W1",
                "demand_count": 1,
            },
            {
                "bucket_start": b1,
                "bucket_end": datetime(2026, 3, 6, tzinfo=timezone.utc),
                "service_category": "Roads",
                "geography_key": "W1",
                "demand_count": 2,
            },
        ],
    )
    session.commit()
    bundle = repo.get_result_bundle(req.analysis_request_id)
    assert bundle is not None
    _result, points = bundle
    assert len(points) == 2
    assert points[0].bucket_start.replace(tzinfo=timezone.utc) == b1
    assert points[1].bucket_start.replace(tzinfo=timezone.utc) == b2


@pytest.mark.integration
def test_upsert_outcome_updates_existing_row(session) -> None:
    vid = _dataset_version_id(session)
    repo = HistoricalDemandRepository(session)
    req = repo.create_request(
        requested_by_actor="city_planner",
        source_cleaned_dataset_version_id=vid,
        service_category_filter=None,
        time_range_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        time_range_end=datetime(2026, 3, 31, tzinfo=timezone.utc),
        geography_filter_type=None,
        geography_filter_value=None,
        warning_status="not_needed",
    )
    repo.upsert_outcome(
        analysis_request_id=req.analysis_request_id,
        outcome_type="success",
        warning_acknowledged=False,
        message="first",
    )
    session.commit()
    repo.upsert_outcome(
        analysis_request_id=req.analysis_request_id,
        outcome_type="no_data",
        warning_acknowledged=True,
        message="second",
    )
    session.commit()
    from app.models import HistoricalAnalysisOutcomeRecord

    row = session.query(HistoricalAnalysisOutcomeRecord).filter_by(analysis_request_id=req.analysis_request_id).one()
    assert row.outcome_type == "no_data"
    assert row.warning_acknowledged is True
    assert row.message == "second"
