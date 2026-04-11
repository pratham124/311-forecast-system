from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.cleaned_dataset_repository import CleanedDatasetRepository
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.forecast_run_repository import ForecastRunRepository
from app.repositories.run_repository import RunRepository
from app.repositories.surge_configuration_repository import SurgeConfigurationRepository
from app.services.surge_alert_trigger_service import run_surge_alert_evaluation_for_forecast


def seed_surge_inputs(session, *, history_count: int = 1, current_count: int = 6, service_category: str = "Roads") -> str:
    dataset_repository = DatasetRepository(session)
    cleaned_repository = CleanedDatasetRepository(session)
    run_repository = RunRepository(session)
    forecast_repository = ForecastRepository(session)
    forecast_run_repository = ForecastRunRepository(session)

    evaluation_hour = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
    history_run = run_repository.create_run(trigger_type="scheduled", cursor_used=None)
    history_records: list[dict[str, object]] = []
    for offset in range(7):
        history_bucket = evaluation_hour - timedelta(hours=offset + 1)
        for index in range(history_count):
            history_records.append(
                {
                    "service_request_id": f"hist-{offset}-{index}",
                    "requested_at": history_bucket.isoformat().replace("+00:00", "Z"),
                    "category": service_category,
                }
            )
    history_version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id=history_run.run_id,
        candidate_id=None,
        record_count=len(history_records),
        records=history_records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="history-validation",
    )
    cleaned_repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id=history_run.run_id,
        source_dataset_version_id=history_version.dataset_version_id,
        approved_dataset_version_id=history_version.dataset_version_id,
        approved_by_validation_run_id="history-validation",
        cleaned_records=history_records,
    )
    dataset_repository.activate_dataset("edmonton_311", history_version.dataset_version_id, history_run.run_id)
    run_repository.finalize_run(
        history_run.run_id,
        status="completed",
        result_type="approved",
        records_received=len(history_records),
        dataset_version_id=history_version.dataset_version_id,
    )

    ingestion_run = run_repository.create_run(trigger_type="manual", cursor_used=None)
    current_records = [
        {
            "service_request_id": f"eval-{index}",
            "requested_at": evaluation_hour.isoformat().replace("+00:00", "Z"),
            "category": service_category,
        }
        for index in range(current_count)
    ]
    current_version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id=ingestion_run.run_id,
        candidate_id=None,
        record_count=len(current_records),
        records=current_records,
    )
    approved_current_version = dataset_repository.create_dataset_version(
        source_name="edmonton_311",
        run_id=ingestion_run.run_id,
        candidate_id=None,
        record_count=len(current_records),
        records=current_records,
        validation_status="approved",
        dataset_kind="cleaned",
        approved_by_validation_run_id="validation-current",
        source_dataset_version_id=current_version.dataset_version_id,
    )
    cleaned_repository.upsert_current_cleaned_records(
        source_name="edmonton_311",
        ingestion_run_id=ingestion_run.run_id,
        source_dataset_version_id=current_version.dataset_version_id,
        approved_dataset_version_id=approved_current_version.dataset_version_id,
        approved_by_validation_run_id="validation-current",
        cleaned_records=current_records,
    )
    dataset_repository.activate_dataset("edmonton_311", approved_current_version.dataset_version_id, ingestion_run.run_id)
    run_repository.finalize_run(
        ingestion_run.run_id,
        status="completed",
        result_type="approved",
        records_received=len(current_records),
        dataset_version_id=current_version.dataset_version_id,
    )

    forecast_run = forecast_run_repository.create_run(
        trigger_type="scheduled",
        source_cleaned_dataset_version_id=approved_current_version.dataset_version_id,
        requested_horizon_start=evaluation_hour,
        requested_horizon_end=evaluation_hour + timedelta(hours=1),
    )
    forecast_version = forecast_repository.create_forecast_version(
        forecast_run_id=forecast_run.forecast_run_id,
        source_cleaned_dataset_version_id=approved_current_version.dataset_version_id,
        horizon_start=evaluation_hour,
        horizon_end=evaluation_hour + timedelta(hours=1),
        geography_scope="citywide",
        baseline_method="historical_hourly_mean",
        summary="Surge test forecast",
    )
    forecast_repository.store_buckets(
        forecast_version.forecast_version_id,
        [
            {
                "bucket_start": evaluation_hour,
                "bucket_end": evaluation_hour + timedelta(hours=1),
                "service_category": service_category,
                "geography_key": None,
                "point_forecast": 2,
                "quantile_p10": 1,
                "quantile_p50": 2,
                "quantile_p90": 3,
                "baseline_value": 1,
            }
        ],
    )
    forecast_repository.mark_version_stored(forecast_version.forecast_version_id, bucket_count=1)
    forecast_repository.activate_forecast(
        forecast_product_name="daily_1_day_demand",
        forecast_version_id=forecast_version.forecast_version_id,
        source_cleaned_dataset_version_id=approved_current_version.dataset_version_id,
        horizon_start=evaluation_hour,
        horizon_end=evaluation_hour + timedelta(hours=1),
        updated_by_run_id=forecast_run.forecast_run_id,
        geography_scope="citywide",
    )
    session.commit()
    return ingestion_run.run_id


