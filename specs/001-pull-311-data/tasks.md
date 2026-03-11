# Tasks: UC-01 Scheduled 311 Data Pull

**Input**: Design documents from `/specs/001-pull-311-data/`
**Prerequisites**: [plan.md](/root/311-forecast-system/specs/001-pull-311-data/plan.md), [spec.md](/root/311-forecast-system/specs/001-pull-311-data/spec.md), [research.md](/root/311-forecast-system/specs/001-pull-311-data/research.md), [data-model.md](/root/311-forecast-system/specs/001-pull-311-data/data-model.md), [contracts/ingestion-api.yaml](/root/311-forecast-system/specs/001-pull-311-data/contracts/ingestion-api.yaml)

**Tests**: Include unit, integration, contract, and acceptance-aligned tests because the plan explicitly calls for pytest coverage aligned to `docs/UC-01-AT.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Path Conventions

- Backend application code lives in `backend/app/`
- Backend tests live in `backend/tests/`
- This feature is backend-only for UC-01

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the backend project skeleton and shared tooling needed for all UC-01 work.

- [ ] T001 Create backend package structure in `backend/app/__init__.py`, `backend/app/api/routes/__init__.py`, `backend/app/clients/__init__.py`, `backend/app/core/__init__.py`, `backend/app/pipelines/ingestion/__init__.py`, `backend/app/repositories/__init__.py`, `backend/app/schemas/__init__.py`, `backend/app/services/__init__.py`, and `backend/tests/__init__.py`
- [ ] T002 Initialize backend project configuration and dependencies in `backend/pyproject.toml`
- [ ] T003 [P] Configure pytest discovery and test markers in `backend/pytest.ini`
- [ ] T004 [P] Add backend environment configuration template for Edmonton source credentials and storage settings in `backend/.env.example`
- [ ] T005 Configure migration tooling and migration environment in `backend/alembic.ini` and `backend/migrations/env.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build core infrastructure that blocks all user story implementation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create shared configuration and settings loader in `backend/app/core/config.py`
- [ ] T007 [P] Create structured logging setup for run/result classification in `backend/app/core/logging.py`
- [ ] T008 [P] Create database session and base metadata modules in `backend/app/core/db.py`
- [ ] T009 Create shared SQLAlchemy models for `IngestionRun`, `SuccessfulPullCursor`, `CandidateDataset`, `DatasetVersion`, `CurrentDatasetMarker`, and `FailureNotificationRecord` in `backend/app/repositories/models.py`
- [ ] T010 [P] Create shared Pydantic schemas for run status, current dataset, and failure notifications in `backend/app/schemas/ingestion.py`
- [ ] T011 [P] Create repository interfaces for cursor, datasets, current marker, runs, and notifications in `backend/app/repositories/ingestion_repository.py`
- [ ] T012 Create initial migration for all UC-01 persisted entities in `backend/migrations/versions/001_uc01_ingestion_foundation.py`
- [ ] T013 [P] Implement backend auth dependencies and role checks for ingestion endpoints in `backend/app/core/auth.py`
- [ ] T014 [P] Create scheduler service and configured job registration skeleton in `backend/app/services/scheduler_service.py`
- [ ] T015 Create Edmonton 311 client skeleton and normalized source payload schema in `backend/app/clients/edmonton_311.py`
- [ ] T016 Create ingestion route registration and app wiring skeleton in `backend/app/api/routes/ingestion.py` and `backend/app/main.py`

**Checkpoint**: Foundation ready; user stories can now be implemented independently.

---

## Phase 3: User Story 1 - Refresh Current 311 Dataset (Priority: P1) 🎯 MVP

**Goal**: Deliver the successful scheduled ingestion flow that handles first-run logic, uses the exclusive successful-pull cursor, creates a new stored dataset version only for new validated data, activates it as current, and exposes run/current-dataset observability.

**Independent Test**: Trigger the ingestion flow with valid credentials and new records, then verify a new stored dataset version exists, the current dataset query returns the new version details, and the cursor advances only after the successful validated store.

### Tests for User Story 1

- [ ] T017 [P] [US1] Add unit tests for first-run cursor lookup and cursor advancement rules in `backend/tests/unit/test_cursor_service.py`
- [ ] T018 [P] [US1] Add unit tests for candidate-to-stored-to-current activation boundaries in `backend/tests/unit/test_activation_rules.py`
- [ ] T019 [P] [US1] Add contract tests for trigger, run status, current dataset endpoints, and authorized access in `backend/tests/contract/test_ingestion_api.py`
- [ ] T020 [P] [US1] Add integration test for successful scheduled ingestion with new records in `backend/tests/integration/test_ingestion_success.py`

### Implementation for User Story 1

