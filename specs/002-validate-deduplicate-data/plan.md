# Implementation Plan: Validate and Deduplicate Ingested Data

**Branch**: `002-validate-deduplicate-data` | **Date**: 2026-03-12 | **Spec**: [spec.md](/root/311-forecast-system/specs/002-validate-deduplicate-data/spec.md)
**Input**: Feature specification from `/specs/002-validate-deduplicate-data/spec.md`

## Summary

Implement the UC-02 backend validation and deduplication stage that operates on datasets produced by the UC-01 lifecycle. The implementation must validate each newly ingested dataset against required fields, data types, formats, and structural-completeness rules, reject schema-invalid datasets, resolve duplicates into one cleaned record per duplicate group when the duplicate percentage remains within threshold, block approval with a review-needed outcome when the duplicate percentage exceeds threshold, and preserve the previously approved cleaned dataset whenever processing or outcome exposure is incomplete or unreliable. The design must keep the approval marker pointed at the cleaned dataset version only after validation, deduplication, and storage succeed, while exposing backend operational status surfaces that let authorized users distinguish the active approved dataset from candidate datasets that are in progress, rejected, failed, or review-needed.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy or SQLModel-compatible PostgreSQL access layer, HTTP client for Socrata ingestion, APScheduler-compatible scheduling, JWT authentication support, role-based authorization dependencies, structured logging  
**Storage**: PostgreSQL for UC-01 ingestion state plus validation runs, validation outcomes, duplicate-analysis outcomes, cleaned dataset versions, operational status records, and the approval marker that points to the active cleaned dataset version  
**Testing**: pytest with unit, integration, contract, and acceptance coverage aligned to `docs/UC-02-AT.md`  
**Target Platform**: Linux server environment running the backend API and processing pipeline  
**Project Type**: backend web service with a staged ingestion-and-validation pipeline  
**Performance Goals**: Complete validation and duplicate processing for a newly ingested dataset within 15 minutes of ingestion completion, provide operational status query results within 2 minutes of operator checks, and preserve durable approval and outcome state for all UC-02 acceptance assertions  
**Constraints**: Reuse the canonical Edmonton 311 dataset lineage established by UC-01, keep business logic out of FastAPI routes, reject schema-invalid datasets rather than marking them failed, use `approved`, `rejected`, `failed`, and `review-needed` as the requirements-level outcome vocabulary with any storage or API normalization documented explicitly, treat duplicate review thresholds as percentage-based, limit exposed status details to operationally necessary summaries, counts, identifiers, and timestamps rather than raw source payloads, define unauthorized or forbidden, missing-resource, and invalid-query outcomes for operational status surfaces, preserve the previously approved cleaned dataset whenever processing or outcome storage/exposure is incomplete, and do not add manual review, manual approval, or reprocessing workflows  
**Scale/Scope**: One validation workflow for each newly ingested dataset version, one approval marker for the active cleaned dataset version, one duplicate-threshold configuration per source workflow, operational status visibility for Operational Managers and City Planners, and acceptance coverage for all UC-02 success and failure paths

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Use-case traceability**: PASS. The plan remains tied to [`docs/UC-02.md`](/root/311-forecast-system/docs/UC-02.md) and [`docs/UC-02-AT.md`](/root/311-forecast-system/docs/UC-02-AT.md) and keeps UC-02 aligned with UC-01 lineage rather than adding a new workflow.
- **Canonical data-source usage**: PASS. UC-02 continues to validate and deduplicate datasets originating from the constitution-required Edmonton 311 source already ingested through UC-01.
- **Layered backend architecture**: PASS. Validation orchestration remains in pipeline and service layers, persistence stays in repositories, and operational status surfaces remain thin backend routes.
- **Typed contracts and normalized schemas**: PASS. The plan defines explicit normalization between requirements-level status terms and storage/API field values while preserving stable backend contracts for validation status and approved dataset visibility.
- **Security coverage**: PASS. Operational status surfaces remain backend-enforced with JWT-authenticated role checks, explicit authorization failures, and minimized exposed status details.
- **Time-safe forecasting constraints**: PASS. This feature continues to improve dataset quality gates only and does not alter forecasting, model, or evaluation behavior.
- **Operational safety / last-known-good activation**: PASS. Schema rejection, review-needed outcomes, processing failures, and unreliable outcome persistence all preserve the previously approved cleaned dataset and prevent uncertain activation.

