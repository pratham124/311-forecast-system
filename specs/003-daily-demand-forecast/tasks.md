# Tasks: Generate 1-Day Demand Forecast

**Input**: Design documents from `/specs/003-daily-demand-forecast/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/forecast-api.yaml, quickstart.md

**Tests**: Include unit, integration, contract, and acceptance-aligned backend tests because the specification and quickstart explicitly require pytest coverage aligned to `docs/UC-03-AT.md`.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving the constitution-aligned UC-03 backend scope.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Path Conventions

- Backend implementation: `backend/app/`
- Backend tests: `backend/tests/`
- Migrations: `backend/alembic/versions/`
- Planning artifacts: `specs/003-daily-demand-forecast/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the UC-03 forecasting module skeleton and implementation scaffolding that all later work depends on.

- [ ] T001 Create the UC-03 backend forecasting module skeleton in `backend/app/api/routes/forecasts.py`, `backend/app/clients/geomet_client.py`, `backend/app/clients/nager_date_client.py`, `backend/app/pipelines/forecasting/hourly_demand_pipeline.py`, `backend/app/repositories/forecast_repository.py`, `backend/app/repositories/forecast_run_repository.py`, `backend/app/schemas/forecast.py`, and `backend/app/services/forecast_service.py`
- [ ] T002 Configure forecast-specific settings for scheduler timing, GeoMet, Nager.Date, and model parameters in `backend/app/core/config.py`
- [ ] T003 [P] Add a forecasting test package scaffold in `backend/tests/contract/test_forecast_api.py`, `backend/tests/integration/test_forecast_generation.py`, `backend/tests/integration/test_forecast_reuse.py`, `backend/tests/integration/test_forecast_failures.py`, and `backend/tests/unit/test_forecast_pipeline.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared forecast lifecycle, auth, contracts, and observability infrastructure before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add migration-managed forecast lifecycle tables in `backend/alembic/versions/003_forecast_lifecycle.py`
- [ ] T005 [P] Define repository-owned forecast lifecycle models for `ForecastRun`, `ForecastVersion`, `ForecastBucket`, and `CurrentForecastMarker` in `backend/app/repositories/models.py`
- [ ] T006 [P] Define Pydantic request and response schemas for trigger, run-status, and current-forecast surfaces in `backend/app/schemas/forecast.py`
- [ ] T007 [P] Implement repository methods for forecast runs, forecast versions, buckets, and current-marker persistence in `backend/app/repositories/forecast_run_repository.py` and `backend/app/repositories/forecast_repository.py`
- [ ] T008 [P] Implement approved cleaned dataset lookup and shared lineage access for UC-03 in `backend/app/repositories/cleaned_dataset_repository.py`
- [ ] T009 [P] Implement dedicated Government of Canada MSC GeoMet normalization in `backend/app/clients/geomet_client.py`
- [ ] T010 [P] Implement dedicated Nager.Date Canada holiday normalization in `backend/app/clients/nager_date_client.py`
- [ ] T011 [P] Implement JWT-authenticated RBAC dependencies for forecast trigger and read surfaces in `backend/app/api/dependencies/auth.py`
- [ ] T012 [P] Implement structured forecast logging and failure classification helpers in `backend/app/core/logging.py`
- [ ] T013 Wire the forecast router and dependency injection into the backend application in `backend/app/api/routes/forecasts.py` and `backend/app/main.py`

**Checkpoint**: Forecast persistence, enrichment clients, auth, schemas, and routing foundations are in place.

---

## Phase 3: User Story 1 - Generate a current daily forecast (Priority: P1) 🎯 MVP

**Goal**: Generate and activate a new 24-hour hourly forecast by service category, with geography when supported, using the approved dataset lineage and constitution-required enrichments and safeguards.

**Independent Test**: Trigger forecast generation with approved input data and confirm a new stored forecast version with 24 hourly buckets becomes current and is returned through the current-forecast read surface.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add contract coverage for `POST /api/v1/forecast-runs/1-day/trigger` and `GET /api/v1/forecasts/current` in `backend/tests/contract/test_forecast_api.py`
- [ ] T015 [P] [US1] Add unit coverage for leakage-free feature assembly, quantile ordering, and hourly bucket materialization in `backend/tests/unit/test_forecast_pipeline.py`
- [ ] T016 [P] [US1] Add integration coverage for successful on-demand and scheduled generation in `backend/tests/integration/test_forecast_generation.py`

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement leakage-free feature preparation from the approved cleaned dataset plus GeoMet and Nager.Date enrichments in `backend/app/pipelines/forecasting/feature_preparation.py`
- [ ] T018 [P] [US1] Implement the single global LightGBM forecast path with baseline comparator and `P10`/`P50`/`P90` outputs in `backend/app/pipelines/forecasting/hourly_demand_pipeline.py`
- [ ] T019 [P] [US1] Implement hourly forecast bucket creation and geography-scope handling in `backend/app/services/forecast_bucket_service.py`
- [ ] T020 [US1] Implement forecast orchestration for accepted generation requests and scheduled runs in `backend/app/services/forecast_service.py`
- [ ] T021 [US1] Implement safe forecast persistence and post-store current-marker activation in `backend/app/services/forecast_activation_service.py`
- [ ] T022 [US1] Implement the trigger endpoint and scheduler entrypoint using thin route handling in `backend/app/api/routes/forecasts.py` and `backend/app/services/forecast_scheduler.py`
- [ ] T023 [US1] Implement the current-forecast read endpoint with typed responses and no model internals exposure in `backend/app/api/routes/forecasts.py`

**Checkpoint**: User Story 1 delivers a complete forecast-generation path and current-forecast read path for the 24-hour hourly product.

---

## Phase 4: User Story 2 - Reuse an already current forecast (Priority: P2)

**Goal**: Serve an existing current forecast for the same 24-hour window without rerunning the model and record that reuse distinctly.

**Independent Test**: Seed a current forecast for the requested horizon, trigger the forecast surface, and confirm the stored forecast is served without creating a new forecast version or invoking model execution.

### Tests for User Story 2

- [ ] T024 [P] [US2] Add contract coverage for `GET /api/v1/forecast-runs/{forecastRunId}` success, 404, 422, and reuse reporting in `backend/tests/contract/test_forecast_api.py`
- [ ] T025 [P] [US2] Add unit coverage for 24-hour horizon reuse eligibility rules in `backend/tests/unit/test_forecast_pipeline.py`
- [ ] T026 [P] [US2] Add integration coverage for reuse of an already current forecast and rejection of partial-window reuse in `backend/tests/integration/test_forecast_reuse.py`

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement repository queries for exact-horizon current forecast lookup and served-current linkage in `backend/app/repositories/forecast_repository.py`
- [ ] T028 [US2] Implement reuse decision logic that distinguishes exact-horizon reuse from regeneration in `backend/app/services/forecast_service.py`
- [ ] T029 [US2] Implement forecast-run outcome recording for `served_current` responses in `backend/app/repositories/forecast_run_repository.py`
- [ ] T030 [US2] Implement the full run-status endpoint, including status lookup, normal success responses, 404 handling, 422 handling, and reused-current response shaping in `backend/app/api/routes/forecasts.py`

**Checkpoint**: User Story 2 adds reuse without changing User Story 1 generation behavior.

---

## Phase 5: User Story 3 - Protect operations from failed or incomplete updates (Priority: P3)

**Goal**: Preserve the last-known-good current forecast across missing data, enrichment or model failures, storage failures, category-only fallbacks, and access-denial scenarios.

**Independent Test**: Simulate missing approved input data, incomplete geography, model failure, storage failure, and access denial; confirm the current forecast remains unchanged except for valid category-only success and that denied or invalid requests do not create forecast runs.

### Tests for User Story 3

- [ ] T031 [P] [US3] Add contract coverage for unauthorized, forbidden, missing-resource, and invalid-request responses in `backend/tests/contract/test_forecast_api.py`
- [ ] T032 [P] [US3] Add unit coverage for activation guards, category-only fallback, and no-run creation on denied or invalid requests in `backend/tests/unit/test_forecast_pipeline.py`
- [ ] T033 [P] [US3] Add integration coverage for missing data, category-only success, storage failure, and unchanged current-marker behavior in `backend/tests/integration/test_forecast_failures.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement category-only fallback handling and geography omission recording in `backend/app/services/forecast_bucket_service.py`
- [ ] T035 [P] [US3] Implement missing-input, enrichment-failure, and model-failure outcome classification in `backend/app/services/forecast_service.py`
- [ ] T036 [P] [US3] Implement activation guards that preserve the prior current forecast on storage failure or partial persistence in `backend/app/services/forecast_activation_service.py`
- [ ] T037 [US3] Implement read-surface missing-resource handling and invalid-request rejection in `backend/app/api/routes/forecasts.py`
- [ ] T038 [US3] Implement auth-denial handling that blocks run creation for trigger and read surfaces in `backend/app/api/routes/forecasts.py` and `backend/app/api/dependencies/auth.py`
- [ ] T039 [US3] Implement persisted run-history summaries and failure-safe observability without raw payload exposure in `backend/app/repositories/forecast_run_repository.py` and `backend/app/core/logging.py`

