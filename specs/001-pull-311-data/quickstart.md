# Quickstart: UC-01 Scheduled 311 Data Pull

## Purpose

Use this guide to implement and verify UC-01 with the minimum backend components required by [`docs/UC-01-AT.md`](/root/311-forecast-system/docs/UC-01-AT.md).

## Implementation Outline

1. Create backend modules for:
   - Edmonton 311 ingestion client
   - Successful-pull cursor repository
   - Dataset validation service
   - Candidate dataset handling service or repository
   - Dataset storage repository
   - Current dataset marker repository
   - Ingestion orchestration service or pipeline
   - Monitoring notification repository or service
   - Thin API routes for test-trigger and observability endpoints
2. Persist the planned entities:
   - `IngestionRun`
   - `SuccessfulPullCursor`
   - `CandidateDataset`
   - `DatasetVersion`
   - `CurrentDatasetMarker`
   - `FailureNotificationRecord`
3. Ensure orchestration follows this order:
   - Start run record
   - Load the last-successful-pull cursor or detect first run
   - Authenticate to Edmonton 311 source
   - Fetch records newer than the exclusive cursor, or full-source data on first run
   - Handle no-new-records as a successful no-change result with no new stored dataset version and no cursor advance
   - Materialize a candidate dataset only when records are returned
   - Validate the candidate dataset
   - Store a new dataset version only after validation succeeds
   - Switch the current dataset marker only after successful storage
   - Advance the successful-pull cursor only after successful validated storage
   - Persist a failure notification on any failed run
   - Emit structured logs for success, no-new-records success, and each failure category
   - Write failure notification for failed runs

## Acceptance Alignment

Map implementation and tests directly to these acceptance scenarios:

- `AT-01`: Successful scheduled trigger creates and activates a new dataset version
- `AT-02`: Authentication failure preserves current dataset
- `AT-03`: Source timeout or unavailability preserves current dataset
- `AT-04`: No new records returns success with no dataset change
- `AT-05`: Validation failure rejects the candidate dataset
- `AT-06`: Storage failure prevents activation
- `AT-07`: No partial activation before validation and storage succeed
- `AT-08`: Failed runs create a monitoring-visible failure notification

## Suggested Test Layers

- Unit tests for cursor advancement rules, validation, activation guards, version-creation rules, and failure classification
- Integration tests for orchestration across cursor, dataset, marker, and notification repositories with the Edmonton client stub
- Contract tests for [ingestion-api.yaml](/root/311-forecast-system/specs/001-pull-311-data/contracts/ingestion-api.yaml)
- Acceptance-style tests that mirror `docs/UC-01-AT.md`

## Exit Conditions

Implementation is ready for task breakdown when:

- Each required module maps to a planned backend layer
- The current dataset query surface returns the required minimum fields
- The successful-pull cursor advances only after successful validated storage
- Failed runs emit both logs and failure notification records
- No code path can activate a dataset before validation and successful storage
