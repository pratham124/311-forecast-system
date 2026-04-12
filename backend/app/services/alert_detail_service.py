from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import logging
from typing import Any

import pandas as pd
from fastapi import HTTPException, status

from app.core.logging import summarize_status
from app.pipelines.forecasting.feature_preparation import prepare_forecast_features
from app.pipelines.forecasting.hourly_demand_pipeline import HourlyDemandPipeline, TrainedHourlyDemandArtifact
from app.pipelines.forecasting.weekly_demand_pipeline import TrainedWeeklyDemandArtifact, WeeklyDemandPipeline
from app.pipelines.forecasting.weekly_feature_preparation import prepare_weekly_forecast_features
from app.schemas.alert_details import (
    AlertAnomaliesComponentRead,
    AlertAnomalyContextItemRead,
    AlertDetailRead,
    AlertDetailRenderEvent,
    AlertDetailRenderEventResponse,
    AlertDistributionComponentRead,
    AlertDistributionPointRead,
    AlertDriverRead,
    AlertDriversComponentRead,
    AlertScopeRead,
)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _fetch_historical_weather(weather_client: object, start: datetime, end: datetime) -> list[dict[str, object]]:
    if hasattr(weather_client, "fetch_historical_hourly_conditions"):
        return list(weather_client.fetch_historical_hourly_conditions(start, end))
    if hasattr(weather_client, "fetch_hourly_conditions"):
        return list(weather_client.fetch_hourly_conditions(start, end))
    return []


def _fetch_forecast_weather(weather_client: object, start: datetime, end: datetime) -> list[dict[str, object]]:
    if hasattr(weather_client, "fetch_forecast_hourly_conditions"):
        return list(weather_client.fetch_forecast_hourly_conditions(start, end))
    if hasattr(weather_client, "fetch_hourly_conditions"):
        return list(weather_client.fetch_hourly_conditions(start, end))
    return []


