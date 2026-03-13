# Tasks: Explore Historical 311 Demand Data

**Input**: Design documents from `/specs/007-historical-demand-exploration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/historical-demand-api.yaml, quickstart.md

**Tests**: Include backend unit, integration, contract, and frontend component or interaction tests because the plan and quickstart explicitly require acceptance-aligned verification for `docs/UC-07.md` and `docs/UC-07-AT.md`.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving the shared UC-02 historical-data lineage.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Path Conventions

- Backend implementation: `backend/app/`
- Backend tests: `backend/tests/`
- Frontend implementation: `frontend/src/`
- Database migrations: `backend/alembic/versions/`
- Planning artifacts: `specs/007-historical-demand-exploration/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the UC-07 backend and frontend scaffolding shared by all stories.

- [ ] T001 Create UC-07 backend scaffolding in `backend/app/api/routes/historical_demand.py`, `backend/app/repositories/historical_demand_repository.py`, `backend/app/schemas/historical_demand.py`, `backend/app/services/historical_demand_service.py`, `backend/app/services/historical_context_service.py`, and `backend/app/services/historical_warning_service.py`
- [ ] T002 Create UC-07 frontend scaffolding in `frontend/src/api/historicalDemand.ts`, `frontend/src/types/historicalDemand.ts`, `frontend/src/features/historical-demand/components/HistoricalDemandFilters.tsx`, `frontend/src/features/historical-demand/components/HistoricalDemandResults.tsx`, `frontend/src/features/historical-demand/components/HistoricalDemandStatus.tsx`, `frontend/src/features/historical-demand/hooks/useHistoricalDemand.ts`, and `frontend/src/pages/HistoricalDemandPage.tsx`
- [ ] T003 [P] Create UC-07 test scaffolding in `backend/tests/contract/test_historical_demand_api.py`, `backend/tests/integration/test_historical_demand_success.py`, `backend/tests/integration/test_historical_demand_warning.py`, `backend/tests/integration/test_historical_demand_failures.py`, `backend/tests/unit/test_historical_demand_service.py`, and `frontend/src/features/historical-demand/__tests__/HistoricalDemandPage.test.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared persistence, typed contracts, access control, and frontend plumbing required before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add migration-managed UC-07 tables for `HistoricalDemandAnalysisRequest`, `HistoricalDemandAnalysisResult`, `HistoricalDemandSummaryPoint`, and `HistoricalAnalysisOutcomeRecord` in `backend/alembic/versions/007_historical_demand_analysis.py`
- [ ] T005 [P] Define repository ORM models for UC-07 historical-analysis entities in `backend/app/repositories/models.py`
- [ ] T006 [P] Define typed backend request, context, warning, summary-point, and response schemas in `backend/app/schemas/historical_demand.py`
- [ ] T007 [P] Implement repository methods for analysis-request persistence, result persistence, summary-point persistence, and outcome-record retrieval in `backend/app/repositories/historical_demand_repository.py`
- [ ] T008 [P] Implement approved cleaned-dataset resolution and supported-filter metadata assembly using UC-02 lineage in `backend/app/services/historical_context_service.py`
- [ ] T009 [P] Implement authenticated historical-analysis access dependencies and role enforcement in `backend/app/api/dependencies/auth.py`
- [ ] T010 [P] Implement structured logging helpers for historical-demand success, warning, no-data, and failure outcomes in `backend/app/core/logging.py`
- [ ] T011 [P] Define shared frontend domain types and API payload adapters in `frontend/src/types/historicalDemand.ts` and `frontend/src/api/historicalDemand.ts`
- [ ] T012 Wire the historical-demand router into `backend/app/api/routes/historical_demand.py` and `backend/app/main.py`, and register the planner page in `frontend/src/App.tsx`

**Checkpoint**: Historical-analysis persistence, UC-02 lineage resolution, auth, logging, typed contracts, and frontend page wiring are in place.

---

## Phase 3: User Story 1 - Explore Historical Demand with Filters (Priority: P1) 🎯 MVP

**Goal**: Let a City Planner open the historical-demand interface, select valid filters, submit a request, and review matching historical demand patterns for planning analysis.

**Independent Test**: Open the historical-demand page, load available filter context, submit valid service-category, time-range, and supported geography filters, and confirm that matching historical summaries render clearly for review.

### Tests for User Story 1

- [ ] T013 [P] [US1] Add contract coverage for `GET /api/v1/historical-demand/context`, authenticated access, and successful `POST /api/v1/historical-demand/queries` behavior in `backend/tests/contract/test_historical_demand_api.py`
- [ ] T014 [P] [US1] Add backend unit coverage for filter normalization, approved-dataset lookup, and successful summary assembly in `backend/tests/unit/test_historical_demand_service.py`
- [ ] T015 [P] [US1] Add backend integration coverage for successful filtered retrieval, aggregation, and persistence in `backend/tests/integration/test_historical_demand_success.py`
- [ ] T016 [P] [US1] Add frontend interaction coverage for loading filters, submitting a valid request, and rendering returned historical summaries in `frontend/src/features/historical-demand/__tests__/HistoricalDemandPage.test.tsx`

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement historical filter-context retrieval and supported-geography exposure in `backend/app/services/historical_context_service.py`
- [ ] T018 [P] [US1] Implement historical-demand query execution, aggregation, and successful result persistence in `backend/app/services/historical_demand_service.py`
- [ ] T019 [P] [US1] Implement historical-demand context and query route handlers in `backend/app/api/routes/historical_demand.py`
- [ ] T020 [P] [US1] Implement frontend request orchestration and state management in `frontend/src/api/historicalDemand.ts` and `frontend/src/features/historical-demand/hooks/useHistoricalDemand.ts`
- [ ] T021 [P] [US1] Implement filter controls and result rendering components in `frontend/src/features/historical-demand/components/HistoricalDemandFilters.tsx` and `frontend/src/features/historical-demand/components/HistoricalDemandResults.tsx`
- [ ] T022 [US1] Implement the planner-facing historical-demand page composition in `frontend/src/pages/HistoricalDemandPage.tsx`

**Checkpoint**: User Story 1 delivers a complete historical-demand exploration flow for valid filtered requests.

---

## Phase 4: User Story 2 - Review Historical Trends Across Different Slices (Priority: P2)

**Goal**: Let a City Planner compare historical trends across valid service-category, time-range, and reliable-geography slices, including a warning before exceptionally large requests are executed.

**Independent Test**: Apply multiple valid filter combinations, confirm the displayed summaries change to match the selected slice, and confirm exceptionally large requests show a warning before retrieval and proceed only after acknowledgement.

### Tests for User Story 2

- [ ] T023 [P] [US2] Add contract coverage for high-volume warning metadata, declined warned requests, and acknowledged large-request execution in `backend/tests/contract/test_historical_demand_api.py`
- [ ] T024 [P] [US2] Add backend unit coverage for aggregation-granularity selection, supported-geography enforcement, and high-volume warning detection in `backend/tests/unit/test_historical_demand_service.py`
- [ ] T025 [P] [US2] Add backend integration coverage for declined warned requests, acknowledged large requests, and updated slice-specific summaries in `backend/tests/integration/test_historical_demand_warning.py`
- [ ] T026 [P] [US2] Extend frontend interaction coverage for changing filter combinations, declining high-volume warnings, and acknowledging high-volume warnings in `frontend/src/features/historical-demand/__tests__/HistoricalDemandPage.test.tsx`

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement high-volume request detection and warning decision logic in `backend/app/services/historical_warning_service.py`
- [ ] T028 [P] [US2] Extend historical-demand aggregation to select planning-friendly summary granularity for different valid slices in `backend/app/services/historical_demand_service.py`
- [ ] T029 [P] [US2] Persist warning state and acknowledgement details for executed large requests in `backend/app/repositories/historical_demand_repository.py`
- [ ] T030 [P] [US2] Extend backend response schemas for warning metadata, selected filters, and aggregation granularity in `backend/app/schemas/historical_demand.py`
- [ ] T031 [P] [US2] Implement warning state presentation plus decline-or-acknowledgement flow in `frontend/src/features/historical-demand/components/HistoricalDemandStatus.tsx` and `frontend/src/features/historical-demand/hooks/useHistoricalDemand.ts`
- [ ] T032 [US2] Extend `frontend/src/features/historical-demand/components/HistoricalDemandResults.tsx` and `frontend/src/pages/HistoricalDemandPage.tsx` to refresh displayed summaries for each valid filter combination without losing selected filter context

**Checkpoint**: User Story 2 adds slice comparison and high-volume warning behavior without breaking the core US1 flow.

---

## Phase 5: User Story 3 - Receive Clear No-Data and Error States (Priority: P3)

**Goal**: Let a City Planner receive explicit no-data or error outcomes, preserve the selected filter context, and avoid misleading partial results when retrieval or rendering cannot complete.

**Independent Test**: Submit filters that produce no matches, force retrieval failure, and force rendering failure, then confirm the interface shows the correct state, preserves the selected filters, and records the terminal outcome.

### Tests for User Story 3

- [ ] T033 [P] [US3] Add contract coverage for `no_data`, `retrieval_failed`, and `render_failed` response behavior in `backend/tests/contract/test_historical_demand_api.py`
- [ ] T034 [P] [US3] Add backend unit coverage for terminal outcome selection, message generation, and filter-context preservation in `backend/tests/unit/test_historical_demand_service.py`
- [ ] T035 [P] [US3] Add backend integration coverage for no-data, retrieval-failure, and render-failure outcome recording in `backend/tests/integration/test_historical_demand_failures.py`
- [ ] T036 [P] [US3] Extend frontend interaction coverage for no-data and error-state rendering with preserved filters in `frontend/src/features/historical-demand/__tests__/HistoricalDemandPage.test.tsx`

### Implementation for User Story 3

- [ ] T037 [P] [US3] Implement terminal no-data, retrieval-failure, and render-failure handling in `backend/app/services/historical_demand_service.py`
- [ ] T038 [P] [US3] Implement outcome-record persistence and filter-context retention for failed or empty requests in `backend/app/repositories/historical_demand_repository.py`
- [ ] T039 [P] [US3] Implement explicit frontend no-data and error-state presentation in `frontend/src/features/historical-demand/components/HistoricalDemandStatus.tsx`
- [ ] T040 [US3] Extend `frontend/src/pages/HistoricalDemandPage.tsx` and `frontend/src/features/historical-demand/hooks/useHistoricalDemand.ts` to preserve selected filters across warning, no-data, and error outcomes without displaying partial results

**Checkpoint**: User Story 3 completes clear no-data and error behavior with preserved filter context and recorded outcomes.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish acceptance traceability, contract examples, and cross-story performance and checklist alignment.

- [ ] T041 [P] Align implementation verification steps with `docs/UC-07.md` and `docs/UC-07-AT.md` in `specs/007-historical-demand-exploration/quickstart.md`
- [ ] T042 [P] Add performance assertions for SC-001 through SC-005 in `backend/tests/integration/test_historical_demand_success.py`, `backend/tests/integration/test_historical_demand_warning.py`, and `backend/tests/integration/test_historical_demand_failures.py`
- [ ] T043 [P] Align request and response examples for warning, no-data, and error outcomes in `specs/007-historical-demand-exploration/contracts/historical-demand-api.yaml`
- [ ] T044 Review and resolve remaining unchecked requirement-quality items in `specs/007-historical-demand-exploration/checklists/api-data-security-performance.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: US1**: Depends on Phase 2.
- **Phase 4: US2**: Depends on Phase 2 and on the US1 request or response foundations.
- **Phase 5: US3**: Depends on Phase 2 and on the US1 query lifecycle foundations.
- **Phase 6: Polish**: Depends on completion of the user stories being shipped.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories; this is the MVP.
- **US2 (P2)**: Depends on US1 filter context, response shaping, and frontend page foundations; it remains independently testable once those shared pieces exist.
- **US3 (P3)**: Depends on US1 query lifecycle and page state foundations; it can proceed independently of US2.

