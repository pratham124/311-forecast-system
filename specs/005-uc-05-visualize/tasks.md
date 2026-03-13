# Tasks: Visualize Forecast Curves with Uncertainty Bands

**Input**: Design documents from `/specs/005-uc-05-visualize/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/forecast-visualization-api.yaml, quickstart.md

**Tests**: Include backend unit, integration, and contract tests plus frontend component and interaction tests because the plan and quickstart explicitly require acceptance-aligned verification for `docs/UC-05-AT.md`.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving the constitution-aligned UC-05 backend/frontend scope.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Path Conventions

- Backend implementation: `backend/app/`
- Backend tests: `backend/tests/`
- Frontend implementation: `frontend/src/`
- Database migrations: `backend/alembic/versions/`
- Planning artifacts: `specs/005-uc-05-visualize/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the UC-05 visualization scaffolding shared by all stories across backend and frontend.

- [ ] T001 Create UC-05 backend and frontend scaffolding in `backend/app/api/routes/forecast_visualizations.py`, `backend/app/repositories/visualization_repository.py`, `backend/app/schemas/forecast_visualization.py`, `backend/app/services/forecast_visualization_service.py`, `backend/app/services/visualization_snapshot_service.py`, `frontend/src/api/forecastVisualizations.ts`, `frontend/src/features/forecast-visualization/components/ForecastVisualizationChart.tsx`, `frontend/src/features/forecast-visualization/hooks/useForecastVisualization.ts`, and `frontend/src/pages/ForecastVisualizationPage.tsx`
- [ ] T002 Configure visualization-specific backend and frontend settings for fallback age, dashboard defaults, and render-event submission in `backend/app/core/config.py` and `frontend/src/config/env.ts`
- [ ] T003 [P] Create UC-05 test scaffolding in `backend/tests/contract/test_forecast_visualization_api.py`, `backend/tests/integration/test_forecast_visualization_success.py`, `backend/tests/integration/test_forecast_visualization_degraded.py`, `backend/tests/integration/test_forecast_visualization_fallback.py`, `backend/tests/unit/test_forecast_visualization_service.py`, `frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx`, and `frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationChart.test.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared persistence, normalization, routing, and typed dashboard infrastructure required before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add migration-managed UC-05 tables for `VisualizationLoadRecord` and `VisualizationSnapshot` lifecycle state in `backend/alembic/versions/005_visualization_lifecycle.py`
- [ ] T005 [P] Define repository ORM models for `VisualizationLoadRecord` and `VisualizationSnapshot` in `backend/app/repositories/models.py`
- [ ] T006 [P] Define typed backend schemas for current-visualization responses and render-event requests in `backend/app/schemas/forecast_visualization.py`
- [ ] T007 [P] Implement repository methods for visualization load records, eligible fallback snapshot lookup, snapshot persistence, and terminal outcome updates in `backend/app/repositories/visualization_repository.py`
- [ ] T008 [P] Implement approved cleaned dataset lookup and 7-day historical demand aggregation reuse for UC-05 in `backend/app/repositories/cleaned_dataset_repository.py`
- [ ] T009 [P] Implement current daily and weekly forecast product normalization helpers in `backend/app/services/forecast_visualization_sources.py`
- [ ] T010 [P] Implement authenticated dashboard access dependencies and role enforcement for visualization read/write routes in `backend/app/api/dependencies/auth.py`
- [ ] T011 [P] Implement structured logging helpers for visualization load statuses, degradations, fallback use, and render failures in `backend/app/core/logging.py`
- [ ] T012 [P] Implement shared frontend domain types, API client typing, and status-message models in `frontend/src/types/forecastVisualization.ts`, `frontend/src/api/forecastVisualizations.ts`, and `frontend/src/utils/statusMessages.ts`
- [ ] T013 Wire the visualization router and dashboard page registration in `backend/app/api/routes/forecast_visualizations.py`, `backend/app/main.py`, `frontend/src/pages/ForecastVisualizationPage.tsx`, and `frontend/src/App.tsx`

**Checkpoint**: Visualization persistence, source normalization, auth, typed contracts, and route/page wiring are in place.

---

## Phase 3: User Story 1 - View Forecast with Historical Context (Priority: P1) 🎯 MVP

**Goal**: Let an Operational Manager open the dashboard and see the current daily or weekly forecast curve with `P10`/`P50`/`P90` bands over the previous 7 days of historical demand on one shared time axis.

**Independent Test**: Load the dashboard with valid current forecast, uncertainty, and historical inputs and confirm the chart, metadata, and successful visualization outcome all appear together for the selected product.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add contract coverage for `GET /api/v1/forecast-visualizations/current` success, auth failure, and query validation in `backend/tests/contract/test_forecast_visualization_api.py`
- [ ] T015 [P] [US1] Add backend unit coverage for 7-day history window selection, daily/weekly normalization, shared-axis alignment, and `P10`/`P50`/`P90` mapping in `backend/tests/unit/test_forecast_visualization_service.py`
- [ ] T016 [P] [US1] Add integration coverage for successful current daily and weekly visualization assembly plus load-outcome recording in `backend/tests/integration/test_forecast_visualization_success.py`
- [ ] T017 [P] [US1] Add frontend component and page interaction coverage for combined history/forecast/band rendering and boundary visibility in `frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationChart.test.tsx` and `frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx`

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement historical overlay assembly from the approved cleaned dataset with a strict 7-day context window in `backend/app/services/historical_demand_service.py`
- [ ] T019 [P] [US1] Implement normalized daily and weekly forecast-series extraction with canonical `P10`/`P50`/`P90` output labels in `backend/app/services/forecast_visualization_sources.py`
- [ ] T020 [P] [US1] Implement visualization response assembly for shared-axis chart data, last-updated metadata, category filter state, and success outcome creation in `backend/app/services/forecast_visualization_service.py`
- [ ] T021 [P] [US1] Implement reusable chart primitives and typed series adapters for history, forecast, uncertainty, and forecast-boundary markers in `frontend/src/features/forecast-visualization/components/ForecastVisualizationChart.tsx` and `frontend/src/features/forecast-visualization/utils/chartSeries.ts`
- [ ] T022 [US1] Implement the current-visualization endpoint with thin request handling and typed responses in `backend/app/api/routes/forecast_visualizations.py`
- [ ] T023 [US1] Implement the dashboard data hook and page composition for product selection, category filtering, alerts, pipeline status, and last-updated display in `frontend/src/features/forecast-visualization/hooks/useForecastVisualization.ts` and `frontend/src/pages/ForecastVisualizationPage.tsx`
- [ ] T024 [US1] Implement successful render-event submission and terminal outcome updates in `backend/app/api/routes/forecast_visualizations.py`, `backend/app/services/forecast_visualization_service.py`, and `frontend/src/api/forecastVisualizations.ts`

**Checkpoint**: User Story 1 delivers a complete current-visualization experience for daily and weekly products with successful-outcome recording.

---

## Phase 4: User Story 2 - Continue Using the Dashboard When Some Inputs Are Missing (Priority: P2)

**Goal**: Preserve dashboard usability when historical data or uncertainty metrics are missing by returning only the valid elements and making the degradation explicit.

**Independent Test**: Load the dashboard once with history unavailable and once with uncertainty unavailable, then confirm the chart omits only the missing element, surfaces clear status metadata, and records the correct degraded outcome.

### Tests for User Story 2

- [ ] T025 [P] [US2] Add contract coverage for degraded `GET /api/v1/forecast-visualizations/current` responses with `history_missing` and `uncertainty_missing` states in `backend/tests/contract/test_forecast_visualization_api.py`
- [ ] T026 [P] [US2] Add backend unit coverage for degradation selection, omitted-series response shaping, and stable alerts/pipeline-status population in `backend/tests/unit/test_forecast_visualization_service.py`
- [ ] T027 [P] [US2] Add integration coverage for history-missing and uncertainty-missing visualization loads and persisted degraded outcomes in `backend/tests/integration/test_forecast_visualization_degraded.py`
- [ ] T028 [P] [US2] Add frontend interaction coverage for degraded banners, omitted chart elements, and category-filter continuity in `frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx`

### Implementation for User Story 2

- [ ] T029 [P] [US2] Implement degradation detection for missing historical context and missing uncertainty metrics in `backend/app/services/forecast_visualization_service.py`
- [ ] T030 [P] [US2] Implement degraded-state persistence, degradation-type recording, and status-summary generation in `backend/app/repositories/visualization_repository.py` and `backend/app/services/forecast_visualization_status_service.py`
- [ ] T031 [P] [US2] Implement frontend status panels and empty-state treatments that distinguish omitted history from omitted uncertainty without implying zero values in `frontend/src/features/forecast-visualization/components/VisualizationStatusPanel.tsx` and `frontend/src/features/forecast-visualization/components/ForecastVisualizationChart.tsx`
- [ ] T032 [US2] Implement route and schema support for explicit degraded responses including `degradationType` and stable alerts/pipeline-status arrays in `backend/app/api/routes/forecast_visualizations.py` and `backend/app/schemas/forecast_visualization.py`
- [ ] T033 [US2] Implement dashboard copy and filter-preserving degraded rendering behavior in `frontend/src/pages/ForecastVisualizationPage.tsx` and `frontend/src/features/forecast-visualization/hooks/useForecastVisualization.ts`

**Checkpoint**: User Story 2 adds graceful degraded behavior without changing User Story 1 success-path semantics.

---

## Phase 5: User Story 3 - Receive a Reliable Fallback on Visualization Failure (Priority: P3)

**Goal**: Show a bounded last-known-good fallback or an explicit unavailable/error state when current forecast visualization cannot be produced or rendered reliably.

**Independent Test**: Load the dashboard with missing current forecast data and with client render failure, then confirm the system shows an eligible fallback or explicit failure state and records the matching terminal outcome.

### Tests for User Story 3

- [ ] T034 [P] [US3] Add contract coverage for fallback-shown, unavailable, render-event acceptance, missing-load, and invalid render-event responses in `backend/tests/contract/test_forecast_visualization_api.py`
- [ ] T035 [P] [US3] Add backend unit coverage for 24-hour fallback eligibility, expired-snapshot rejection, and render-failure terminal transitions in `backend/tests/unit/test_forecast_visualization_service.py`
- [ ] T036 [P] [US3] Add integration coverage for missing-current-forecast fallback, expired-fallback unavailable state, and persisted render-failure outcomes in `backend/tests/integration/test_forecast_visualization_fallback.py`
- [ ] T037 [P] [US3] Add frontend interaction coverage for fallback badges, unavailable states, and render-failure reporting in `frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx`

### Implementation for User Story 3

- [ ] T038 [P] [US3] Implement fallback snapshot creation, expiration enforcement, and eligible snapshot retrieval in `backend/app/services/visualization_snapshot_service.py` and `backend/app/repositories/visualization_repository.py`
- [ ] T039 [P] [US3] Implement unavailable-state and fallback-shown selection logic for missing or invalid current forecast inputs in `backend/app/services/forecast_visualization_service.py`
- [ ] T040 [P] [US3] Implement frontend fallback, unavailable, and explicit render-error views plus client render-failure reporting in `frontend/src/pages/ForecastVisualizationPage.tsx`, `frontend/src/features/forecast-visualization/components/VisualizationFallbackBanner.tsx`, and `frontend/src/features/forecast-visualization/hooks/useForecastVisualization.ts`
- [ ] T041 [US3] Implement render-event endpoint handling, load-not-found validation, and terminal render-failure updates in `backend/app/api/routes/forecast_visualizations.py` and `backend/app/services/forecast_visualization_service.py`

**Checkpoint**: User Story 3 completes fallback resilience, unavailable/error states, and render-failure observability.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish acceptance traceability, performance verification, and contract/documentation hardening across the shipped stories.

- [ ] T042 [P] Map implemented backend and frontend verification to `docs/UC-05-AT.md` in `specs/005-uc-05-visualize/quickstart.md`
- [ ] T043 [P] Add performance and terminal-outcome assertions for SC-001, SC-005, and SC-006 in `backend/tests/integration/test_forecast_visualization_success.py` and `backend/tests/integration/test_forecast_visualization_fallback.py`
- [ ] T044 [P] Align request/response examples and degraded/fallback payload documentation in `specs/005-uc-05-visualize/contracts/forecast-visualization-api.yaml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: US1**: Depends on Phase 2.
- **Phase 4: US2**: Depends on Phase 2 and on US1 current-visualization assembly and frontend rendering foundations.
- **Phase 5: US3**: Depends on Phase 2 and on US1 load-record creation, render-event flow, and normalized visualization contract.
- **Phase 6: Polish**: Depends on completion of the user stories being shipped.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories; this is the MVP.
- **US2 (P2)**: Depends on US1 visualization assembly, contract, and dashboard rendering behavior.
- **US3 (P3)**: Depends on US1 load tracking and normalized visualization surfaces; it can proceed independently of US2.

