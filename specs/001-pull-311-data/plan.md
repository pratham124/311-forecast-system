# Implementation Plan: UC-01 Scheduled 311 Data Pull

**Branch**: `001-pull-311-data` | **Date**: 2026-03-11 | **Spec**: [spec.md](/root/311-forecast-system/specs/001-pull-311-data/spec.md)
**Input**: Feature specification from `/specs/001-pull-311-data/spec.md`

## Summary

Implement the UC-01 backend-only scheduled ingestion flow for the canonical Edmonton 311 source. The implementation must persist and advance the successful-pull cursor only after successful validated storage, handle first-run ingestion when no cursor exists, create new dataset versions only for validated runs with new records, preserve strict candidate/stored/current dataset boundaries so no partial activation is possible, expose the current dataset query surface required by acceptance tests, persist failure notification records for all failed runs, and emit logs that distinguish each failure category and the no-new-records success outcome.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy or SQLModel-compatible PostgreSQL access layer, HTTP client for Socrata ingestion, APScheduler-compatible scheduling, structured logging  
**Storage**: PostgreSQL for ingestion runs, successful-pull cursor state, candidate-to-stored dataset version lifecycle, current dataset marker, failure notification records, and migration-managed schema state  
**Testing**: pytest with unit, integration, contract, and acceptance coverage aligned to `docs/UC-01-AT.md`  
**Target Platform**: Linux server environment running the backend API and scheduler  
**Project Type**: backend web service with scheduled ingestion pipeline  
**Performance Goals**: Complete each scheduled pull in one unattended run, return run status and current-dataset query results immediately after run completion, and leave enough durable evidence for acceptance assertions after success, no-new-records success, and each failure category  
**Constraints**: Use the canonical Edmonton 311 Socrata source, keep business logic out of FastAPI routes, persist the last-successful-pull cursor only after a successful validated store, create no new stored dataset version for no-new-records or failed runs, never partially activate data, and keep the feature limited to backend ingestion and observability without forecasting, dashboard UI, or email delivery work  
**Scale/Scope**: One Edmonton 311 ingestion workflow, one current dataset marker, one cursor stream keyed to the source, versioned dataset storage for successful runs with new records, and acceptance coverage for the eight UC-01 scenarios

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Use-case traceability**: PASS. The plan remains explicitly tied to [`docs/UC-01.md`](/root/311-forecast-system/docs/UC-01.md) and [`docs/UC-01-AT.md`](/root/311-forecast-system/docs/UC-01-AT.md).
- **Canonical data-source usage**: PASS. The plan uses the constitution-required Edmonton Socrata 311 source as the only UC-01 ingestion source.
- **Layered backend architecture**: PASS. The design keeps route handlers thin, places orchestration in pipeline and service modules, keeps source access in a dedicated client, and isolates persistence in repositories.
- **Typed contracts and normalized schemas**: PASS. The plan requires normalized backend schemas for run status, current dataset state, cursor state, and failure-notification responses.
- **Security coverage**: PASS. External-source authentication remains backend-managed and configuration-based, and UC-01 backend trigger/query endpoints are required to use authenticated access with basic role-based authorization.
- **Time-safe forecasting constraints**: PASS. UC-01 remains strictly ingestion and activation work; it does not alter forecasting, training, or dashboard behaviors.
- **Operational safety / last-known-good activation**: PASS. Candidate, stored, and current states are explicitly separated, cursor advancement is delayed until successful validated storage, and failed runs leave the prior current dataset intact.

**Post-Design Check**: PASS. Updated research, data model, contracts, and quickstart artifacts preserve the same seven constitution gates and remain backend-only for UC-01.

## Project Structure

### Documentation (this feature)