**Post-Design Check**: PASS. Updated research, data model, contracts, and quickstart preserve the same seven constitution gates, keep UC-02 backend-only, and synchronize status semantics, approval-marker behavior, and safe operational visibility with the current spec.

## Project Structure

### Documentation (this feature)

```text
specs/002-validate-deduplicate-data/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── validation-api.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── clients/
│   ├── core/
│   ├── models/
│   ├── pipelines/
│   │   └── ingestion/
│   ├── repositories/
│   ├── schemas/
│   └── services/
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

frontend/
└── src/
    ├── api/
    ├── features/
    ├── hooks/
    ├── pages/
    ├── types/
    └── utils/
```

**Structure Decision**: Keep the constitution-mandated backend/frontend repository shape, but implement UC-02 entirely in `backend/`. The frontend structure remains a repository-level convention only and is not part of this feature because UC-02 concerns backend data-quality processing and operational status visibility, not dashboard UI work.

## Phase 0 Research Summary

- Confirmed UC-02 extends the UC-01 lifecycle and that the approval marker must point to the cleaned dataset version, not the ingested dataset version, after validation, deduplication, and storage succeed.
- Confirmed schema validation failure maps to the requirements-level outcome `rejected`, while `failed` is reserved for processing or storage that cannot complete after processing starts.
- Confirmed the requirements-level outcome vocabulary is `approved`, `rejected`, `failed`, and `review-needed`; storage and contract representations may normalize `review-needed` to `review_needed` if documented explicitly.
- Confirmed operational users must be able to distinguish the currently approved cleaned dataset from candidate datasets that are in progress, rejected, failed, or review-needed.
- Confirmed operational status surfaces must define unauthorized or forbidden, missing-resource, and invalid-query behavior in addition to successful reads.
- Confirmed exposed status details must remain limited to operationally necessary summaries and identifiers rather than raw source payloads.
- Confirmed that if outcome details cannot be stored or exposed reliably, the candidate dataset must remain not approved and the previously approved cleaned dataset must remain active.

## Phase 1 Design Summary

- Reuse UC-01 lineage entities and model UC-02 as a validation stage that can produce a cleaned dataset version and advance the shared approval marker only on full success.
- Represent outcome state consistently across prose, persistence, and contracts by documenting the mapping between requirements-level `review-needed` and storage/API enum normalization where needed.
- Treat schema-invalid datasets as `rejected` terminal outcomes and reserve `failed` for duplicate-analysis or storage execution failures.
- Expose operational status surfaces that can distinguish active approved datasets from candidate datasets that are running, rejected, failed, or review-needed, while returning explicit auth and query-error outcomes.
- Keep operational visibility limited to statuses, identifiers, timestamps, counts, and summary reasons and never expose raw source payloads.
- Preserve last-known-good safety when outcome persistence or exposure fails by withholding approval and leaving the existing approved cleaned dataset unchanged.

## Implementation Steps

1. **Load the ingested dataset context from UC-01 artifacts**
   - Read the newly ingested dataset version or candidate dataset produced by the UC-01 workflow.
   - Link validation processing to the originating ingestion run and dataset version so the full lineage remains queryable.
   - Reuse the shared approval marker and ensure it ultimately points to the cleaned dataset version after successful UC-02 completion.

2. **Start and persist a validation run**
   - Create a `ValidationRun` record with `running` status, source dataset references, started timestamp, and stage markers.
   - Persist enough state to distinguish `approved`, `rejected`, `failed`, and `review-needed` requirements-level outcomes.
   - Document any enum normalization used in storage or API contracts explicitly so it remains aligned with the spec vocabulary.