### Within Each User Story

- Test tasks should be completed before or alongside implementation and must fail before the implementation is considered complete.
- Backend source assembly and normalization precede service orchestration.
- Service orchestration precedes route and frontend state finalization.
- Frontend view handling closes only after backend response shapes are stable.

### Dependency Graph

`Setup -> Foundational -> US1 -> {US2, US3} -> Polish`

---

## Parallel Opportunities

- Phase 1: T003 can run while T001-T002 are in progress.
- Phase 2: T005-T012 are parallelizable after T004 if migration naming must be settled first.
- US1: T014-T017 can run in parallel; T018-T021 can run in parallel before T022-T024.
- US2: T025-T028 can run in parallel; T029-T031 can run in parallel before T032-T033.
- US3: T034-T037 can run in parallel; T038-T040 can run in parallel before T041.
- US2 and US3 can run in parallel after US1 is complete.

## Parallel Example: User Story 1

```bash
Task: "Add contract coverage for GET /api/v1/forecast-visualizations/current success, auth failure, and query validation in backend/tests/contract/test_forecast_visualization_api.py"
Task: "Add backend unit coverage for 7-day history window selection and P10/P50/P90 mapping in backend/tests/unit/test_forecast_visualization_service.py"
Task: "Add integration coverage for successful current daily and weekly visualization assembly in backend/tests/integration/test_forecast_visualization_success.py"
Task: "Add frontend interaction coverage for combined history/forecast/band rendering in frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx"

Task: "Implement historical overlay assembly from the approved cleaned dataset in backend/app/services/historical_demand_service.py"
Task: "Implement normalized daily and weekly forecast-series extraction in backend/app/services/forecast_visualization_sources.py"
Task: "Implement reusable chart primitives and typed series adapters in frontend/src/features/forecast-visualization/components/ForecastVisualizationChart.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract coverage for degraded GET /api/v1/forecast-visualizations/current responses in backend/tests/contract/test_forecast_visualization_api.py"
Task: "Add integration coverage for history-missing and uncertainty-missing loads in backend/tests/integration/test_forecast_visualization_degraded.py"
Task: "Add frontend interaction coverage for degraded banners and omitted chart elements in frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx"

Task: "Implement degradation detection for missing historical context and missing uncertainty metrics in backend/app/services/forecast_visualization_service.py"
Task: "Implement degraded-state persistence and status-summary generation in backend/app/repositories/visualization_repository.py and backend/app/services/forecast_visualization_status_service.py"
Task: "Implement frontend status panels that distinguish omitted history from omitted uncertainty in frontend/src/features/forecast-visualization/components/VisualizationStatusPanel.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract coverage for fallback-shown, unavailable, and render-event responses in backend/tests/contract/test_forecast_visualization_api.py"
Task: "Add integration coverage for fallback, expired snapshot rejection, and render-failure outcomes in backend/tests/integration/test_forecast_visualization_fallback.py"
Task: "Add frontend interaction coverage for fallback badges, unavailable states, and render-failure reporting in frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx"

Task: "Implement fallback snapshot creation and expiration enforcement in backend/app/services/visualization_snapshot_service.py"
Task: "Implement unavailable-state and fallback-shown selection logic in backend/app/services/forecast_visualization_service.py"
Task: "Implement frontend fallback and explicit render-error views in frontend/src/pages/ForecastVisualizationPage.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3.
4. Validate successful visualization assembly, dashboard rendering, and render-event recording before expanding scope.

### Incremental Delivery

1. Deliver US1 to establish the normalized current-visualization dashboard for daily and weekly products.
2. Add US2 to preserve usability under missing history or uncertainty inputs.
3. Add US3 to harden fallback snapshots, unavailable states, and render-failure reporting.
4. Finish with Phase 6 traceability and performance verification.

### Parallel Team Strategy

1. One engineer can own migration/models/repositories in Phase 2.
2. One engineer can own backend visualization assembly while another owns frontend dashboard rendering in US1.
3. After US1, one engineer can implement degraded behavior for US2 while another implements fallback and render-failure handling for US3.

---

## Notes

- The task list preserves UC-05’s requirement to reuse UC-02 through UC-04 lineage instead of redefining forecast entities.
- Every user story phase is independently testable against the spec and `docs/UC-05-AT.md`.
- All tasks follow the required checklist format with task IDs, optional parallel markers, story labels where required, and exact file paths.
- `tasks.md` remains a planning checklist rather than a place to record execution results.