- [ ] T021 [P] [US1] Implement cursor repository operations in `backend/app/repositories/cursor_repository.py`
- [ ] T022 [P] [US1] Implement dataset version and current marker repository operations in `backend/app/repositories/dataset_repository.py`
- [ ] T023 [P] [US1] Implement run repository operations for successful ingestion state in `backend/app/repositories/run_repository.py`
- [ ] T024 [P] [US1] Implement candidate dataset service and validation handoff logic in `backend/app/services/candidate_dataset_service.py`
- [ ] T025 [US1] Implement dataset validation service for required structure and completeness checks in `backend/app/services/dataset_validation_service.py`
- [ ] T026 [US1] Implement successful ingestion orchestration, including first-run full fetch, exclusive cursor windowing, stored dataset version creation, current marker activation, post-store cursor advancement, and scheduler entrypoint reuse in `backend/app/pipelines/ingestion/run_ingestion.py`
- [ ] T027 [US1] Implement run status and current dataset query services in `backend/app/services/ingestion_query_service.py`
- [ ] T028 [US1] Implement FastAPI trigger, run status, and current dataset endpoints with auth guards in `backend/app/api/routes/ingestion.py`
- [ ] T029 [US1] Wire configured scheduled execution to the ingestion pipeline in `backend/app/services/scheduler_service.py`
- [ ] T030 [US1] Add structured success and `new_data` logging fields in `backend/app/services/ingestion_logging_service.py`

**Checkpoint**: User Story 1 should support AT-01 and the first-run behavior in isolation.

---

## Phase 4: User Story 2 - Protect Last Known Good Dataset on Failures (Priority: P2)

**Goal**: Ensure authentication, source availability, validation, and storage failures preserve the prior current dataset, never partially activate candidate data, and persist failure notifications plus diagnosable logs.

**Independent Test**: Trigger auth failure, timeout/unavailable, validation failure, and storage failure runs against an existing current dataset and verify the current dataset remains unchanged, no candidate/stored dataset is activated incorrectly, and a matching failure notification record exists.

### Tests for User Story 2

- [ ] T031 [P] [US2] Add unit tests for failure classification and notification payload creation in `backend/tests/unit/test_failure_notifications.py`
- [ ] T032 [P] [US2] Add integration tests for authentication and source-unavailable failures in `backend/tests/integration/test_ingestion_source_failures.py`
- [ ] T033 [P] [US2] Add integration tests for validation and storage failures in `backend/tests/integration/test_ingestion_processing_failures.py`
- [ ] T034 [P] [US2] Add acceptance-aligned integration test for no partial activation on failed runs in `backend/tests/integration/test_no_partial_activation.py`

### Implementation for User Story 2

- [ ] T035 [P] [US2] Implement failure notification repository operations in `backend/app/repositories/failure_notification_repository.py`
- [ ] T036 [P] [US2] Implement failure notification schema mapping and serialization in `backend/app/schemas/failure_notifications.py`
- [ ] T037 [US2] Implement failure notification service with required minimum fields and monitoring-store persistence in `backend/app/services/failure_notification_service.py`
- [ ] T038 [US2] Extend the ingestion pipeline to classify `auth_failure`, `source_unavailable`, `validation_failure`, and `storage_failure` and preserve the previous current dataset in `backend/app/pipelines/ingestion/run_ingestion.py`
- [ ] T039 [US2] Add storage-boundary enforcement so candidate datasets never become stored/current on failed runs in `backend/app/services/activation_guard_service.py`
- [ ] T040 [US2] Implement failure-notification query endpoint with auth guards in `backend/app/api/routes/ingestion.py`
- [ ] T041 [US2] Add structured failure logging fields and correlation with failure notification records in `backend/app/services/ingestion_logging_service.py` (depends on T030)

**Checkpoint**: User Story 2 should support AT-02, AT-03, AT-05, AT-06, AT-07, and AT-08 independently once foundational and US1 work are present.

---

## Phase 5: User Story 3 - Treat No Updates as a Successful No-Change Run (Priority: P3)

**Goal**: Support the no-new-records success path as a no-op run that records success, creates no candidate/stored dataset version, leaves the current dataset unchanged, and leaves the successful-pull cursor unchanged.

**Independent Test**: Trigger ingestion when the source returns no records newer than the stored cursor and verify the run succeeds with `no_new_records`, no new stored dataset version exists, the current dataset query returns the prior active dataset, and logs distinguish the no-op success.

### Tests for User Story 3

- [ ] T042 [P] [US3] Add unit tests for no-new-records no-op rules in `backend/tests/unit/test_no_new_records_rules.py`
- [ ] T043 [P] [US3] Add integration test for the no-new-records success path in `backend/tests/integration/test_ingestion_no_new_records.py`
- [ ] T044 [P] [US3] Extend contract tests for `no_new_records` run status fields in `backend/tests/contract/test_ingestion_api.py`

### Implementation for User Story 3

- [ ] T045 [US3] Extend the Edmonton 311 client result mapping to classify empty incremental responses as `no_new_records` in `backend/app/clients/edmonton_311.py`
- [ ] T046 [US3] Extend ingestion orchestration so `no_new_records` creates no candidate dataset, no stored dataset version, and no cursor advancement in `backend/app/pipelines/ingestion/run_ingestion.py` (depends on T026)
- [ ] T047 [US3] Extend run status and current dataset query responses to expose unchanged-state success cleanly in `backend/app/services/ingestion_query_service.py`
- [ ] T048 [US3] Add structured `no_new_records` success logging in `backend/app/services/ingestion_logging_service.py`