```text
specs/001-pull-311-data/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ingestion-api.yaml
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

**Structure Decision**: Keep the constitution-mandated backend/frontend repository shape, but implement UC-01 entirely in `backend/`. The frontend structure remains a repository-level convention only and is not part of this feature because UC-01 explicitly excludes dashboard UI and email work.

## Phase 0 Research Summary

- Confirmed the successful-pull window must use an exclusive cursor captured from the most recent successful validated store, not from failed or no-op runs.
- Confirmed first-run behavior must request the full available source dataset when no successful-pull cursor exists and must establish the first cursor only after a successful validated store.
- Confirmed dataset versioning must create a new stored version only for successful runs with new records; no-new-records and all failed outcomes are versioning no-ops.
- Confirmed the system must distinguish candidate, stored, and current dataset states so AT-07 can assert no partial activation.
- Confirmed UC-01 acceptance support requires a query surface for the current dataset state and a persisted failure-notification record store in addition to logs.
- Confirmed logs must include enough structured fields to separate `new_data`, `no_new_records`, `auth_failure`, `source_unavailable`, `validation_failure`, and `storage_failure`.

## Phase 1 Design Summary

- Add a repository-backed cursor state keyed to the Edmonton 311 source, read before each run and updated only after successful validated storage.
- Model candidate, stored, and current dataset boundaries explicitly in the ingestion orchestration flow and persistence layer.
- Expose backend read surfaces for run status, current dataset state, and failure notification records required by acceptance tests.
- Persist `FailureNotificationRecord` for every failed run with the required minimum fields and align structured logs to the same failure classification vocabulary.

## Implementation Steps

1. **Run bootstrap and cursor lookup**
   - Start an `IngestionRun` record with `running` status, trigger type, source identifier, and the current cursor value if one exists.
   - Read the last-successful-pull cursor from a dedicated repository keyed to the Edmonton 311 source.
   - If no cursor exists, mark the run as a first-run fetch and request the full available source dataset.
   - Ensure the production scheduler invokes this same orchestration path through configured job registration rather than a separate implementation path.

2. **Source request and window handling**
   - Authenticate to the Edmonton 311 source using configured credentials.
   - Build the source request from the exclusive cursor rule: fetch only records newer than the stored cursor on normal runs, or all available records on first run.
   - Classify source outcomes into `new_data`, `no_new_records`, `auth_failure`, or `source_unavailable` before any storage activation logic runs.

3. **No-new-records success path**
   - On a successful source response with no records newer than the stored cursor, mark the run `success` with `result_type = no_new_records`.
   - Do not create a candidate dataset for activation, do not create a stored dataset version, do not update the current dataset marker, and do not advance the cursor.
   - Emit a success log that explicitly identifies the `no_new_records` outcome and the unchanged current dataset version.

4. **Candidate dataset and validation path**
   - Treat retrieved data with records as a candidate dataset only while the run is in validation and pre-storage stages.
   - Validate required structure, required fields, data types, and completeness before any durable activation step.
   - On validation failure, keep the candidate dataset non-current and non-stored, mark the run failed with `result_type = validation_failure`, persist a failure notification, and leave both cursor and current dataset unchanged.

5. **Stored dataset version creation rules**
   - Create a new stored `DatasetVersion` only when the run has new records and validation succeeds.
   - Persist dataset metadata including version identifier, source identifier, record count, validation status, storage status, and current/inactive state.
   - Do not create a stored dataset version for no-new-records, authentication failures, source unavailability, or validation failures.

6. **Activation boundaries and first-run success**
   - Separate candidate, stored, and current states in both service logic and persistence rules.
   - Mark a dataset as current only after durable storage succeeds for that same validated dataset.
   - On the first successful run, create the first stored dataset version, update the current dataset marker, and then persist the first successful-pull cursor.
   - On storage failure after validation, treat the dataset as non-current and not successfully stored, mark the run failed with `result_type = storage_failure`, persist a failure notification, and leave cursor and current dataset unchanged.

7. **Current dataset query surface**
   - Expose a backend read surface that returns at minimum the source identifier, current dataset version identifier, activation timestamp, activating run identifier, and record count.
   - Ensure this surface resolves against the current dataset marker and never returns candidate-only data.
   - Keep this read surface backend-only and acceptance-oriented; no dashboard UI work is included in UC-01.
   - Protect trigger and query surfaces with authenticated backend access and basic role-based authorization.

8. **Failure notification persistence**
   - Persist a `FailureNotificationRecord` for every failed run in a queryable monitoring record store.
   - Include at minimum the failed run identifier or run timestamp, failure reason category, failed status, recorded-at timestamp, and human-readable failure summary.
   - Keep the failure category vocabulary aligned with run result types so AT-08 can assert both the run and its monitoring record.

9. **Logging and observability**
   - Emit structured log fields for run identifier, source identifier, trigger type, result type, failure category when present, cursor used, cursor advanced flag, dataset version identifier when present, record count, and completion status.
   - Log distinct terminal outcomes for `new_data`, `no_new_records`, `auth_failure`, `source_unavailable`, `validation_failure`, and `storage_failure`.
   - Ensure logs for failed runs can be correlated with the persisted failure notification record and the unchanged current dataset.

10. **Schema and deployment bootstrap**
   - Manage database schema creation through migrations for all persisted UC-01 entities before story implementation begins.
   - Include migration coverage for ingestion runs, successful-pull cursor state, candidate datasets, stored dataset versions, current dataset marker, and failure notification records.

11. **Acceptance-aligned verification targets**
   - Verify AT-01 by asserting new stored dataset version creation, current marker update, and success logging.
   - Verify AT-02 through AT-06 by asserting unchanged current dataset, no invalid activation, and correct failure notification plus failure logs.
   - Verify AT-07 by asserting candidate datasets never become current before successful storage.
   - Verify AT-08 by asserting the persisted failure notification record contains the required minimum fields and links back to the failed run.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations or justified exceptions were required for this feature.