def test_surge_alert_evaluation_and_review_contracts(app_client, operational_manager_headers, planner_headers, session) -> None:
    seed_surge_inputs(session)
    SurgeConfigurationRepository(session).create_configuration(
        service_category="Roads",
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        rolling_baseline_window_count=7,
        notification_channels=["email", "dashboard"],
        operational_manager_id="manager-1",
    )
    session.commit()

    forecast_version_id = ForecastRepository(session).get_current_marker("daily_1_day_demand").forecast_version_id
    evaluation_run = run_surge_alert_evaluation_for_forecast(session, forecast_version_id=forecast_version_id)
    session.commit()

    listing = app_client.get("/api/v1/surge-alerts/evaluations", headers=planner_headers)
    assert listing.status_code == 200
    evaluation_items = listing.json()["items"]
    assert len(evaluation_items) == 1
    assert evaluation_items[0]["candidateCount"] == 1
    assert evaluation_items[0]["confirmedCount"] == 1
    assert evaluation_items[0]["triggerSource"] == "ingestion_completion"

    detail = app_client.get(
        f"/api/v1/surge-alerts/evaluations/{evaluation_run.surge_evaluation_run_id}",
        headers=planner_headers,
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["candidates"][0]["candidateStatus"] == "flagged"
    assert detail_body["candidates"][0]["confirmation"]["outcome"] == "confirmed"

    events = app_client.get("/api/v1/surge-alerts/events", headers=planner_headers)
    assert events.status_code == 200
    first_event = events.json()["items"][0]
    assert first_event["serviceCategory"] == "Roads"
    assert first_event["overallDeliveryStatus"] == "delivered"

    event_detail = app_client.get(
        f"/api/v1/surge-alerts/events/{first_event['surgeNotificationEventId']}",
        headers=planner_headers,
    )
    assert event_detail.status_code == 200
    assert len(event_detail.json()["channelAttempts"]) == 2


def test_surge_alert_manual_replay_trigger_contract(app_client, operational_manager_headers, session) -> None:
    seed_surge_inputs(session)
    SurgeConfigurationRepository(session).create_configuration(
        service_category="Roads",
        z_score_threshold=2.0,
        percent_above_forecast_floor=100.0,
        rolling_baseline_window_count=7,
        notification_channels=["dashboard"],
        operational_manager_id="manager-1",
    )
    session.commit()

    forecast_version_id = ForecastRepository(session).get_current_marker("daily_1_day_demand").forecast_version_id
    response = app_client.post(
        "/api/v1/surge-alerts/evaluations",
        json={
            "forecastReferenceId": forecast_version_id,
            "triggerSource": "manual_replay",
        },
        headers=operational_manager_headers,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert body["surgeEvaluationRunId"]
    assert body["acceptedAt"]


def test_surge_alert_api_requires_auth(app_client, viewer_headers) -> None:
    assert app_client.get("/api/v1/surge-alerts/events").status_code == 401
    assert app_client.get("/api/v1/surge-alerts/events", headers=viewer_headers).status_code == 403