**Checkpoint**: User Story 3 should support AT-04 independently once foundational and shared orchestration work are present.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, documentation, and end-to-end acceptance alignment across all user stories.

- [ ] T049 Validate quickstart steps and update any mismatches in `specs/001-pull-311-data/quickstart.md`
- [ ] T050 [P] Add end-to-end acceptance matrix coverage notes in `backend/tests/integration/README.md`
- [ ] T051 Run full pytest coverage selection and document the command set in `specs/001-pull-311-data/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story phases (Phase 3 onward)**: Depend on Foundational completion.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational; no dependency on other stories and is the MVP.
- **User Story 2 (P2)**: Starts after Foundational; it extends the shared ingestion pipeline and can be implemented independently of US3.
- **User Story 3 (P3)**: Starts after Foundational; it extends the shared ingestion pipeline and can be implemented independently of US2.

### Within Each User Story

- Tests should be written first and fail before implementation.
- Repository and schema work precede orchestration changes.
- Orchestration changes precede route and observability refinements.
- Logging and query-surface tasks finish each story so it is independently testable.

## Parallel Opportunities

- Setup tasks `T003` and `T004` can run in parallel after `T002`.
- Foundational tasks `T007`, `T008`, `T010`, `T011`, `T013`, and `T014` can run in parallel once `T006` is in place.
- For **US1**, tests `T017`-`T020` can run in parallel, repository tasks `T021`-`T024` can run in parallel, and scheduler wiring `T029` can proceed once orchestration wiring is stable.
- For **US2**, tests `T031`-`T034` can run in parallel, and repository/schema tasks `T035`-`T036` can run in parallel before service and pipeline updates.
- For **US3**, tests `T042`-`T044` can run in parallel, followed by implementation tasks `T045` and `T048` in parallel before final orchestration/query updates.

## Parallel Example: User Story 1

```bash
# Run US1 test authoring in parallel
Task: "Add unit tests for first-run cursor lookup and cursor advancement rules in backend/tests/unit/test_cursor_service.py"
Task: "Add unit tests for candidate-to-stored-to-current activation boundaries in backend/tests/unit/test_activation_rules.py"
Task: "Add contract tests for trigger, run status, current dataset endpoints, and authorized access in backend/tests/contract/test_ingestion_api.py"
Task: "Add integration test for successful scheduled ingestion with new records in backend/tests/integration/test_ingestion_success.py"

# Run US1 repository work in parallel
Task: "Implement cursor repository operations in backend/app/repositories/cursor_repository.py"
Task: "Implement dataset version and current marker repository operations in backend/app/repositories/dataset_repository.py"
Task: "Implement run repository operations for successful ingestion state in backend/app/repositories/run_repository.py"
```

## Parallel Example: User Story 2

```bash
# Run US2 test authoring in parallel
Task: "Add unit tests for failure classification and notification payload creation in backend/tests/unit/test_failure_notifications.py"
Task: "Add integration tests for authentication and source-unavailable failures in backend/tests/integration/test_ingestion_source_failures.py"
Task: "Add integration tests for validation and storage failures in backend/tests/integration/test_ingestion_processing_failures.py"
Task: "Add acceptance-aligned integration test for no partial activation on failed runs in backend/tests/integration/test_no_partial_activation.py"

# Run US2 persistence work in parallel
Task: "Implement failure notification repository operations in backend/app/repositories/failure_notification_repository.py"
Task: "Implement failure notification schema mapping and serialization in backend/app/schemas/failure_notifications.py"
```

## Parallel Example: User Story 3

```bash
# Run US3 test authoring in parallel
Task: "Add unit tests for no-new-records no-op rules in backend/tests/unit/test_no_new_records_rules.py"
Task: "Add integration test for the no-new-records success path in backend/tests/integration/test_ingestion_no_new_records.py"
Task: "Extend contract tests for no_new_records run status fields in backend/tests/contract/test_ingestion_api.py"

# Run US3 implementation work in parallel
Task: "Extend the Edmonton 311 client result mapping to classify empty incremental responses as no_new_records in backend/app/clients/edmonton_311.py"
Task: "Add structured no_new_records success logging in backend/app/services/ingestion_logging_service.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate AT-01 plus first-run cursor behavior before moving on.

### Incremental Delivery

1. Deliver US1 for successful ingestion, version creation, current activation, and cursor advancement.
2. Add US2 to harden all failed-run paths and monitoring persistence without changing the US1 success path.
3. Add US3 to support no-new-records success as an explicit no-op outcome.
4. Finish with Polish tasks for documentation and full acceptance alignment.

### Notes

- All tasks follow the required checklist format with exact file paths.
- `[P]` tasks touch different files and can proceed in parallel once dependencies are satisfied.
- UC-01 remains backend-only; no frontend, dashboard UI, forecasting, or email tasks are included.
