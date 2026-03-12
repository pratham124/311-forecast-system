# Data Model: Validate and Deduplicate Ingested Data

## Overview

UC-02 extends the persistent dataset lifecycle introduced by UC-01. The validation and deduplication workflow consumes an ingested dataset already tracked by UC-01, evaluates it through schema validation and duplicate analysis, and either produces a new approved cleaned dataset version or preserves the previously approved dataset. The model below intentionally incorporates the relevant UC-01 entities so the cross-feature lineage remains explicit.

## Reused Entities From Previous Specs

### Entity: IngestionRun

**Purpose**: Represents the UC-01 execution that retrieved the dataset entering UC-02 validation.

**Reuse in UC-02**

- Provides the upstream run lineage for every validation attempt.
- Remains the authoritative source for ingestion trigger, source-window, and source retrieval outcome details.
- Must not be duplicated in UC-02 tables; validation records reference it.

### Entity: DatasetVersion (Ingested)

**Purpose**: Represents the ingested dataset version created by UC-01 before validation and deduplication approval is finalized.

**Reuse in UC-02**

- Serves as the source dataset for each `ValidationRun`.
- Preserves the ingested record count and source lineage.
- Must remain distinct from the cleaned approved dataset version produced by UC-02.

### Entity: CurrentDatasetMarker / Approved Dataset Marker

**Purpose**: Identifies the cleaned dataset version currently active for downstream forecasting and dashboards.

**Reuse in UC-02**

- UC-02 updates this shared marker only after a cleaned dataset version is fully stored and approved.
- The marker remains unchanged for schema failures, review-needed outcomes, deduplication failures, and storage failures.
- This shared marker is the bridge between previous specs and this feature's approval semantics.

## Entity: ValidationRun

**Purpose**: Represents one automated attempt to validate, deduplicate, and decide approval for an ingested dataset.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `validation_run_id` | Identifier | Yes | Unique per validation attempt |
| `ingestion_run_id` | Identifier | Yes | References the upstream `IngestionRun` |
| `source_dataset_version_id` | Identifier | Yes | References the ingested `DatasetVersion` entering validation |
| `started_at` | Timestamp | Yes | Set when validation processing begins |
| `completed_at` | Timestamp | No | Present only after a terminal outcome |
| `status` | Enum | Yes | Requirements-level outcomes `running`, `approved`, `rejected`, `failed`, `review-needed`; storage normalization MAY represent `review-needed` as `review_needed` |
| `failure_stage` | Enum | No | `schema_validation`, `duplicate_analysis`, `storage` |
| `duplicate_threshold_type` | Enum | Yes | `percentage` only |
| `duplicate_percentage` | Decimal | No | Range `0` to `100` when duplicate analysis completes |
| `approved_dataset_version_id` | Identifier | No | Present only when a cleaned dataset version is approved |
| `review_reason` | String | No | Required when `status = review-needed` |

**Validation rules**

- `completed_at` is required for `approved`, `rejected`, `failed`, and `review-needed`.
- `duplicate_threshold_type` must remain `percentage`.
- `approved_dataset_version_id` is valid only when `status = approved`.
- `review_reason` is required only when `status = review-needed`.
- `rejected` is used only for schema-validation failure; `failed` is used only when duplicate analysis, storage, or reliable outcome persistence cannot complete.

**State transitions**

`running` → `approved`  
`running` → `rejected`  
`running` → `failed`  
`running` → `review-needed`

No other transitions are valid.

## Entity: ValidationResult

**Purpose**: Captures the schema-validation outcome for a validation run.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `validation_result_id` | Identifier | Yes | Unique per validation result |
| `validation_run_id` | Identifier | Yes | References the owning `ValidationRun` |
| `status` | Enum | Yes | `passed` or `rejected` |
| `required_field_check` | Enum | Yes | `passed` or `failed` |
| `type_check` | Enum | Yes | `passed` or `failed` |
| `format_check` | Enum | Yes | `passed` or `failed` |
| `completeness_check` | Enum | Yes | `passed` or `failed` |
| `issue_summary` | String | No | Summary of rule failures without raw source rows |
| `recorded_at` | Timestamp | Yes | Set when validation finishes |

**Validation rules**

- `issue_summary` is required when `status = rejected`.
- Validation must complete before duplicate analysis begins.

## Entity: DuplicateAnalysisResult

**Purpose**: Captures the duplicate-analysis metrics and policy outcome for a validation run.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `duplicate_analysis_id` | Identifier | Yes | Unique per duplicate-analysis result |
| `validation_run_id` | Identifier | Yes | References the owning `ValidationRun` |
| `status` | Enum | Yes | Requirements-level outcomes `passed`, `review-needed`, `failed`; storage normalization MAY represent `review-needed` as `review_needed` |
| `total_record_count` | Integer | Yes | Greater than or equal to zero |
| `duplicate_record_count` | Integer | Yes | Greater than or equal to zero |
| `duplicate_percentage` | Decimal | Yes | Derived from duplicate versus total records |
| `threshold_percentage` | Decimal | Yes | Configured review threshold used for this run |
| `duplicate_group_count` | Integer | Yes | Greater than or equal to zero |
| `issue_summary` | String | No | Summary of duplicate-analysis or processing issues |
| `recorded_at` | Timestamp | Yes | Set when duplicate analysis finishes |