**Checkpoint**: User Story 3 completes last-known-good safety, category-only fallback, and access/error separation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish cross-story verification, documentation, and implementation hardening without turning this task list into an execution log.

- [ ] T040 [P] Update UC-03 implementation notes and artifact traceability in `specs/003-daily-demand-forecast/quickstart.md`
- [ ] T041 [P] Add on-demand generation and category-only latency verification for SC-001 and SC-005 in `backend/tests/integration/test_forecast_generation.py` and `backend/tests/integration/test_forecast_failures.py`
- [ ] T042 [P] Add current-forecast reuse latency verification for SC-003 in `backend/tests/integration/test_forecast_reuse.py`
- [ ] T043 [P] Add scheduler and API usage examples for the forecast product in `specs/003-daily-demand-forecast/contracts/forecast-api.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: User Story 1**: Depends on Phase 2.
- **Phase 4: User Story 2**: Depends on Phase 2 and on User Story 1 persistence and read foundations from T020-T023.
- **Phase 5: User Story 3**: Depends on Phase 2 and on User Story 1 activation flow from T020-T023.
- **Phase 6: Polish**: Depends on completion of the user stories being shipped.

### User Story Dependencies

- **US1**: No dependency on other user stories; this is the MVP.
- **US2**: Depends on US1 forecast storage and current-forecast read behavior.
- **US3**: Depends on US1 generation and activation behavior; it can proceed independently of US2.

### Within Each User Story

- Test tasks should be completed before or alongside implementation and must fail before the implementation is considered complete.
- Repository and pipeline work precedes service orchestration.
- Service orchestration precedes route finalization.
- Activation and observability verification close each story.

### Dependency Graph

`Setup -> Foundational -> US1 -> {US2, US3} -> Polish`

---

## Parallel Opportunities

- Phase 1: T003 can run while T001-T002 are in progress.
- Phase 2: T005-T012 are parallelizable after T004 if model imports require the migrated schema names to be settled first.
- US1: T014-T016 can run in parallel; T017-T019 can run in parallel before T020.
- US2: T024-T026 can run in parallel; T027 and T029 can run in parallel before T028-T030.
- US3: T031-T033 can run in parallel; T034-T036 can run in parallel before T037-T039.
- US2 and US3 can run in parallel after US1 is complete.

## Parallel Example: User Story 1

```bash
Task: "Add contract coverage for POST /api/v1/forecast-runs/1-day/trigger and GET /api/v1/forecasts/current in backend/tests/contract/test_forecast_api.py"
Task: "Add unit coverage for leakage-free feature assembly, quantile ordering, and hourly bucket materialization in backend/tests/unit/test_forecast_pipeline.py"
Task: "Add integration coverage for successful on-demand and scheduled generation in backend/tests/integration/test_forecast_generation.py"

