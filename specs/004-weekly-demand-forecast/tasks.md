# Tasks: Generate 7-Day Demand Forecast

**Input**: Design documents from `/specs/004-weekly-demand-forecast/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/forecast-api.yaml, quickstart.md

**Tests**: Include unit, integration, contract, and acceptance-aligned backend tests because the feature docs explicitly define independent test criteria per user story and acceptance alignment to `docs/UC-04-AT.md`.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving UC-04 scope.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Path Conventions

- Backend implementation: `backend/app/`
- Backend tests: `backend/tests/`
- Migrations: `backend/alembic/versions/`
- Planning artifacts: `specs/004-weekly-demand-forecast/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create UC-04 module scaffolding and baseline configuration shared by all stories.

- [ ] T001 Create UC-04 forecasting module scaffolding in `backend/app/api/routes/weekly_forecasts.py`, `backend/app/pipelines/forecasting/weekly_demand_pipeline.py`, `backend/app/services/weekly_forecast_service.py`, `backend/app/repositories/weekly_forecast_repository.py`, `backend/app/repositories/weekly_forecast_run_repository.py`, and `backend/app/schemas/weekly_forecast.py`
- [ ] T002 Configure weekly forecast settings for scheduler timing, week-boundary timezone, and pipeline controls in `backend/app/core/config.py`
- [ ] T003 [P] Create UC-04 test scaffolding in `backend/tests/contract/test_weekly_forecast_api.py`, `backend/tests/integration/test_weekly_forecast_generation.py`, `backend/tests/integration/test_weekly_forecast_reuse.py`, `backend/tests/integration/test_weekly_forecast_failures.py`, and `backend/tests/unit/test_weekly_forecast_service.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared lifecycle, schema, contract, and orchestration foundations required before any story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add migration-managed UC-04 tables for weekly forecast run/version/bucket/current-marker lifecycle including quantile and baseline fields in `backend/alembic/versions/004_weekly_forecast_lifecycle.py`
- [ ] T005 [P] Define repository ORM models for `WeeklyForecastRun`, `WeeklyForecastVersion`, `WeeklyForecastBucket`, and `CurrentWeeklyForecastMarker` in `backend/app/repositories/models.py`
- [ ] T006 [P] Define Pydantic schemas for trigger, run-status, and current-weekly response contracts including quantile/baseline outputs and in-progress dedupe context in `backend/app/schemas/weekly_forecast.py`
- [ ] T007 [P] Implement repository methods for weekly run/version/bucket/current-marker persistence in `backend/app/repositories/weekly_forecast_repository.py` and `backend/app/repositories/weekly_forecast_run_repository.py`
- [ ] T008 [P] Implement approved cleaned dataset lookup for UC-04 lineage reuse in `backend/app/repositories/cleaned_dataset_repository.py`
- [ ] T009 [P] Implement week-boundary utility for Monday-start operational windows in `backend/app/services/week_window_service.py`
- [ ] T010 [P] Implement authenticated role dependencies for weekly trigger and read surfaces in `backend/app/api/dependencies/auth.py`
- [ ] T011 [P] Implement structured logging helpers for weekly run outcomes and failure classification in `backend/app/core/logging.py`
- [ ] T012 Wire weekly forecast router registration in `backend/app/api/routes/weekly_forecasts.py` and `backend/app/main.py`
- [ ] T013 Align OpenAPI contract examples and schema naming with implementation paths in `specs/004-weekly-demand-forecast/contracts/forecast-api.yaml`

**Checkpoint**: Foundations ready for independent user story implementation.

---

## Phase 3: User Story 1 - Generate Weekly Forecast (Priority: P1) 🎯 MVP

**Goal**: Generate and activate a new 7-day forecast by service category with optional geography using approved lineage and deterministic week boundaries.

**Independent Test**: Trigger on-demand and scheduled generation with valid input and confirm a new stored weekly forecast with 7 daily buckets is marked current and retrievable.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add contract tests for `POST /api/v1/forecast-runs/7-day/trigger` and `GET /api/v1/forecasts/current-weekly` in `backend/tests/contract/test_weekly_forecast_api.py`
- [ ] T015 [P] [US1] Add unit tests for week-window derivation, seven-day bucket construction, and quantile ordering in `backend/tests/unit/test_weekly_forecast_service.py`
- [ ] T016 [P] [US1] Add integration tests for successful on-demand, scheduled weekly, and automated daily-regeneration generation paths in `backend/tests/integration/test_weekly_forecast_generation.py`

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement leakage-safe weekly feature preparation from approved lineage and enrichments in `backend/app/pipelines/forecasting/weekly_feature_preparation.py`
- [ ] T018 [P] [US1] Implement weekly forecasting pipeline producing seven daily category demand values plus `P10`/`P50`/`P90` and baseline comparator outputs in `backend/app/pipelines/forecasting/weekly_demand_pipeline.py`
- [ ] T019 [P] [US1] Implement weekly bucket materialization and geography-scope tagging in `backend/app/services/weekly_forecast_bucket_service.py`
- [ ] T020 [US1] Implement orchestration for accepted on-demand and scheduled generation in `backend/app/services/weekly_forecast_service.py`
- [ ] T021 [US1] Implement safe persistence plus post-store current-marker activation in `backend/app/services/weekly_forecast_activation_service.py`
- [ ] T022 [US1] Implement trigger endpoint and scheduler entrypoints for weekly and daily-regeneration runs using thin route handlers in `backend/app/api/routes/weekly_forecasts.py` and `backend/app/services/weekly_forecast_scheduler.py`
- [ ] T023 [US1] Implement current-weekly-forecast read endpoint with typed responses in `backend/app/api/routes/weekly_forecasts.py`

**Checkpoint**: US1 delivers end-to-end weekly forecast generation and retrieval.

---

## Phase 4: User Story 2 - Reuse Current Forecast (Priority: P2)

**Goal**: Serve an already current weekly forecast for the same operational week without rerunning generation.

**Independent Test**: Seed a current weekly forecast for the same operational week, trigger a forecast request, and confirm the existing version is served with no new generated version.

### Tests for User Story 2

- [ ] T024 [P] [US2] Add contract tests for run-status reuse reporting and relevant 404/422 paths in `backend/tests/contract/test_weekly_forecast_api.py`
- [ ] T025 [P] [US2] Add unit tests for same-week reuse eligibility, in-progress deduplication, and non-reuse boundaries in `backend/tests/unit/test_weekly_forecast_service.py`
- [ ] T026 [P] [US2] Add integration tests for current-week reuse behavior (AT-03) and same-week in-progress dedupe behavior in `backend/tests/integration/test_weekly_forecast_reuse.py`

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement repository queries for current-forecast lookup by operational week in `backend/app/repositories/weekly_forecast_repository.py`
- [ ] T028 [US2] Implement reuse decision logic, served-current outcomes, and in-progress same-week dedupe handling in `backend/app/services/weekly_forecast_service.py`
- [ ] T029 [US2] Implement persisted `served_current` run outcome recording in `backend/app/repositories/weekly_forecast_run_repository.py`
- [ ] T030 [US2] Implement run-status endpoint response shaping for reuse outcomes in `backend/app/api/routes/weekly_forecasts.py`

**Checkpoint**: US2 adds deterministic reuse without changing US1 generation behavior.

---

## Phase 5: User Story 3 - Maintain Continuity on Failures (Priority: P3)

**Goal**: Preserve last-known-good current weekly forecast across missing-data, engine, and storage failures while supporting category-only success when geography is incomplete.

**Independent Test**: Inject missing-data, engine-failure, and storage-failure conditions plus incomplete geography and confirm current marker behavior matches AT-04 through AT-08.

### Tests for User Story 3

- [ ] T031 [P] [US3] Add contract tests for unauthorized, forbidden, and no-current-forecast responses in `backend/tests/contract/test_weekly_forecast_api.py`
- [ ] T032 [P] [US3] Add unit tests for failure classification and activation guards in `backend/tests/unit/test_weekly_forecast_service.py`
- [ ] T033 [P] [US3] Add integration tests for AT-04, AT-05, AT-06, AT-07, and AT-08 in `backend/tests/integration/test_weekly_forecast_failures.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement missing-input-data and engine-failure classification in `backend/app/services/weekly_forecast_service.py`
- [ ] T035 [P] [US3] Implement category-only fallback logic for incomplete geography in `backend/app/services/weekly_forecast_bucket_service.py`
- [ ] T036 [P] [US3] Implement storage-failure handling that blocks activation in `backend/app/services/weekly_forecast_activation_service.py`
- [ ] T037 [US3] Implement run-failure persistence with explicit failure reasons in `backend/app/repositories/weekly_forecast_run_repository.py`
- [ ] T038 [US3] Implement no-partial-activation invariants in `backend/app/services/weekly_forecast_activation_service.py`
- [ ] T039 [US3] Implement route-level handling for no-current-forecast reads and invalid requests in `backend/app/api/routes/weekly_forecasts.py`