**Validation rules**

- `duplicate_percentage` must be calculated from `duplicate_record_count / total_record_count` when `total_record_count > 0`.
- `status = review-needed` requires `duplicate_percentage` to exceed `threshold_percentage`.
- `status = failed` indicates duplicate processing did not complete.

## Entity: DuplicateGroup

**Purpose**: Represents one set of records identified as duplicates and the deterministic outcome required to resolve them.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `duplicate_group_id` | Identifier | Yes | Unique per duplicate group |
| `duplicate_analysis_id` | Identifier | Yes | References the owning `DuplicateAnalysisResult` |
| `group_key` | String | Yes | Stable deduplication key for the duplicate set |
| `source_record_count` | Integer | Yes | Must be 2 or greater |
| `resolution_status` | Enum | Yes | `consolidated`, `kept_single`, `failed` |
| `cleaned_record_id` | Identifier | No | Present when a cleaned output record is produced |
| `resolution_summary` | String | No | Summarizes retained or consolidated values |

**Validation rules**

- Each duplicate group must yield at most one cleaned record.
- `resolution_status = consolidated` is used when non-conflicting values are merged.
- `cleaned_record_id` is required when `resolution_status` is `consolidated` or `kept_single`.

## Entity: CleanedDatasetVersion

**Purpose**: Represents the cleaned dataset produced by UC-02 after validation and duplicate resolution succeed.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `cleaned_dataset_version_id` | Identifier | Yes | Unique per cleaned dataset version |
| `source_dataset_version_id` | Identifier | Yes | References the ingested `DatasetVersion` from UC-01 |
| `validation_run_id` | Identifier | Yes | References the validation run that created it |
| `cleaned_record_count` | Integer | Yes | Greater than or equal to zero |
| `duplicate_group_count` | Integer | Yes | Greater than or equal to zero |
| `storage_status` | Enum | Yes | `pending`, `stored`, `failed` |
| `approval_status` | Enum | Yes | `pending`, `approved`, `blocked` |
| `stored_at` | Timestamp | No | Present when storage succeeds |
| `approved_at` | Timestamp | No | Present only when `approval_status = approved` |

**Validation rules**

- `approval_status = approved` requires `storage_status = stored`.
- A cleaned dataset version must not be approved until validation and duplicate analysis both pass.
- No cleaned dataset version is created for rejected or review-needed outcomes.

**State transitions**

`pending/pending` → `stored/pending`  
`stored/pending` → `stored/approved`  
`pending/pending` → `failed/blocked`

## Entity: ReviewNeededRecord

**Purpose**: Records that a validation run was blocked because duplicate percentage exceeded the accepted threshold.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `review_record_id` | Identifier | Yes | Unique per review-needed record |
| `validation_run_id` | Identifier | Yes | References a `ValidationRun` with `status = review-needed` |
| `duplicate_analysis_id` | Identifier | Yes | References the duplicate-analysis outcome that triggered the hold |
| `reason` | String | Yes | Human-readable summary of why approval was blocked |
| `recorded_at` | Timestamp | Yes | Set when the review-needed outcome is persisted |

**Validation rules**

- A review-needed record can exist only for runs where duplicate analysis completed and exceeded the threshold.
- Review-needed records are informational only and do not grant manual approval or reprocessing actions.
- Review-needed records MUST expose only operationally necessary summary details and never raw source payloads.

## Relationships

- One `IngestionRun` may produce zero or more `ValidationRun` records if revalidation is ever retried, but UC-02 initially expects one primary validation run per ingested dataset.
- One ingested `DatasetVersion` may have zero or one successful `CleanedDatasetVersion` approved from it.
- One `ValidationRun` has exactly one `ValidationResult`.
- One `ValidationRun` may have zero or one `DuplicateAnalysisResult`.
- One `DuplicateAnalysisResult` may own zero or more `DuplicateGroup` records.
- One successful `ValidationRun` produces exactly one `CleanedDatasetVersion`.
- One review-needed `ValidationRun` must have one corresponding `ReviewNeededRecord`.
- One shared approved dataset marker points to exactly one approved `CleanedDatasetVersion` at a time.

## Derived Invariants

- The approved dataset marker remains unchanged until a `CleanedDatasetVersion` is both stored and approved.
- A schema-invalid dataset never has a `DuplicateAnalysisResult`.
- A review-needed outcome never produces an approved cleaned dataset version.
- Every duplicate group contributes at most one cleaned output record.
- Operational queries for the approved dataset must resolve through the shared active marker, not through candidate validation artifacts.
- If reliable outcome persistence or operational exposure fails, the candidate dataset remains not approved and the approved dataset marker remains unchanged.
