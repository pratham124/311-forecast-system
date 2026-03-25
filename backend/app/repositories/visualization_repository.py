from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import VisualizationLoadRecord, VisualizationSnapshot


class VisualizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_load_record(
        self,
        *,
        requested_by_actor: str,
        forecast_product_name: str,
        forecast_granularity: str,
        service_category_filter: str | None,
        history_window_start: datetime,
        history_window_end: datetime,
        forecast_window_start: datetime | None,
        forecast_window_end: datetime | None,
        source_cleaned_dataset_version_id: str | None = None,
        source_forecast_version_id: str | None = None,
        source_weekly_forecast_version_id: str | None = None,
    ) -> VisualizationLoadRecord:
        record = VisualizationLoadRecord(
            requested_by_actor=requested_by_actor,
            forecast_product_name=forecast_product_name,
            forecast_granularity=forecast_granularity,
            service_category_filter=service_category_filter,
            history_window_start=history_window_start,
            history_window_end=history_window_end,
            forecast_window_start=forecast_window_start,
            forecast_window_end=forecast_window_end,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            source_forecast_version_id=source_forecast_version_id,
            source_weekly_forecast_version_id=source_weekly_forecast_version_id,
            status="running",
        )
        self.session.add(record)
        self.session.flush()
        return record

    def complete_load(
        self,
        visualization_load_id: str,
        *,
        status: str,
        degradation_type: str | None = None,
        failure_reason: str | None = None,
        fallback_snapshot_id: str | None = None,
        history_window_start: datetime | None = None,
        history_window_end: datetime | None = None,
        forecast_window_start: datetime | None = None,
        forecast_window_end: datetime | None = None,
        source_cleaned_dataset_version_id: str | None = None,
        source_forecast_version_id: str | None = None,
        source_weekly_forecast_version_id: str | None = None,
    ) -> VisualizationLoadRecord:
        record = self.require_load_record(visualization_load_id)
        record.status = status
        record.degradation_type = degradation_type
        record.failure_reason = failure_reason
        record.fallback_snapshot_id = fallback_snapshot_id
        record.completed_at = datetime.utcnow()
        if history_window_start is not None:
            record.history_window_start = history_window_start
        if history_window_end is not None:
            record.history_window_end = history_window_end
        if forecast_window_start is not None:
            record.forecast_window_start = forecast_window_start
        if forecast_window_end is not None:
            record.forecast_window_end = forecast_window_end
        if source_cleaned_dataset_version_id is not None:
            record.source_cleaned_dataset_version_id = source_cleaned_dataset_version_id
        if source_forecast_version_id is not None:
            record.source_forecast_version_id = source_forecast_version_id
        if source_weekly_forecast_version_id is not None:
            record.source_weekly_forecast_version_id = source_weekly_forecast_version_id
        self.session.flush()
        return record

    def report_render_event(
        self,
        visualization_load_id: str,
        *,
        render_status: str,
        failure_reason: str | None,
    ) -> VisualizationLoadRecord:
        record = self.require_load_record(visualization_load_id)
        record.render_reported_at = datetime.utcnow()
        if render_status == "render_failed":
            record.status = "render_failed"
            record.failure_reason = failure_reason
            if record.completed_at is None:
                record.completed_at = datetime.utcnow()
        self.session.flush()
        return record

    def require_load_record(self, visualization_load_id: str) -> VisualizationLoadRecord:
        record = self.session.get(VisualizationLoadRecord, visualization_load_id)
        if record is None:
            raise LookupError("Visualization load not found")
        return record

    def create_snapshot(
        self,
        *,
        forecast_product_name: str,
        forecast_granularity: str,
        service_category_filter: str | None,
        source_cleaned_dataset_version_id: str,
        source_forecast_version_id: str | None,
        source_weekly_forecast_version_id: str | None,
        source_forecast_run_id: str | None,
        source_weekly_forecast_run_id: str | None,
        history_window_start: datetime,
        history_window_end: datetime,
        forecast_window_start: datetime,
        forecast_window_end: datetime,
        payload: dict[str, Any],
        created_from_load_id: str,
        expires_in_hours: int,
    ) -> VisualizationSnapshot:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        snapshot = VisualizationSnapshot(
            forecast_product_name=forecast_product_name,
            forecast_granularity=forecast_granularity,
            service_category_filter=service_category_filter,
            source_cleaned_dataset_version_id=source_cleaned_dataset_version_id,
            source_forecast_version_id=source_forecast_version_id,
            source_weekly_forecast_version_id=source_weekly_forecast_version_id,
            source_forecast_run_id=source_forecast_run_id,
            source_weekly_forecast_run_id=source_weekly_forecast_run_id,
            history_window_start=history_window_start,
            history_window_end=history_window_end,
            forecast_window_start=forecast_window_start,
            forecast_window_end=forecast_window_end,
            payload_json=json.dumps(payload),
            created_at=now,
            expires_at=now + timedelta(hours=expires_in_hours),
            created_from_load_id=created_from_load_id,
        )
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def get_latest_eligible_snapshot(
        self,
        *,
        forecast_product_name: str,
        service_category_filter: str | None,
        now: datetime,
    ) -> VisualizationSnapshot | None:
        statement = (
            select(VisualizationSnapshot)
            .where(VisualizationSnapshot.forecast_product_name == forecast_product_name)
            .where(VisualizationSnapshot.snapshot_status == "stored")
            .order_by(VisualizationSnapshot.created_at.desc())
        )
        snapshots = list(self.session.scalars(statement))
        normalized_now = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        for snapshot in snapshots:
            if snapshot.service_category_filter != service_category_filter:
                continue
            expires_at = snapshot.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < normalized_now:
                snapshot.snapshot_status = "expired"
                continue
            self.session.flush()
            return snapshot
        self.session.flush()
        return None
