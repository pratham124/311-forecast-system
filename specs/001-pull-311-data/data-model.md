# Data Model: UC-01 Scheduled 311 Data Pull

## Overview

UC-01 requires persistent state for scheduled ingestion attempts, the successful-pull cursor, candidate-versus-stored dataset version boundaries, the active dataset pointer, and monitoring-visible failure records. The model below is intentionally limited to the entities needed to satisfy `docs/UC-01-AT.md`.

## Entity: IngestionRun

**Purpose**: Represents one scheduled or test-triggered execution of the Edmonton 311 ingestion workflow.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `run_id` | Identifier | Yes | Unique per run |
| `trigger_type` | Enum | Yes | `scheduled` or `test_trigger` |
| `started_at` | Timestamp | Yes | Set when orchestration begins |
| `completed_at` | Timestamp | No | Present when run reaches terminal status |
| `status` | Enum | Yes | `running`, `success`, `failed` |
| `result_type` | Enum | No | `new_data`, `no_new_records`, `auth_failure`, `source_unavailable`, `validation_failure`, `storage_failure` |
| `source_window_start` | Timestamp | No | Last successful pull boundary when applicable |
| `cursor_used` | String | No | The exclusive last-successful-pull cursor used for this run |
| `cursor_advanced` | Boolean | Yes | `true` only when a successful validated store advances the cursor |
| `records_received` | Integer | No | Zero or greater |
| `candidate_dataset_id` | Identifier | No | Present only while a candidate dataset exists for the run |
| `dataset_version_id` | Identifier | No | Present only when a stored dataset version exists |
| `failure_reason` | String | No | Short category or detail for failed runs |

**Validation rules**

- `completed_at` is required when `status` is `success` or `failed`.
- `result_type = no_new_records` is only valid when `status = success`.
- `cursor_advanced = true` is only valid when `status = success` and `result_type = new_data`.
- `dataset_version_id` must not point to an active dataset unless validation and storage have both succeeded.

**State transitions**

`running` → `success`  
`running` → `failed`

No other transitions are valid.

## Entity: SuccessfulPullCursor

**Purpose**: Stores the exclusive cursor used to define the next incremental pull window for the Edmonton 311 source.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `source_name` | String | Yes | Unique per source |
| `cursor_value` | String | Yes | Exclusive cursor from the most recent successful validated store |
| `updated_at` | Timestamp | Yes | Set only when the cursor is advanced |
| `updated_by_run_id` | Identifier | Yes | Run that established the current cursor |

**Validation rules**

- Exactly zero or one cursor record exists for the Edmonton 311 source.
- No cursor record on first run is valid and means the next request is a full-source fetch.
- Cursor updates occur only after a successful validated store that produced a new stored dataset version.

## Entity: CandidateDataset

**Purpose**: Represents retrieved data being processed for the current run before durable storage.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `candidate_dataset_id` | Identifier | Yes | Unique per run candidate |
| `ingestion_run_id` | Identifier | Yes | References the owning run |
| `record_count` | Integer | Yes | Zero or greater |
| `validation_status` | Enum | Yes | `pending`, `passed`, `failed` |
| `is_current` | Boolean | Yes | Always `false` |

**Validation rules**

- A candidate dataset is never current.
- A no-new-records run creates no candidate dataset.
- Validation failure leaves the candidate dataset without a stored dataset version.

## Entity: DatasetVersion

**Purpose**: Stores one durably persisted version of the ingested 311 dataset created only after a run with new records passes validation.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `dataset_version_id` | Identifier | Yes | Unique per dataset version |
| `source_name` | String | Yes | Canonical Edmonton 311 source name |
| `ingestion_run_id` | Identifier | Yes | References the creating run |
| `candidate_dataset_id` | Identifier | No | References the candidate dataset that produced this stored version |
| `record_count` | Integer | Yes | Zero or greater |
| `validation_status` | Enum | Yes | `passed` only |
| `storage_status` | Enum | Yes | `stored` only |
| `is_current` | Boolean | Yes | True for at most one dataset version |
| `stored_at` | Timestamp | No | Present when storage completes successfully |
| `activated_at` | Timestamp | No | Present only when `is_current = true` |

**Validation rules**

- `is_current = true` requires `validation_status = passed` and `storage_status = stored`.
- `record_count` must reflect the normalized dataset size for the version.
- No dataset version exists for no-new-records or failed runs.

**State transitions**

`stored/not current` → `stored/current`

## Entity: CurrentDatasetMarker

**Purpose**: Provides a stable query point for the dataset version currently active for downstream consumers and acceptance checks.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `source_name` | String | Yes | Unique per source |
| `dataset_version_id` | Identifier | Yes | References the active dataset version |
| `updated_at` | Timestamp | Yes | Updated only on successful activation |
| `updated_by_run_id` | Identifier | Yes | Run that activated the current dataset |
| `record_count` | Integer | Yes | Record count of the active stored dataset version |

**Validation rules**

- There is exactly one marker for the Edmonton 311 source.
- Marker updates occur only after the new dataset version has passed validation and storage.

## Entity: FailureNotificationRecord

**Purpose**: Stores a monitoring-visible notification for each failed ingestion run.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `notification_id` | Identifier | Yes | Unique per failure notification |
| `run_id` | Identifier | Yes | References a failed `IngestionRun` |
| `failure_category` | Enum | Yes | `auth_failure`, `source_unavailable`, `validation_failure`, `storage_failure` |
| `run_status` | Enum | Yes | `failed` |
| `recorded_at` | Timestamp | Yes | Set when the failed run is recorded |
| `message` | String | Yes | Human-readable failure summary |

**Validation rules**

- A failure notification can exist only for runs with `status = failed`.
- `failure_category` must match the run's terminal failure result.

## Relationships

- One `IngestionRun` may create zero or one `CandidateDataset`.
- One `CandidateDataset` belongs to exactly one `IngestionRun`.
- One `CandidateDataset` may produce zero or one stored `DatasetVersion`.
- One `DatasetVersion` belongs to exactly one `IngestionRun`.
- One `SuccessfulPullCursor` belongs to the Edmonton 311 source and is updated by zero or more successful runs over time.
- One `CurrentDatasetMarker` points to exactly one active `DatasetVersion`.
- One failed `IngestionRun` must have one corresponding `FailureNotificationRecord`.

## Derived Invariants

- At most one `DatasetVersion` is current for the Edmonton 311 source at any time.
- Failed runs never change `CurrentDatasetMarker`.
- Failed runs and no-new-records success runs never advance `SuccessfulPullCursor`.
- A successful `no_new_records` run creates no candidate dataset for activation and no stored dataset version.
- Acceptance assertions can determine the active dataset by querying `CurrentDatasetMarker` directly for source identifier, dataset version identifier, activation timestamp, activating run identifier, and record count.
