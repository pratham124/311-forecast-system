from __future__ import annotations

import json
from datetime import datetime, timezone
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CleanedCurrentRecord, CurrentDatasetMarker, DatasetRecord, DatasetVersion


def _to_requested_at_string(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _extract_geography_key(record: dict[str, object]) -> str | None:
    for key in ("geography_key", "neighbourhood", "ward", "district"):
        raw_value = record.get(key)
        if isinstance(raw_value, str) and raw_value.strip():
            return raw_value.strip()
    return None


class CleanedDatasetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.logger = logging.getLogger("ingestion.cleaned_dataset_repository")

    def list_current_categories(self, source_name: str) -> list[str]:
        rows = list(
            self.session.scalars(
                select(CleanedCurrentRecord.category)
                .where(
                    CleanedCurrentRecord.source_name == source_name,
                    CleanedCurrentRecord.category.is_not(None),
                    CleanedCurrentRecord.category != "",
                )
                .distinct()
            )
        )
        categories = sorted({value.strip() for value in rows if isinstance(value, str) and value.strip()})
        if categories:
            return categories

        current_dataset = self.get_current_approved_dataset(source_name)
        if current_dataset is None:
            return []

        return sorted(
            {
                str(record.get("category")).strip()
                for record in self.list_dataset_records(current_dataset.dataset_version_id)
                if isinstance(record.get("category"), str) and str(record.get("category")).strip()
            }
        )

    def get_latest_current_requested_at(self, source_name: str) -> datetime | None:
        latest = self.session.scalar(
            select(func.max(CleanedCurrentRecord.requested_at)).where(CleanedCurrentRecord.source_name == source_name)
        )
        if latest:
            return datetime.fromisoformat(str(latest).replace('Z', '+00:00')).astimezone(timezone.utc)

        current_dataset = self.get_current_approved_dataset(source_name)
        if current_dataset is None:
            return None

        latest_requested_at: datetime | None = None
        for record in self.list_dataset_records(current_dataset.dataset_version_id):
            raw_requested_at = str(record.get('requested_at') or '')
            if not raw_requested_at:
                continue
            requested_at = datetime.fromisoformat(raw_requested_at.replace('Z', '+00:00')).astimezone(timezone.utc)
            if latest_requested_at is None or requested_at > latest_requested_at:
                latest_requested_at = requested_at
        return latest_requested_at

    def get_current_approved_dataset(self, source_name: str) -> DatasetVersion | None:
        marker = self.session.get(CurrentDatasetMarker, source_name)
        if marker is None:
            return None
        dataset_version = self.session.get(DatasetVersion, marker.dataset_version_id)
        if dataset_version is None:
            return None
        if dataset_version.dataset_kind != "cleaned" or dataset_version.validation_status != "approved":
            return None
        return dataset_version

    def list_dataset_records(self, dataset_version_id: str) -> list[dict[str, object]]:
        rows = (
            self.session.query(DatasetRecord)
            .filter(DatasetRecord.dataset_version_id == dataset_version_id)
            .order_by(DatasetRecord.requested_at.asc(), DatasetRecord.source_record_id.asc())
            .all()
        )
        normalized: list[dict[str, object]] = []
        for row in rows:
            try:
                payload = json.loads(row.record_payload)
            except json.JSONDecodeError:
                payload = {
                    "service_request_id": row.source_record_id,
                    "requested_at": row.requested_at,
                    "category": row.category,
                }
            normalized.append(payload)
        return normalized

    def upsert_current_cleaned_records(
        self,
        *,
        source_name: str,
        ingestion_run_id: str,
        source_dataset_version_id: str,
        approved_dataset_version_id: str,
        approved_by_validation_run_id: str,
        cleaned_records: list[dict[str, object]],
    ) -> None:
        self.logger.info(
            "cleaned_current_records.upsert.started source_name=%s ingestion_run_id=%s input_record_count=%s",
            source_name,
            ingestion_run_id,
            len(cleaned_records),
        )
        # Last wins: duplicate service_request_id in one batch must not produce two INSERTs
        # (PK is service_request_id; pending adds are not visible to a second pass over the list).
        deduped: dict[str, dict[str, object]] = {}
        for record in cleaned_records:
            sid = str(record.get("service_request_id", "")).strip()
            if sid:
                deduped[sid] = record
        cleaned_records = list(deduped.values())
        self.logger.info(
            "cleaned_current_records.deduped source_name=%s ingestion_run_id=%s deduped_record_count=%s",
            source_name,
            ingestion_run_id,
            len(cleaned_records),
        )

        service_request_ids = [
            str(record.get("service_request_id", "")).strip()
            for record in cleaned_records
            if str(record.get("service_request_id", "")).strip()
        ]
        existing_rows = (
            {
                row.service_request_id: row
                for row in self.session.scalars(
                    select(CleanedCurrentRecord).where(CleanedCurrentRecord.service_request_id.in_(service_request_ids))
                )
            }
            if service_request_ids
            else {}
        )
        self.logger.info(
            "cleaned_current_records.existing_lookup.completed source_name=%s ingestion_run_id=%s existing_row_count=%s",
            source_name,
            ingestion_run_id,
            len(existing_rows),
        )

        now = datetime.utcnow()
        inserted_count = 0
        updated_count = 0
        for record in cleaned_records:
            service_request_id = str(record.get("service_request_id", "")).strip()
            payload = json.dumps(record, sort_keys=True)
            requested_at = str(record.get("requested_at", ""))
            category = str(record.get("category", ""))
            geography_key = _extract_geography_key(record)
            existing = existing_rows.get(service_request_id)
            if existing is None:
                new_row = CleanedCurrentRecord(
                    service_request_id=service_request_id,
                    source_name=source_name,
                    requested_at=requested_at,
                    category=category,
                    geography_key=geography_key,
                    record_payload=payload,
                    first_seen_ingestion_run_id=ingestion_run_id,
                    last_updated_ingestion_run_id=ingestion_run_id,
                    source_dataset_version_id=source_dataset_version_id,
                    approved_by_validation_run_id=approved_by_validation_run_id,
                    last_approved_dataset_version_id=approved_dataset_version_id,
                    created_at=now,
                    updated_at=now,
                )
                self.session.add(new_row)
                existing_rows[service_request_id] = new_row
                inserted_count += 1
                continue
            existing.source_name = source_name
            existing.requested_at = requested_at
            existing.category = category
            existing.geography_key = geography_key
            existing.record_payload = payload
            existing.last_updated_ingestion_run_id = ingestion_run_id
            existing.source_dataset_version_id = source_dataset_version_id
            existing.approved_by_validation_run_id = approved_by_validation_run_id
            existing.last_approved_dataset_version_id = approved_dataset_version_id
            existing.updated_at = now
            updated_count += 1
        self.session.flush()
        self.logger.info(
            "cleaned_current_records.upsert.completed source_name=%s ingestion_run_id=%s inserted_count=%s updated_count=%s",
            source_name,
            ingestion_run_id,
            inserted_count,
            updated_count,
        )

    def count_current_cleaned_records(self, source_name: str) -> int:
        return int(
            self.session.scalar(
                select(func.count()).select_from(CleanedCurrentRecord).where(CleanedCurrentRecord.source_name == source_name)
            )
            or 0
        )

    def list_current_cleaned_records(
        self,
        source_name: str,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, object]]:
        statement = select(CleanedCurrentRecord).where(CleanedCurrentRecord.source_name == source_name)
        if start_time is not None:
            statement = statement.where(CleanedCurrentRecord.requested_at >= _to_requested_at_string(start_time))
        if end_time is not None:
            statement = statement.where(CleanedCurrentRecord.requested_at < _to_requested_at_string(end_time))
        rows = list(
            self.session.scalars(
                statement.order_by(CleanedCurrentRecord.requested_at.asc(), CleanedCurrentRecord.service_request_id.asc())
            )
        )
        if rows:
            normalized: list[dict[str, object]] = []
            for row in rows:
                try:
                    payload = json.loads(row.record_payload)
                except json.JSONDecodeError:
                    payload = {
                        "service_request_id": row.service_request_id,
                        "requested_at": row.requested_at,
                        "category": row.category,
                    }
                    if row.geography_key is not None:
                        payload["geography_key"] = row.geography_key
                normalized.append(payload)
            return normalized

        current_dataset = self.get_current_approved_dataset(source_name)
        if current_dataset is None:
            return []

        start_requested_at = _to_requested_at_string(start_time) if start_time is not None else None
        end_requested_at = _to_requested_at_string(end_time) if end_time is not None else None
        return [
            record
            for record in self.list_dataset_records(current_dataset.dataset_version_id)
            if (start_requested_at is None or str(record.get("requested_at", "")) >= start_requested_at)
            and (end_requested_at is None or str(record.get("requested_at", "")) < end_requested_at)
        ]

    def list_current_cleaned_records_filtered(
        self,
        source_name: str,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        categories: list[str] | None = None,
        geography_keys: list[str] | None = None,
    ) -> list[dict[str, object]]:
        """Like list_current_cleaned_records but with category and geography pushed into SQL."""
        statement = select(CleanedCurrentRecord).where(CleanedCurrentRecord.source_name == source_name)
        if start_time is not None:
            statement = statement.where(CleanedCurrentRecord.requested_at >= _to_requested_at_string(start_time))
        if end_time is not None:
            statement = statement.where(CleanedCurrentRecord.requested_at < _to_requested_at_string(end_time))
        if categories:
            statement = statement.where(CleanedCurrentRecord.category.in_(categories))
        if geography_keys is not None:
            statement = statement.where(CleanedCurrentRecord.geography_key.in_(geography_keys))
        rows = list(
            self.session.scalars(
                statement.order_by(CleanedCurrentRecord.requested_at.asc(), CleanedCurrentRecord.service_request_id.asc())
            )
        )
        if rows:
            normalized: list[dict[str, object]] = []
            for row in rows:
                try:
                    payload = json.loads(row.record_payload)
                except json.JSONDecodeError:
                    payload = {
                        "service_request_id": row.service_request_id,
                        "requested_at": row.requested_at,
                        "category": row.category,
                    }
                    if row.geography_key is not None:
                        payload["geography_key"] = row.geography_key
                normalized.append(payload)
            return normalized

        # Fallback to dataset_records table (same as list_current_cleaned_records)
        current_dataset = self.get_current_approved_dataset(source_name)
        if current_dataset is None:
            return []

        start_requested_at = _to_requested_at_string(start_time) if start_time is not None else None
        end_requested_at = _to_requested_at_string(end_time) if end_time is not None else None
        category_set = set(categories) if categories else None
        geography_set = set(geography_keys) if geography_keys is not None else None
        return [
            record
            for record in self.list_dataset_records(current_dataset.dataset_version_id)
            if (start_requested_at is None or str(record.get("requested_at", "")) >= start_requested_at)
            and (end_requested_at is None or str(record.get("requested_at", "")) < end_requested_at)
            and (category_set is None or str(record.get("category", "")).strip() in category_set)
            and (geography_set is None or str(record.get("geography_key", "") or "").strip() in geography_set)
        ]