3. **Execute schema validation before duplicate handling**
   - Validate required fields, required formats, required data types, and structural completeness against the configured rules.
   - On schema failure, mark the run outcome as `rejected`, record the validation result details, block approval, and keep the previously approved cleaned dataset unchanged.
   - Ensure duplicate analysis does not execute for rejected datasets.

4. **Run duplicate analysis and threshold handling**
   - Identify duplicate groups using the configured duplicate-identification rules for the dataset.
   - Compute duplicate percentage over total records and compare it with the configured threshold.
   - If the percentage exceeds the threshold, mark the outcome as `review-needed`, record the duplicate-rate outcome, block approval, and keep the current approved cleaned dataset unchanged.

5. **Produce cleaned records for resolvable duplicate groups**
   - For duplicate groups within the accepted threshold, produce one cleaned record per group.
   - Consolidate non-conflicting values into the cleaned record when allowed by policy.
   - Keep a deterministic record of how each duplicate group was resolved so acceptance tests can verify policy application.

6. **Persist the cleaned dataset version**
   - Create a new cleaned dataset version only when schema validation passes, duplicate percentage remains within threshold, duplicate resolution completes, and storage succeeds.
   - Record cleaned record count, duplicate counts, storage state, approval eligibility, and source lineage back to the ingested dataset.
   - Ensure the approval marker points to this cleaned dataset version only after storage and approval both succeed.

7. **Preserve last-known-good approval safety**
   - Leave the previously approved cleaned dataset active for `rejected`, `review-needed`, and `failed` outcomes.
   - If processing outcome details cannot be stored or exposed reliably, keep the candidate dataset not approved, do not advance the approval marker, and avoid presenting uncertain status as approved state.
   - Ensure no candidate or partially processed dataset is visible as approved during any intermediate or degraded state.

8. **Expose operational query surfaces**
   - Provide backend read surfaces for validation-run status, candidate-dataset outcome visibility, and the current approved dataset marker.
   - Ensure authorized operational users can distinguish the active approved cleaned dataset from candidates that are in progress, blocked, rejected, failed, or review-needed.
   - Define unauthorized or forbidden, missing-resource, and invalid-query outcomes for these operational status surfaces.

9. **Logging and data-exposure safeguards**
   - Emit structured logs for schema rejection, duplicate analysis metrics, review-needed holds, deduplication failures, storage failures, and successful approval.
   - Keep logs and exposed status details limited to operationally necessary summaries, counts, identifiers, timestamps, and rule outcomes rather than raw source payloads or secrets.
   - Correlate validation-run outcomes with the originating ingestion run and dataset lineage for diagnosis.

10. **Schema and migration bootstrap**
   - Add migration-managed schema changes for validation runs, validation results, duplicate groups or duplicate summaries, cleaned dataset version metadata, approval-marker linkage, and operational status records needed for review-needed outcomes.
   - Reuse existing UC-01 tables where the lifecycle is shared and add foreign keys instead of duplicating ingestion entities.

11. **Acceptance-aligned verification targets**
   - Verify AT-01 by asserting schema validation success, duplicate resolution, cleaned dataset storage, and approval marker change to the cleaned dataset version.
   - Verify AT-02 by asserting schema failure produces a rejected outcome, blocks duplicate analysis, and preserves the prior approved dataset.
   - Verify AT-03 and AT-05 by asserting deduplication or storage failure produces a failed outcome, blocks approval, and preserves the prior approved dataset.
   - Verify AT-04 by asserting percentage-based duplicate review holds produce a review-needed outcome, block approval, and keep the prior approved dataset active.
   - Verify AT-06 by asserting candidate datasets never become approved before the full pipeline and reliable outcome persistence succeed.
   - Verify AT-07 by asserting one cleaned record exists per duplicate group and reflects the configured consolidation policy.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations or justified exceptions were required for this feature.