Task: "Implement leakage-free feature preparation from the approved cleaned dataset plus GeoMet and Nager.Date enrichments in backend/app/pipelines/forecasting/feature_preparation.py"
Task: "Implement the single global LightGBM forecast path with baseline comparator and P10/P50/P90 outputs in backend/app/pipelines/forecasting/hourly_demand_pipeline.py"
Task: "Implement hourly forecast bucket creation and geography-scope handling in backend/app/services/forecast_bucket_service.py"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract coverage for GET /api/v1/forecast-runs/{forecastRunId} success, 404, 422, and reuse reporting in backend/tests/contract/test_forecast_api.py"
Task: "Add unit coverage for 24-hour horizon reuse eligibility rules in backend/tests/unit/test_forecast_pipeline.py"
Task: "Add integration coverage for reuse of an already current forecast and rejection of partial-window reuse in backend/tests/integration/test_forecast_reuse.py"

Task: "Implement repository queries for exact-horizon current forecast lookup and served-current linkage in backend/app/repositories/forecast_repository.py"
Task: "Implement forecast-run outcome recording for served_current responses in backend/app/repositories/forecast_run_repository.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract coverage for unauthorized, forbidden, missing-resource, and invalid-request responses in backend/tests/contract/test_forecast_api.py"
Task: "Add unit coverage for activation guards, category-only fallback, and no-run creation on denied or invalid requests in backend/tests/unit/test_forecast_pipeline.py"
Task: "Add integration coverage for missing data, category-only success, storage failure, and unchanged current-marker behavior in backend/tests/integration/test_forecast_failures.py"

Task: "Implement category-only fallback handling and geography omission recording in backend/app/services/forecast_bucket_service.py"
Task: "Implement missing-input, enrichment-failure, and model-failure outcome classification in backend/app/services/forecast_service.py"
Task: "Implement activation guards that preserve the prior current forecast on storage failure or partial persistence in backend/app/services/forecast_activation_service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3.
4. Validate successful generation, persistence, and current-forecast reads before expanding scope.

### Incremental Delivery

1. Deliver US1 to establish the core 24-hour hourly forecast product.
2. Add US2 to avoid unnecessary reruns and improve response speed.
3. Add US3 to harden failure handling, category-only fallback, and access/error separation.
4. Finish with Phase 6 verification and documentation updates.

### Parallel Team Strategy

1. One developer can own migrations, models, and repositories in Phase 2.
2. One developer can own enrichment and pipeline work for US1.
3. After US1, one developer can implement US2 reuse logic while another implements US3 failure-safety and auth/error handling.

---

## Notes

- The task list preserves the constitution-aligned UC-03 scope and does not add frontend work, dashboards, or manual workflows.
- Every user story phase is independently testable against the spec and `docs/UC-03-AT.md`.
- All tasks follow the required checklist format with task IDs, optional parallel markers, story labels where required, and exact file paths.
- `tasks.md` remains a planning checklist rather than a place to record execution results.