**Checkpoint**: US3 completes failure-safe continuity and category-only fallback.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize cross-story traceability, documentation, and operational readiness checks.

- [ ] T040 [P] Map implemented tests to `docs/UC-04-AT.md` traceability notes in `specs/004-weekly-demand-forecast/quickstart.md`
- [ ] T041 [P] Update checklist follow-up clarifications and requirement alignment notes in `specs/004-weekly-demand-forecast/spec.md` and `specs/004-weekly-demand-forecast/checklists/api-data-security-performance.md`
- [ ] T042 [P] Add performance assertion scenarios for SC-002, SC-004, and SC-007 in `backend/tests/integration/test_weekly_forecast_generation.py` and `backend/tests/integration/test_weekly_forecast_reuse.py`
- [ ] T043 [P] Add cross-cutting observability verification for success/reuse/failure paths in `backend/tests/integration/test_weekly_forecast_failures.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all story work.
- **Phase 3: US1**: Depends on Phase 2.
- **Phase 4: US2**: Depends on Phase 2 and US1 persistence/read foundations.
- **Phase 5: US3**: Depends on Phase 2 and US1 generation/activation foundations.
- **Phase 6: Polish**: Depends on completion of targeted user stories.

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational; this is the MVP.
- **US2 (P2)**: Depends on US1 forecast storage and current marker behavior.
- **US3 (P3)**: Depends on US1 generation and activation flow; independent from US2.

### Dependency Graph

`Setup -> Foundational -> US1 -> {US2, US3} -> Polish`

---

## Parallel Opportunities

- Setup: T003 parallel with T001-T002.
- Foundational: T005-T011 parallel after migration naming is fixed in T004.
- US1: T014-T016 parallel; T017-T019 parallel before T020.
- US2: T024-T026 parallel; T027 and T029 parallel before T028-T030.
- US3: T031-T033 parallel; T034-T036 parallel before T037-T039.
- US2 and US3 can execute in parallel after US1 completion.

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for POST /api/v1/forecast-runs/7-day/trigger and GET /api/v1/forecasts/current-weekly in backend/tests/contract/test_weekly_forecast_api.py"
Task: "Add unit tests for week-window derivation and seven-day bucket construction in backend/tests/unit/test_weekly_forecast_service.py"
Task: "Add integration tests for successful on-demand and scheduled weekly generation (AT-01, AT-02) in backend/tests/integration/test_weekly_forecast_generation.py"

Task: "Implement leakage-safe weekly feature preparation from approved lineage and enrichments in backend/app/pipelines/forecasting/weekly_feature_preparation.py"
Task: "Implement weekly forecasting pipeline producing seven daily category demand values in backend/app/pipelines/forecasting/weekly_demand_pipeline.py"
Task: "Implement weekly bucket materialization and geography-scope tagging in backend/app/services/weekly_forecast_bucket_service.py"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract tests for run-status reuse reporting and relevant 404/422 paths in backend/tests/contract/test_weekly_forecast_api.py"
Task: "Add unit tests for same-week reuse eligibility and non-reuse boundaries in backend/tests/unit/test_weekly_forecast_service.py"
Task: "Add integration tests for current-week reuse behavior (AT-03) in backend/tests/integration/test_weekly_forecast_reuse.py"

Task: "Implement repository queries for current-forecast lookup by operational week in backend/app/repositories/weekly_forecast_repository.py"
Task: "Implement persisted served_current run outcome recording in backend/app/repositories/weekly_forecast_run_repository.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract tests for unauthorized, forbidden, and no-current-forecast responses in backend/tests/contract/test_weekly_forecast_api.py"
Task: "Add unit tests for failure classification and activation guards in backend/tests/unit/test_weekly_forecast_service.py"
Task: "Add integration tests for AT-04, AT-05, AT-06, AT-07, and AT-08 in backend/tests/integration/test_weekly_forecast_failures.py"

Task: "Implement missing-input-data and engine-failure classification in backend/app/services/weekly_forecast_service.py"
Task: "Implement category-only fallback logic for incomplete geography in backend/app/services/weekly_forecast_bucket_service.py"
Task: "Implement storage-failure handling that blocks activation in backend/app/services/weekly_forecast_activation_service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3 (US1).
4. Validate independent test criteria for US1 before expanding scope.

### Incremental Delivery

1. Deliver US1 for end-to-end weekly generation and current retrieval.
2. Deliver US2 for same-week reuse optimization.
3. Deliver US3 for failure-safe continuity and category-only fallback.
4. Run Polish tasks for traceability and cross-cutting verification.

### Parallel Team Strategy

1. One engineer owns migration/models/repositories in Foundational phase.
2. One engineer owns pipeline/service orchestration in US1.
3. After US1, one engineer can take US2 while another takes US3.

---

## Notes

- All tasks follow required checklist format with task ID, optional `[P]`, required `[US#]` labels for story tasks, and file paths.
- User stories are organized for independent implementation and verification.
- Task list is scoped to UC-04 backend workflows and excludes frontend work.