### Within Each User Story

- Test tasks should be completed before or alongside implementation and must fail before implementation is considered complete.
- Backend context and repository behavior precede route finalization.
- Backend response shaping precedes frontend rendering updates.
- Terminal outcome persistence precedes final frontend state handling.

### Dependency Graph

`Setup -> Foundational -> US1 -> {US2, US3} -> Polish`

---

## Parallel Opportunities

- Phase 1: T003 can run while T001-T002 are in progress.
- Phase 2: T005-T011 are parallelizable after T004 if migration naming must be settled first.
- US1: T013-T016 can run in parallel; T017-T021 can run in parallel before T022.
- US2: T023-T026 can run in parallel; T027-T031 can run in parallel before T032.
- US3: T033-T036 can run in parallel; T037-T039 can run in parallel before T040.
- US2 and US3 can run in parallel after US1 is complete.

## Parallel Example: User Story 1

```bash
Task: "Add contract coverage for historical-demand context and successful query behavior in backend/tests/contract/test_historical_demand_api.py"
Task: "Add backend unit coverage for filter normalization, approved-dataset lookup, and successful summary assembly in backend/tests/unit/test_historical_demand_service.py"
Task: "Add backend integration coverage for successful filtered retrieval and persistence in backend/tests/integration/test_historical_demand_success.py"
Task: "Add frontend interaction coverage for loading filters, submitting a valid request, and rendering summaries in frontend/src/features/historical-demand/__tests__/HistoricalDemandPage.test.tsx"

Task: "Implement historical filter-context retrieval in backend/app/services/historical_context_service.py"
Task: "Implement historical-demand query execution and aggregation in backend/app/services/historical_demand_service.py"
Task: "Implement frontend request orchestration and state management in frontend/src/api/historicalDemand.ts and frontend/src/features/historical-demand/hooks/useHistoricalDemand.ts"
Task: "Implement filter controls and result rendering components in frontend/src/features/historical-demand/components/HistoricalDemandFilters.tsx and frontend/src/features/historical-demand/components/HistoricalDemandResults.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract coverage for high-volume warning metadata, declined warned requests, and acknowledged execution in backend/tests/contract/test_historical_demand_api.py"
Task: "Add backend unit coverage for aggregation-granularity selection, geography enforcement, and warning detection in backend/tests/unit/test_historical_demand_service.py"
Task: "Add backend integration coverage for declined warned requests, acknowledged execution, and updated slice-specific summaries in backend/tests/integration/test_historical_demand_warning.py"
Task: "Extend frontend interaction coverage for changing filter combinations, declining warnings, and acknowledging warnings in frontend/src/features/historical-demand/__tests__/HistoricalDemandPage.test.tsx"

Task: "Implement high-volume request detection in backend/app/services/historical_warning_service.py"
Task: "Extend historical-demand aggregation for different valid slices in backend/app/services/historical_demand_service.py"
Task: "Persist warning state and acknowledgement details in backend/app/repositories/historical_demand_repository.py"
Task: "Implement warning state presentation plus decline-or-acknowledgement flow in frontend/src/features/historical-demand/components/HistoricalDemandStatus.tsx and frontend/src/features/historical-demand/hooks/useHistoricalDemand.ts"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract coverage for no_data, retrieval_failed, and render_failed responses in backend/tests/contract/test_historical_demand_api.py"
Task: "Add backend unit coverage for terminal outcome selection and filter-context preservation in backend/tests/unit/test_historical_demand_service.py"
Task: "Add backend integration coverage for no-data and failure outcome recording in backend/tests/integration/test_historical_demand_failures.py"
Task: "Extend frontend interaction coverage for no-data and error states in frontend/src/features/historical-demand/__tests__/HistoricalDemandPage.test.tsx"

Task: "Implement terminal no-data, retrieval-failure, and render-failure handling in backend/app/services/historical_demand_service.py"
Task: "Implement outcome-record persistence and filter-context retention in backend/app/repositories/historical_demand_repository.py"
Task: "Implement explicit frontend no-data and error-state presentation in frontend/src/features/historical-demand/components/HistoricalDemandStatus.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3.
4. Validate successful filtered historical-demand retrieval and display before expanding scope.

### Incremental Delivery

1. Deliver US1 to establish the core historical-demand exploration flow.
2. Add US2 to support trend comparison across slices and warned large-request handling.
3. Add US3 to harden no-data and failure behavior.
4. Finish with Phase 6 traceability and remaining checklist cleanup.

### Parallel Team Strategy

1. One engineer can own migrations, models, and repositories in Phase 2.
2. One engineer can own backend services and contracts while another owns frontend types, hooks, and components in US1.
3. After US1, one engineer can implement warning and slice behavior for US2 while another implements no-data and error handling for US3.

---

## Notes

- The task list preserves UC-07’s requirement to reuse the approved cleaned dataset lineage from UC-02 instead of redefining upstream historical-data entities.
- Every user story phase is independently testable against the UC-07 spec, `docs/UC-07.md`, and `docs/UC-07-AT.md`.
- All tasks follow the required checklist format with task IDs, optional parallel markers, story labels where required, and exact file paths.
- `tasks.md` remains a planning checklist rather than a place to record execution results.