def _merge_weather_rows(*weather_sets: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[datetime, dict[str, object]] = {}
    for rows in weather_sets:
        for row in rows:
            timestamp = row.get("timestamp")
            if isinstance(timestamp, datetime):
                merged[_ensure_utc(timestamp)] = {**row, "timestamp": _ensure_utc(timestamp)}
    return [merged[timestamp] for timestamp in sorted(merged)]


@dataclass
class _ResolvedAlertSource:
    alert_source: str
    alert_id: str
    correlation_id: str | None
    service_category: str
    geography_type: str | None
    geography_value: str | None
    alert_triggered_at: datetime
    overall_delivery_status: str
    forecast_product: str | None
    forecast_reference_id: str | None
    forecast_window_type: str | None
    window_start: datetime
    window_end: datetime
    primary_metric_label: str
    primary_metric_value: float
    secondary_metric_label: str
    secondary_metric_value: float
    threshold_evaluation_run_id: str | None = None
    surge_evaluation_run_id: str | None = None
    surge_candidate_id: str | None = None


@dataclass
class _ComponentOutcome:
    status: str
    payload: Any
    reason: str | None = None


class AlertDetailService:
    def __init__(
        self,
        *,
        alert_detail_repository,
        notification_event_repository,
        threshold_evaluation_repository,
        surge_notification_event_repository,
        surge_evaluation_repository,
        forecast_repository,
        weekly_forecast_repository,
        cleaned_dataset_repository,
        forecast_model_repository,
        forecast_training_service,
        weekly_forecast_training_service,
        geomet_client,
        nager_date_client,
        settings,
        logger: logging.Logger | None = None,
    ) -> None:
        self.alert_detail_repository = alert_detail_repository
        self.notification_event_repository = notification_event_repository
        self.threshold_evaluation_repository = threshold_evaluation_repository
        self.surge_notification_event_repository = surge_notification_event_repository
        self.surge_evaluation_repository = surge_evaluation_repository
        self.forecast_repository = forecast_repository
        self.weekly_forecast_repository = weekly_forecast_repository
        self.cleaned_dataset_repository = cleaned_dataset_repository
        self.forecast_model_repository = forecast_model_repository
        self.forecast_training_service = forecast_training_service
        self.weekly_forecast_training_service = weekly_forecast_training_service
        self.geomet_client = geomet_client
        self.nager_date_client = nager_date_client
        self.settings = settings
        self.logger = logger or logging.getLogger("alert_details")

    def get_alert_detail(self, *, alert_source: str, alert_id: str, claims: dict) -> AlertDetailRead:
        resolved = self._resolve_alert_source(alert_source=alert_source, alert_id=alert_id)
        subject = str(claims.get("sub") or "")
        load = self.alert_detail_repository.create_load(
            alert_source=resolved.alert_source,
            alert_id=resolved.alert_id,
            requested_by_subject=subject,
        )
        self._log(
            "alert_details.request.started",
            alert_detail_load_id=load.alert_detail_load_id,
            alert_source=resolved.alert_source,
            alert_id=resolved.alert_id,
        )

        distribution = self._execute_component(
            load.alert_detail_load_id,
            "distribution",
            lambda: self._build_distribution_context(resolved),
        )
        drivers = self._execute_component(
            load.alert_detail_load_id,
            "drivers",
            lambda: self._build_driver_context(resolved),
        )
        anomalies = self._execute_component(
            load.alert_detail_load_id,
            "anomalies",
            lambda: self._build_anomaly_context(resolved),
        )

        view_status, failure_reason = self._classify_view_status(
            distribution_status=distribution.status,
            drivers_status=drivers.status,
            anomalies_status=anomalies.status,
            distribution_reason=distribution.reason,
            drivers_reason=drivers.reason,
            anomalies_reason=anomalies.reason,
        )
        self.alert_detail_repository.finalize_load(
            load.alert_detail_load_id,
            view_status=view_status,
            distribution_status=distribution.status,
            drivers_status=drivers.status,
            anomalies_status=anomalies.status,
            preparation_status="completed",
            failure_reason=failure_reason,
            source_forecast_version_id=(
                resolved.forecast_reference_id if resolved.forecast_product == "daily" else None
            ),
            source_weekly_forecast_version_id=(
                resolved.forecast_reference_id if resolved.forecast_product == "weekly" else None
            ),
            source_threshold_evaluation_run_id=resolved.threshold_evaluation_run_id,
            source_surge_evaluation_run_id=resolved.surge_evaluation_run_id,
            source_surge_candidate_id=resolved.surge_candidate_id,
            correlation_id=resolved.correlation_id,
        )
        self._log(
            "alert_details.prepared",
            alert_detail_load_id=load.alert_detail_load_id,
            view_status=view_status,
            distribution_status=distribution.status,
            drivers_status=drivers.status,
            anomalies_status=anomalies.status,
        )
        return AlertDetailRead(
            alertDetailLoadId=load.alert_detail_load_id,
            alertSource=resolved.alert_source,
            alertId=resolved.alert_id,
            correlationId=resolved.correlation_id,
            alertTriggeredAt=resolved.alert_triggered_at,
            overallDeliveryStatus=resolved.overall_delivery_status,
            forecastProduct=resolved.forecast_product,
            forecastReferenceId=resolved.forecast_reference_id,
            forecastWindowType=resolved.forecast_window_type,
            windowStart=resolved.window_start,
            windowEnd=resolved.window_end,
            primaryMetricLabel=resolved.primary_metric_label,
            primaryMetricValue=resolved.primary_metric_value,
            secondaryMetricLabel=resolved.secondary_metric_label,
            secondaryMetricValue=resolved.secondary_metric_value,
            scope=AlertScopeRead(
                serviceCategory=resolved.service_category,
                geographyType=resolved.geography_type,
                geographyValue=resolved.geography_value,
            ),
            viewStatus=view_status,
            failureReason=failure_reason,
            distribution=distribution.payload,
            drivers=drivers.payload,
            anomalies=anomalies.payload,
        )

    def record_render_event(
        self,
        *,
        alert_detail_load_id: str,
        payload: AlertDetailRenderEvent,
        claims: dict,
    ) -> AlertDetailRenderEventResponse:
        try:
            record = self.alert_detail_repository.require_load(alert_detail_load_id)
        except LookupError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert detail load not found") from exc
        roles = claims.get("roles", [])
        subject = str(claims.get("sub") or "")
        if "OperationalManager" not in roles and record.requested_by_subject != subject:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        updated = self.alert_detail_repository.record_render_event(
            alert_detail_load_id,
            render_status=payload.render_status,
            failure_reason=payload.failure_reason,
        )
        event_name = "alert_details.rendered" if payload.render_status == "rendered" else "alert_details.render_failed"
        self._log(
            event_name,
            alert_detail_load_id=alert_detail_load_id,
            alert_source=updated.alert_source,
            alert_id=updated.alert_id,
            failure_reason=payload.failure_reason,
        )
        return AlertDetailRenderEventResponse(
            alertDetailLoadId=alert_detail_load_id,
            recordedOutcomeStatus=payload.render_status,
            message="Render event recorded.",
        )

    def _resolve_alert_source(self, *, alert_source: str, alert_id: str) -> _ResolvedAlertSource:
        if alert_source == "threshold_alert":
            bundle = self.notification_event_repository.get_event_bundle(alert_id)
            if bundle is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert event not found")
            run = self.threshold_evaluation_repository.get_run(bundle.event.threshold_evaluation_run_id)
            return _ResolvedAlertSource(
                alert_source=alert_source,
                alert_id=alert_id,
                correlation_id=bundle.event.notification_event_id,
                service_category=bundle.event.service_category,
                geography_type=bundle.event.geography_type,
                geography_value=bundle.event.geography_value,
                alert_triggered_at=bundle.event.created_at,
                overall_delivery_status=bundle.event.overall_delivery_status,
                forecast_product=None if run is None else run.forecast_product,
                forecast_reference_id=None if run is None else run.forecast_version_reference,
                forecast_window_type=bundle.event.forecast_window_type,
                window_start=bundle.event.forecast_window_start,
                window_end=bundle.event.forecast_window_end,
                primary_metric_label="Forecast",
                primary_metric_value=float(bundle.event.forecast_value),
                secondary_metric_label="Threshold",
                secondary_metric_value=float(bundle.event.threshold_value),
                threshold_evaluation_run_id=bundle.event.threshold_evaluation_run_id,
            )
        if alert_source == "surge_alert":
            bundle = self.surge_notification_event_repository.get_event_bundle(alert_id)
            if bundle is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surge alert event not found")
            candidate_bundle = self.surge_evaluation_repository.get_candidate_bundle(bundle.event.surge_candidate_id)
            forecast_reference_id = None if candidate_bundle is None else candidate_bundle.candidate.forecast_version_id
            return _ResolvedAlertSource(
                alert_source=alert_source,
                alert_id=alert_id,
                correlation_id=bundle.event.correlation_id,
                service_category=bundle.event.service_category,
                geography_type=None,
                geography_value=None,
                alert_triggered_at=bundle.event.created_at,
                overall_delivery_status=bundle.event.overall_delivery_status,
                forecast_product=bundle.event.forecast_product,
                forecast_reference_id=forecast_reference_id,
                forecast_window_type="hourly",
                window_start=bundle.event.evaluation_window_start,
                window_end=bundle.event.evaluation_window_end,
                primary_metric_label="Actual demand",
                primary_metric_value=float(bundle.event.actual_demand_value),
                secondary_metric_label="Forecast P50",
                secondary_metric_value=float(bundle.event.forecast_p50_value),
                surge_evaluation_run_id=bundle.event.surge_evaluation_run_id,
                surge_candidate_id=bundle.event.surge_candidate_id,
            )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unsupported alert source")

    def _execute_component(self, alert_detail_load_id: str, name: str, builder) -> _ComponentOutcome:
        try:
            outcome = builder()
        except Exception as exc:  # noqa: BLE001
            self._log(
                f"alert_details.component.{name}",
                alert_detail_load_id=alert_detail_load_id,
                component=name,
                component_status="failed",
                failure_reason=str(exc),
            )
            if name == "distribution":
                payload = AlertDistributionComponentRead(status="failed", failureReason=str(exc))
            elif name == "drivers":
                payload = AlertDriversComponentRead(status="failed", failureReason=str(exc))
            else:
                payload = AlertAnomaliesComponentRead(status="failed", failureReason=str(exc))
            return _ComponentOutcome(status="failed", payload=payload, reason=str(exc))
        self._log(
            f"alert_details.component.{name}",
            alert_detail_load_id=alert_detail_load_id,
            component=name,
            component_status=outcome.status,
            reason=outcome.reason,
        )
        return outcome

    def _classify_view_status(
        self,
        *,
        distribution_status: str,
        drivers_status: str,
        anomalies_status: str,
        distribution_reason: str | None,
        drivers_reason: str | None,
        anomalies_reason: str | None,
    ) -> tuple[str, str | None]:
        statuses = [distribution_status, drivers_status, anomalies_status]
        reasons = [distribution_reason, drivers_reason, anomalies_reason]
        if any(item == "failed" for item in statuses):
            return "error", next((reason for reason in reasons if reason), "Alert detail preparation failed.")
        if all(item == "unavailable" for item in statuses):
            return "unavailable", "All detail components were unavailable for this alert."
        if all(item == "available" for item in statuses):
            return "rendered", None
        return "partial", None

    def _build_distribution_context(self, resolved: _ResolvedAlertSource) -> _ComponentOutcome:
        if resolved.forecast_product == "daily" and resolved.forecast_reference_id:
            version = self.forecast_repository.get_forecast_version(resolved.forecast_reference_id)
            if version is None:
                return _ComponentOutcome(
                    status="failed",
                    payload=AlertDistributionComponentRead(status="failed", failureReason="Forecast version not found."),
                    reason="Forecast version not found.",
                )
            buckets = self.forecast_repository.list_buckets(resolved.forecast_reference_id)
            points = self._daily_distribution_points(resolved, buckets)
            if not points:
                return _ComponentOutcome(
                    status="unavailable",
                    payload=AlertDistributionComponentRead(
                        status="unavailable",
                        granularity="hourly",
                        unavailableReason="Distribution data was not available for the selected alert scope.",
                    ),
                    reason="Distribution data was not available for the selected alert scope.",
                )
            summary_value = next(
                (point.p50 for point in points if point.is_alerted_bucket),
                resolved.primary_metric_value,
            )
            return _ComponentOutcome(
                status="available",
                payload=AlertDistributionComponentRead(
                    status="available",
                    granularity="hourly",
                    summaryValue=summary_value,
                    points=points,
                ),
            )
        if resolved.forecast_product == "weekly" and resolved.forecast_reference_id:
            version = self.weekly_forecast_repository.get_forecast_version(resolved.forecast_reference_id)
            if version is None:
                return _ComponentOutcome(
                    status="failed",
                    payload=AlertDistributionComponentRead(status="failed", failureReason="Weekly forecast version not found."),
                    reason="Weekly forecast version not found.",
                )
            buckets = self.weekly_forecast_repository.list_buckets(resolved.forecast_reference_id)
            points = self._weekly_distribution_points(resolved, buckets)
            if not points:
                return _ComponentOutcome(
                    status="unavailable",
                    payload=AlertDistributionComponentRead(
                        status="unavailable",
                        granularity="daily",
                        unavailableReason="Distribution data was not available for the selected alert scope.",
                    ),
                    reason="Distribution data was not available for the selected alert scope.",
                )
            summary_value = next(
                (point.p50 for point in points if point.is_alerted_bucket),
                resolved.primary_metric_value,
            )
            return _ComponentOutcome(
                status="available",
                payload=AlertDistributionComponentRead(
                    status="available",
                    granularity="daily",
                    summaryValue=summary_value,
                    points=points,
                ),
            )
        return _ComponentOutcome(
            status="unavailable",
            payload=AlertDistributionComponentRead(
                status="unavailable",
                unavailableReason="This alert is not linked to a forecast distribution.",
            ),
            reason="This alert is not linked to a forecast distribution.",
        )

    def _daily_distribution_points(self, resolved: _ResolvedAlertSource, buckets: list[Any]) -> list[AlertDistributionPointRead]:
        grouped: dict[tuple[datetime, datetime], dict[str, Any]] = {}
        for bucket in buckets:
            if bucket.service_category != resolved.service_category:
                continue
            if resolved.geography_value is not None and bucket.geography_key != resolved.geography_value:
                continue
            key = (_ensure_utc(bucket.bucket_start), _ensure_utc(bucket.bucket_end))
            if key not in grouped:
                grouped[key] = {
                    "bucket_start": key[0],
                    "bucket_end": key[1],
                    "p10": 0.0,
                    "p50": 0.0,
                    "p90": 0.0,
                }
            grouped[key]["p10"] += float(bucket.quantile_p10)
            grouped[key]["p50"] += float(bucket.quantile_p50)
            grouped[key]["p90"] += float(bucket.quantile_p90)
        alerted_start = self._resolve_alerted_daily_bucket_start(resolved, grouped)
        points: list[AlertDistributionPointRead] = []
        for key in sorted(grouped):
            payload = grouped[key]
            points.append(
                AlertDistributionPointRead(
                    label=payload["bucket_start"].isoformat(),
                    bucketStart=payload["bucket_start"],
                    bucketEnd=payload["bucket_end"],
                    p10=payload["p10"],
                    p50=payload["p50"],
                    p90=payload["p90"],
                    isAlertedBucket=payload["bucket_start"] == alerted_start,
                )
            )
        return points

    def _weekly_distribution_points(self, resolved: _ResolvedAlertSource, buckets: list[Any]) -> list[AlertDistributionPointRead]:
        grouped: dict[date, dict[str, Any]] = {}
        for bucket in buckets:
            if bucket.service_category != resolved.service_category:
                continue
            if resolved.geography_value is not None and bucket.geography_key != resolved.geography_value:
                continue
            key = bucket.forecast_date_local
            if key not in grouped:
                grouped[key] = {"p10": 0.0, "p50": 0.0, "p90": 0.0}
                grouped[key]["p10"] += float(bucket.quantile_p10)
            grouped[key]["p50"] += float(bucket.quantile_p50)
            grouped[key]["p90"] += float(bucket.quantile_p90)
        points: list[AlertDistributionPointRead] = []
        alert_date = self._resolve_alerted_weekly_bucket_date(resolved, grouped)
        for forecast_date in sorted(grouped):
            payload = grouped[forecast_date]
            points.append(
                AlertDistributionPointRead(
                    label=forecast_date.isoformat(),
                    forecastDateLocal=forecast_date,
                    p10=payload["p10"],
                    p50=payload["p50"],
                    p90=payload["p90"],
                    isAlertedBucket=forecast_date == alert_date,
                )
            )
        return points

    def _resolve_alerted_daily_bucket_start(
        self,
        resolved: _ResolvedAlertSource,
        grouped: dict[tuple[datetime, datetime], dict[str, Any]],
    ) -> datetime:
        if resolved.alert_source == "threshold_alert":
            for bucket_start, _bucket_end in sorted(grouped):
                if float(grouped[(bucket_start, _bucket_end)]["p50"]) >= resolved.secondary_metric_value:
                    return bucket_start
        return _ensure_utc(resolved.window_start)

    def _resolve_alerted_weekly_bucket_date(
        self,
        resolved: _ResolvedAlertSource,
        grouped: dict[date, dict[str, Any]],
    ) -> date:
        if resolved.alert_source == "threshold_alert":
            for forecast_date in sorted(grouped):
                if float(grouped[forecast_date]["p50"]) >= resolved.secondary_metric_value:
                    return forecast_date
        return _ensure_utc(resolved.window_start).date()

    def _build_driver_context(self, resolved: _ResolvedAlertSource) -> _ComponentOutcome:
        if resolved.forecast_product == "daily" and resolved.forecast_reference_id:
            return self._build_daily_driver_context(resolved)
        if resolved.forecast_product == "weekly" and resolved.forecast_reference_id:
            return self._build_weekly_driver_context(resolved)
        return _ComponentOutcome(
            status="unavailable",
            payload=AlertDriversComponentRead(
                status="unavailable",
                unavailableReason="This alert is not linked to a forecast model artifact.",
            ),
            reason="This alert is not linked to a forecast model artifact.",
        )

    def _build_daily_driver_context(self, resolved: _ResolvedAlertSource) -> _ComponentOutcome:
        version = self.forecast_repository.get_forecast_version(resolved.forecast_reference_id)
        if version is None:
            return _ComponentOutcome(
                status="failed",
                payload=AlertDriversComponentRead(status="failed", failureReason="Forecast version not found."),
                reason="Forecast version not found.",
            )
        stored_model = self.forecast_model_repository.find_current_model(self.settings.forecast_product_name)
        if stored_model is None:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="No compatible daily forecast model is currently available.",
                ),
                reason="No compatible daily forecast model is currently available.",
            )
        if stored_model.source_cleaned_dataset_version_id != version.source_cleaned_dataset_version_id:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="The current daily forecast model does not match this alert's forecast lineage.",
                ),
                reason="The current daily forecast model does not match this alert's forecast lineage.",
            )
        if stored_model.feature_schema_version != HourlyDemandPipeline.feature_schema_version:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="The daily forecast model uses an incompatible feature schema.",
                ),
                reason="The daily forecast model uses an incompatible feature schema.",
            )
        artifact = self.forecast_training_service.load_artifact_bundle(stored_model.artifact_path)
        if artifact.point_model is None:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="The current daily forecast artifact does not include a LightGBM point model.",
                ),
                reason="The current daily forecast artifact does not include a LightGBM point model.",
            )
        dataset_records = self.cleaned_dataset_repository.list_dataset_records(version.source_cleaned_dataset_version_id)
        weather = _merge_weather_rows(
            _fetch_historical_weather(
                self.geomet_client,
                _ensure_utc(version.horizon_start) - timedelta(hours=max(self.settings.forecast_training_lookback_days * 24, 1)),
                _ensure_utc(version.horizon_start),
            ),
            _fetch_forecast_weather(
                self.geomet_client,
                _ensure_utc(version.horizon_start),
                _ensure_utc(version.horizon_end),
            ),
        )
        holidays = self._load_holidays(_ensure_utc(version.horizon_start), _ensure_utc(version.horizon_end))
        prepared = prepare_forecast_features(
            dataset_records=dataset_records,
            horizon_start=_ensure_utc(version.horizon_start),
            horizon_end=_ensure_utc(version.horizon_end),
            weather_rows=weather,
            holidays=holidays,
            max_history_hours=max(self.settings.forecast_training_lookback_days * 24, 1),
        )
        rows = self._resolve_daily_dynamic_rows(prepared, artifact, resolved)
        if not rows:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="Driver attribution could not be rebuilt for this alert bucket.",
                ),
                reason="Driver attribution could not be rebuilt for this alert bucket.",
            )
        drivers = self._top_grouped_drivers(
            rows=rows,
            artifact=artifact,
            group_resolver=self._resolve_daily_feature_group,
        )
        return _ComponentOutcome(status="available", payload=AlertDriversComponentRead(status="available", drivers=drivers))

    def _build_weekly_driver_context(self, resolved: _ResolvedAlertSource) -> _ComponentOutcome:
        version = self.weekly_forecast_repository.get_forecast_version(resolved.forecast_reference_id)
        if version is None:
            return _ComponentOutcome(
                status="failed",
                payload=AlertDriversComponentRead(status="failed", failureReason="Weekly forecast version not found."),
                reason="Weekly forecast version not found.",
            )
        stored_model = self.forecast_model_repository.find_current_model(self.settings.weekly_forecast_product_name)
        if stored_model is None:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="No compatible weekly forecast model is currently available.",
                ),
                reason="No compatible weekly forecast model is currently available.",
            )
        if stored_model.source_cleaned_dataset_version_id != version.source_cleaned_dataset_version_id:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="The current weekly forecast model does not match this alert's forecast lineage.",
                ),
                reason="The current weekly forecast model does not match this alert's forecast lineage.",
            )
        if stored_model.feature_schema_version != WeeklyDemandPipeline.feature_schema_version:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="The weekly forecast model uses an incompatible feature schema.",
                ),
                reason="The weekly forecast model uses an incompatible feature schema.",
            )
        artifact = self.weekly_forecast_training_service.load_artifact_bundle(stored_model.artifact_path)
        if artifact.point_model is None:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="The current weekly forecast artifact does not include a LightGBM point model.",
                ),
                reason="The current weekly forecast artifact does not include a LightGBM point model.",
            )
        dataset_records = self.cleaned_dataset_repository.list_dataset_records(version.source_cleaned_dataset_version_id)
        weather_rows = _fetch_forecast_weather(
            self.geomet_client,
            _ensure_utc(version.week_start_local),
            _ensure_utc(version.week_end_local),
        )
        holidays = self._load_holidays(_ensure_utc(version.week_start_local), _ensure_utc(version.week_end_local))
        prepared = prepare_weekly_forecast_features(
            dataset_records=dataset_records,
            week_start_local=_ensure_utc(version.week_start_local),
            week_end_local=_ensure_utc(version.week_end_local),
            timezone_name=self.settings.weekly_forecast_timezone,
            weather_rows=weather_rows,
            holidays=holidays,
        )
        alert_date = _ensure_utc(resolved.window_start).date()
        rows = [
            row
            for row in prepared["rows"]
            if row["service_category"] == resolved.service_category
            and row["forecast_date_local"] == alert_date
            and (resolved.geography_value is None or row.get("geography_key") == resolved.geography_value)
        ]
        if not rows:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertDriversComponentRead(
                    status="unavailable",
                    unavailableReason="Driver attribution could not be rebuilt for this alert day.",
                ),
                reason="Driver attribution could not be rebuilt for this alert day.",
            )
        drivers = self._top_grouped_drivers(
            rows=rows,
            artifact=artifact,
            group_resolver=self._resolve_weekly_feature_group,
        )
        return _ComponentOutcome(status="available", payload=AlertDriversComponentRead(status="available", drivers=drivers))

    def _resolve_daily_dynamic_rows(
        self,
        prepared: dict[str, object],
        artifact: TrainedHourlyDemandArtifact,
        resolved: _ResolvedAlertSource,
    ) -> list[dict[str, object]]:
        pipeline = HourlyDemandPipeline()
        training_rows = list(prepared.get("training_rows", []))
        scoring_rows = sorted(
            list(prepared.get("rows", [])),
            key=lambda row: (
                row["bucket_start"],
                str(row.get("service_category") or ""),
                "" if row.get("geography_key") is None else str(row.get("geography_key")),
            ),
        )
        history_by_scope = pipeline._history_from_training_rows(training_rows)
        matched_rows: list[dict[str, object]] = []
        target_start = _ensure_utc(resolved.window_start)
        target_end = _ensure_utc(resolved.window_end)
        for row in scoring_rows:
            scope_key = pipeline._scope_key(row)
            history = history_by_scope.setdefault(scope_key, {})
            dynamic_row = dict(row)
            dynamic_row.update(pipeline._compute_dynamic_features(dynamic_row["bucket_start"], history))
            x_score = pd.DataFrame(
                [pipeline._encode_row(dynamic_row, artifact.category_codes, artifact.geography_codes, artifact.feature_names)],
                columns=artifact.feature_names,
                dtype=float,
            )
            point_prediction = float(artifact.point_model.predict(x_score)[0])
            history[dynamic_row["bucket_start"]] = max(point_prediction, 0.0)
            if dynamic_row["service_category"] != resolved.service_category:
                continue
            if _ensure_utc(dynamic_row["bucket_start"]) != target_start or _ensure_utc(dynamic_row["bucket_end"]) != target_end:
                continue
            if resolved.geography_value is not None and dynamic_row.get("geography_key") != resolved.geography_value:
                continue
            matched_rows.append(dynamic_row)
        return matched_rows

    def _top_grouped_drivers(
        self,
        *,
        rows: list[dict[str, object]],
        artifact: TrainedHourlyDemandArtifact | TrainedWeeklyDemandArtifact,
        group_resolver,
    ) -> list[AlertDriverRead]:
        if artifact.point_model is None:
            return []
        x_score = pd.DataFrame(
            [
                HourlyDemandPipeline()._encode_row(row, artifact.category_codes, artifact.geography_codes, artifact.feature_names)
                if isinstance(artifact, TrainedHourlyDemandArtifact)
                else WeeklyDemandPipeline()._encode_row(row, artifact.category_codes, artifact.geography_codes, artifact.feature_names)
                for row in rows
            ],
            columns=artifact.feature_names,
            dtype=float,
        )
        contribution_matrix = artifact.point_model.predict(x_score, pred_contrib=True)
        grouped: dict[str, float] = {}
        for contribution_row in contribution_matrix:
            for feature_name, contribution in zip(artifact.feature_names, contribution_row[:-1]):
                label = group_resolver(feature_name)
                grouped[label] = grouped.get(label, 0.0) + float(contribution)
        ordered = sorted(grouped.items(), key=lambda item: abs(item[1]), reverse=True)[:5]
        return [
            AlertDriverRead(
                label=label,
                contribution=value,
                direction="increase" if value >= 0 else "decrease",
            )
            for label, value in ordered
        ]

    def _build_anomaly_context(self, resolved: _ResolvedAlertSource) -> _ComponentOutcome:
        detected_at_end = _ensure_utc(resolved.alert_triggered_at)
        detected_at_start = detected_at_end - timedelta(days=7)
        bundles = self.surge_evaluation_repository.list_candidate_bundles_for_window(
            service_category=resolved.service_category,
            detected_at_start=detected_at_start,
            detected_at_end=detected_at_end,
        )
        if resolved.alert_source == "surge_alert" and resolved.surge_candidate_id:
            if not any(bundle.candidate.surge_candidate_id == resolved.surge_candidate_id for bundle in bundles):
                selected = self.surge_evaluation_repository.get_candidate_bundle(resolved.surge_candidate_id)
                if selected is not None:
                    bundles.append(selected)
                    bundles.sort(key=lambda item: item.candidate.detected_at)
        if not bundles:
            return _ComponentOutcome(
                status="unavailable",
                payload=AlertAnomaliesComponentRead(
                    status="unavailable",
                    unavailableReason="No surge anomalies were recorded in the previous seven days for this service category.",
                ),
                reason="No surge anomalies were recorded in the previous seven days for this service category.",
            )
        items = [
            AlertAnomalyContextItemRead(
                surgeCandidateId=bundle.candidate.surge_candidate_id,
                surgeNotificationEventId=None if bundle.confirmation is None else bundle.confirmation.surge_notification_event_id,
                evaluationWindowStart=bundle.candidate.evaluation_window_start,
                evaluationWindowEnd=bundle.candidate.evaluation_window_end,
                actualDemandValue=float(bundle.candidate.actual_demand_value),
                forecastP50Value=(
                    None
                    if bundle.candidate.forecast_p50_value is None
                    else float(bundle.candidate.forecast_p50_value)
                ),
                residualZScore=(
                    None if bundle.candidate.residual_z_score is None else float(bundle.candidate.residual_z_score)
                ),
                percentAboveForecast=(
                    None
                    if bundle.candidate.percent_above_forecast is None
                    else float(bundle.candidate.percent_above_forecast)
                ),
                candidateStatus=bundle.candidate.candidate_status,
                confirmationOutcome=None if bundle.confirmation is None else bundle.confirmation.outcome,
                isSelectedAlert=(
                    resolved.alert_source == "surge_alert"
                    and bundle.candidate.surge_candidate_id == resolved.surge_candidate_id
                ),
            )
            for bundle in bundles
        ]
        return _ComponentOutcome(status="available", payload=AlertAnomaliesComponentRead(status="available", items=items))

    def _load_holidays(self, start: datetime, end: datetime) -> list[dict[str, object]]:
        holidays: list[dict[str, object]] = []
        for year in range(start.year, end.year + 1):
            holidays.extend(self.nager_date_client.fetch_holidays(year))
        return holidays

    @staticmethod
    def _resolve_daily_feature_group(feature_name: str) -> str:
        if feature_name == "service_category_code":
            return "Service category"
        if feature_name == "geography_code":
            return "Geography"
        if feature_name == "hour_of_day":
            return "Hour of day"
        if feature_name in {"day_of_week", "day_of_year", "month"}:
            return "Calendar seasonality"
        if feature_name in {"is_weekend", "is_holiday"}:
            return "Holiday / weekend"
        if feature_name.startswith("weather_"):
            return "Weather"
        if feature_name == "historical_mean":
            return "Historical average"
        if feature_name.startswith("lag_"):
            return "Recent demand"
        if feature_name.startswith("rolling_mean_"):
            return "Rolling demand trend"
        return feature_name

    @staticmethod
    def _resolve_weekly_feature_group(feature_name: str) -> str:
        if feature_name == "service_category_code":
            return "Service category"
        if feature_name == "geography_code":
            return "Geography"
        if feature_name in {"day_of_week", "day_of_year", "month"}:
            return "Calendar seasonality"
        if feature_name in {"is_weekend", "is_holiday"}:
            return "Holiday / weekend"
        if "temperature" in feature_name or "precipitation" in feature_name or "snowfall" in feature_name or feature_name == "weather_is_missing":
            return "Weather"
        if feature_name == "historical_mean":
            return "Historical average"
        if feature_name.startswith("lag_"):
            return "Recent demand"
        if feature_name.startswith("rolling_mean_"):
            return "Rolling demand trend"
        return feature_name

    def _log(self, event: str, **fields: object) -> None:
        self.logger.info("%s", summarize_status(event, **fields))
