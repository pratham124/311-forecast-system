# Quickstart: Validate and Deduplicate Ingested Data

## Purpose

Use this guide to implement and verify UC-02 with the minimum backend components required by [`docs/UC-02-AT.md`](/root/311-forecast-system/docs/UC-02-AT.md), while reusing the UC-01 ingestion lineage already defined in [data-model.md](/root/311-forecast-system/specs/001-pull-311-data/data-model.md).

## Implementation Outline

1. Reuse and extend backend modules for:
   - Ingested dataset lookup from the UC-01 pipeline
   - Validation-run repository
   - Schema validation service
   - Duplicate analysis and grouping service
   - Duplicate resolution service
   - Cleaned dataset storage repository
   - Approved dataset marker repository
   - Review-needed record repository
   - Thin API routes for validation status and approval visibility endpoints
2. Preserve the shared lineage entities from UC-01:
   - `IngestionRun`
   - `DatasetVersion` for ingested source datasets
   - `CurrentDatasetMarker` or equivalent approved dataset marker
3. Persist the new UC-02 entities:
   - `ValidationRun`
   - `ValidationResult`
   - `DuplicateAnalysisResult`
   - `DuplicateGroup`
   - `CleanedDatasetVersion` via `dataset_versions` rows with `dataset_kind = cleaned`
   - `ReviewNeededRecord`
4. Ensure orchestration follows this order:
   - Load the ingested dataset from the UC-01 lineage
   - Start a validation run
   - Execute schema validation
   - Stop immediately on schema rejection
   - Run duplicate analysis only after schema success
   - Compute duplicate percentage and compare with threshold
   - Stop with `review-needed` when the threshold is exceeded
   - Produce one cleaned record per duplicate group with non-conflicting consolidation when allowed
   - Store the cleaned dataset version
   - Update the approval marker so it points to the cleaned dataset version only after storage succeeds
   - Expose operational status surfaces that distinguish the active approved dataset from in-progress, blocked, rejected, failed, or review-needed candidates
   - Emit structured logs and queryable status artifacts using operational summaries rather than raw source payloads
   - If reliable outcome storage or exposure fails, leave the candidate dataset not approved and keep the previously approved dataset active

## Acceptance Alignment

Map implementation and tests directly to these acceptance scenarios:

- `AT-01`: Valid dataset passes validation and deduplication, then becomes approved
- `AT-02`: Schema validation failure rejects the dataset and preserves the prior approved dataset
- `AT-03`: Deduplication process failure prevents approval and preserves the prior approved dataset
- `AT-04`: Excessive duplicate percentage triggers review-needed and blocks approval
- `AT-05`: Storage failure prevents approval even after validation and duplicate analysis succeed
- `AT-06`: No partial activation occurs before the full pipeline succeeds
- `AT-07`: Duplicate resolution consistently produces one cleaned record per duplicate group according to policy

## Suggested Test Layers

- Unit tests for schema rule evaluation, duplicate percentage calculation, duplicate grouping, consolidation rules, and approval guards
- Integration tests across validation runs, ingested dataset lookup, cleaned dataset storage, approved marker updates, and review-needed persistence
- Contract tests for [validation-api.yaml](/root/311-forecast-system/specs/002-validate-deduplicate-data/contracts/validation-api.yaml)
- Acceptance-style tests that mirror `docs/UC-02-AT.md`

## Verification

Run the backend regression subset that covers the new UC-02 implementation and the shared UC-01 ingestion paths:

```bash
cd backend
.venv/bin/python -m pytest \
  tests/contract/test_ingestion_api.py \
  tests/contract/test_validation_run_status.py \
  tests/contract/test_approved_dataset_status.py \
  tests/contract/test_validation_status_errors.py \
  tests/contract/test_review_needed_status.py \
  tests/integration/test_ingestion_success.py \
  tests/integration/test_no_partial_activation.py \
  tests/integration/test_ingestion_no_new_records.py \
  tests/integration/test_ingestion_source_failures.py \
  tests/integration/test_ingestion_processing_failures.py \
  tests/integration/test_validation_approval_flow.py \
  tests/integration/test_validation_completion_timing.py \
  tests/integration/test_schema_rejection_flow.py \
  tests/integration/test_review_needed_flow.py \
  tests/integration/test_operational_status_visibility.py \
  tests/unit/test_query_and_scheduler_edges.py \
  tests/unit/test_activation_rules.py \
  tests/unit/test_repository_edges.py \
  tests/unit/test_duplicate_resolution_service.py \
  tests/unit/test_schema_validation_outcomes.py \
  tests/unit/test_approval_marker_invariants.py
```

Expected result: all tests pass and the current dataset marker changes only for the approved cleaned dataset path.

## Exit Conditions

Implementation is ready for task breakdown when:

- The UC-01 lineage entities and the UC-02 validation entities are clearly linked
- The duplicate threshold is implemented as a percentage-based rule
- Review-needed outcomes are persisted and queryable without manual approval actions
- The approval marker changes only after cleaned dataset storage succeeds and points to the cleaned dataset version
- Operational status surfaces distinguish active approved data from in-progress, blocked, rejected, failed, or review-needed candidates
- No code path can expose candidate or partially processed data as approved, including degraded cases where reliable outcome storage or exposure fails
