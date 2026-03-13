# Tasks: Compare Demand and Forecasts Across Categories and Geographies

**Input**: Design documents from `/root/311-forecast-system/specs/008-compare-demand-forecasts/`
**Prerequisites**: [plan.md](/root/311-forecast-system/specs/008-compare-demand-forecasts/plan.md), [spec.md](/root/311-forecast-system/specs/008-compare-demand-forecasts/spec.md), [research.md](/root/311-forecast-system/specs/008-compare-demand-forecasts/research.md), [data-model.md](/root/311-forecast-system/specs/008-compare-demand-forecasts/data-model.md), [demand-comparison-api.yaml](/root/311-forecast-system/specs/008-compare-demand-forecasts/contracts/demand-comparison-api.yaml), [quickstart.md](/root/311-forecast-system/specs/008-compare-demand-forecasts/quickstart.md)

**Tests**: Include backend contract, unit, and integration coverage plus frontend component and interaction tests because the plan and quickstart explicitly require acceptance-aligned verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the backend/frontend skeleton and tooling entry points required by the implementation plan.

- [ ] T001 Create backend and frontend source skeleton directories under `/root/311-forecast-system/backend/app/` and `/root/311-forecast-system/frontend/src/`
- [ ] T002 Create Python package entry points for `/root/311-forecast-system/backend/app/api/`, `/root/311-forecast-system/backend/app/core/`, `/root/311-forecast-system/backend/app/repositories/`, `/root/311-forecast-system/backend/app/schemas/`, and `/root/311-forecast-system/backend/app/services/`
- [ ] T003 [P] Create backend test package directories in `/root/311-forecast-system/backend/tests/unit/`, `/root/311-forecast-system/backend/tests/integration/`, and `/root/311-forecast-system/backend/tests/contract/`
- [ ] T004 [P] Create frontend feature directories in `/root/311-forecast-system/frontend/src/api/`, `/root/311-forecast-system/frontend/src/features/demand-comparisons/`, `/root/311-forecast-system/frontend/src/components/`, and `/root/311-forecast-system/frontend/src/types/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared contract, persistence, service, auth, and frontend wiring that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Create comparison domain enums and shared typed models in `/root/311-forecast-system/backend/app/schemas/demand_comparison_models.py`
- [ ] T006 [P] Implement comparison authentication and ownership dependencies in `/root/311-forecast-system/backend/app/api/dependencies/auth.py`
- [ ] T007 [P] Implement comparison repository interfaces for requests, results, missing combinations, and outcome records in `/root/311-forecast-system/backend/app/repositories/demand_comparison_repository.py`
- [ ] T008 [P] Implement upstream lineage lookup interfaces for approved historical and active forecast markers in `/root/311-forecast-system/backend/app/repositories/demand_lineage_repository.py`
- [ ] T009 Implement forecast source selection and comparison granularity rules in `/root/311-forecast-system/backend/app/services/demand_comparison_source_resolution.py`
- [ ] T010 Implement shared outcome vocabulary and terminal-outcome mapping logic in `/root/311-forecast-system/backend/app/services/demand_comparison_outcomes.py`
- [ ] T011 [P] Implement backend request/response schemas from `/root/311-forecast-system/specs/008-compare-demand-forecasts/contracts/demand-comparison-api.yaml` in `/root/311-forecast-system/backend/app/schemas/demand_comparison_api.py`
- [ ] T012 [P] Create frontend API client and shared response discriminators in `/root/311-forecast-system/frontend/src/api/demandComparisons.ts`
- [ ] T013 [P] Create frontend domain types for filters, outcomes, warnings, and render events in `/root/311-forecast-system/frontend/src/types/demandComparisons.ts`
- [ ] T014 Implement comparison router shell for context, query, and render-event endpoints in `/root/311-forecast-system/backend/app/api/routes/demand_comparisons.py`
- [ ] T015 [P] Implement comparison observability helpers for structured lifecycle and outcome logging in `/root/311-forecast-system/backend/app/core/demand_comparison_observability.py`

**Checkpoint**: Foundation ready. User stories can now proceed in priority order or in parallel if staffed.

---

## Phase 3: User Story 1 - Compare selected categories and regions (Priority: P1) 🎯 MVP

**Goal**: Let a city planner request a comparison for selected categories, optional geographies, and a time range, then view a normalized historical/forecast result for the requested scope.

**Independent Test**: Submit a comparison for one or more categories with optional geographies and a continuous time range, then confirm the returned comparison matches only the selected scope and the frontend replaces any older result with the new request state and final response.

### Tests for User Story 1

- [ ] T016 [P] [US1] Add contract tests for context and successful comparison responses in `/root/311-forecast-system/backend/tests/contract/test_demand_comparison_queries.py`
- [ ] T017 [P] [US1] Add unit tests for source-selection and allowable granularity rules in `/root/311-forecast-system/backend/tests/unit/test_demand_comparison_source_resolution.py`
- [ ] T018 [P] [US1] Add integration tests for successful scoped comparison execution in `/root/311-forecast-system/backend/tests/integration/test_demand_comparison_success.py`
- [ ] T019 [P] [US1] Add frontend interaction tests for filter selection and result replacement in `/root/311-forecast-system/frontend/src/features/demand-comparisons/__tests__/DemandComparisonPage.test.tsx`
- [ ] T020 [P] [US1] Add integration tests for request lifecycle logging in `/root/311-forecast-system/backend/tests/integration/test_demand_comparison_request_logging.py`

### Implementation for User Story 1

- [ ] T021 [P] [US1] Implement comparison context service for service-category and optional geography filter metadata in `/root/311-forecast-system/backend/app/services/demand_comparison_context_service.py`
- [ ] T022 [P] [US1] Implement comparison result assembler for normalized chart/table payloads in `/root/311-forecast-system/backend/app/services/demand_comparison_result_builder.py`
- [ ] T023 [US1] Implement comparison execution service for successful scoped retrieval, alignment, and lifecycle logging in `/root/311-forecast-system/backend/app/services/demand_comparison_service.py`
- [ ] T024 [US1] Wire context and comparison query handlers to the service layer in `/root/311-forecast-system/backend/app/api/routes/demand_comparisons.py`
- [ ] T025 [P] [US1] Implement frontend filter form for multi-category, optional multi-geography, and continuous time-range selection in `/root/311-forecast-system/frontend/src/features/demand-comparisons/components/ComparisonFilters.tsx`
- [ ] T026 [P] [US1] Implement frontend comparison result view for normalized chart/table rendering in `/root/311-forecast-system/frontend/src/features/demand-comparisons/components/ComparisonResultView.tsx`
- [ ] T027 [US1] Implement demand comparison page state management and result replacement behavior in `/root/311-forecast-system/frontend/src/pages/DemandComparisonPage.tsx`

**Checkpoint**: User Story 1 delivers the MVP comparison workflow and is independently testable.

---

## Phase 4: User Story 2 - Continue with large comparison requests (Priority: P2)

**Goal**: Warn planners before high-volume comparison retrieval begins and allow them to continue explicitly.

**Independent Test**: Submit a request over the high-volume threshold, confirm the response is `warning_required` with the required message content before retrieval starts, then proceed and receive the normal comparison flow.

### Tests for User Story 2

- [ ] T028 [P] [US2] Add contract tests for `warning_required` request/response semantics in `/root/311-forecast-system/backend/tests/contract/test_demand_comparison_warnings.py`
- [ ] T029 [P] [US2] Add unit tests for high-volume threshold and warning message construction in `/root/311-forecast-system/backend/tests/unit/test_demand_comparison_warnings.py`
- [ ] T030 [P] [US2] Add integration tests for warning acknowledgment and resumed execution in `/root/311-forecast-system/backend/tests/integration/test_demand_comparison_warnings.py`
- [ ] T031 [P] [US2] Add frontend interaction tests for warning display and proceed-after-warning flow in `/root/311-forecast-system/frontend/src/features/demand-comparisons/__tests__/DemandComparisonWarning.test.tsx`
- [ ] T032 [P] [US2] Add integration tests for high-volume warning logging in `/root/311-forecast-system/backend/tests/integration/test_demand_comparison_warning_logging.py`

### Implementation for User Story 2

- [ ] T033 [P] [US2] Implement large-request threshold detection and warning payload builder in `/root/311-forecast-system/backend/app/services/demand_comparison_warning_service.py`
- [ ] T034 [US2] Integrate warning gating and warning logging into comparison execution before retrieval begins in `/root/311-forecast-system/backend/app/services/demand_comparison_service.py`
- [ ] T035 [US2] Persist warning status and acknowledgment outcomes in `/root/311-forecast-system/backend/app/repositories/demand_comparison_repository.py`
- [ ] T036 [P] [US2] Implement frontend warning dialog with required scope and delay messaging in `/root/311-forecast-system/frontend/src/features/demand-comparisons/components/ComparisonWarningDialog.tsx`
- [ ] T037 [US2] Connect warning acknowledgment flow to query re-submission in `/root/311-forecast-system/frontend/src/pages/DemandComparisonPage.tsx`

**Checkpoint**: User Story 2 adds the explicit high-volume warning gate without changing the MVP comparison behavior.

---

## Phase 5: User Story 3 - Understand incomplete or failed comparisons (Priority: P3)

**Goal**: Show clear partial-result and failure outcomes for missing data, retrieval failures, alignment failures, and render failures.

**Independent Test**: Trigger forecast-only, historical-only, partial-forecast-missing, historical retrieval failure, forecast retrieval failure, alignment failure, and render failure cases, then confirm each produces the exact contract outcome and visible state required by the spec.

### Tests for User Story 3

- [ ] T038 [P] [US3] Add contract tests for partial-result and failure outcome responses in `/root/311-forecast-system/backend/tests/contract/test_demand_comparison_outcomes.py`
- [ ] T039 [P] [US3] Add unit tests for outcome classification and failure separation in `/root/311-forecast-system/backend/tests/unit/test_demand_comparison_outcomes.py`
- [ ] T040 [P] [US3] Add integration tests for historical-only, forecast-only, partial-forecast-missing, retrieval failure, and alignment failure paths in `/root/311-forecast-system/backend/tests/integration/test_demand_comparison_failures.py`
- [ ] T041 [P] [US3] Add frontend interaction tests for partial-result, error-state, and render-failure reporting behavior in `/root/311-forecast-system/frontend/src/features/demand-comparisons/__tests__/DemandComparisonFailureStates.test.tsx`
- [ ] T042 [P] [US3] Add integration tests for missing-data, retrieval-failure, alignment-failure, and render-failure logging in `/root/311-forecast-system/backend/tests/integration/test_demand_comparison_failure_logging.py`

### Implementation for User Story 3

- [ ] T043 [P] [US3] Implement persistence models and repository mapping for missing combinations and terminal outcome records in `/root/311-forecast-system/backend/app/repositories/demand_comparison_repository.py`
- [ ] T044 [US3] Extend comparison execution service to return `historical_only`, `forecast_only`, `partial_forecast_missing`, `historical_retrieval_failed`, `forecast_retrieval_failed`, and `alignment_failed` outcomes with explicit outcome logging in `/root/311-forecast-system/backend/app/services/demand_comparison_service.py`
- [ ] T045 [P] [US3] Implement render-event recording service with request-ownership enforcement and render-failure logging in `/root/311-forecast-system/backend/app/services/demand_comparison_render_service.py`
- [ ] T046 [US3] Wire render-event endpoint acceptance and authorization checks in `/root/311-forecast-system/backend/app/api/routes/demand_comparisons.py`
- [ ] T047 [P] [US3] Implement frontend partial-result and explicit error-state components in `/root/311-forecast-system/frontend/src/features/demand-comparisons/components/ComparisonOutcomeState.tsx`
- [ ] T048 [US3] Report frontend render success/failure outcomes through the render-event API in `/root/311-forecast-system/frontend/src/pages/DemandComparisonPage.tsx`

**Checkpoint**: All required UC-08 outcomes are independently testable and distinguishable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish documentation, acceptance coverage, and cross-story consistency checks.

- [ ] T049 [P] Add timing instrumentation for request submission-to-terminal-outcome measurement in `/root/311-forecast-system/backend/app/services/demand_comparison_service.py`
- [ ] T050 [P] Add integration/performance verification for the 10-second normal-threshold target in `/root/311-forecast-system/backend/tests/integration/test_demand_comparison_performance.py`
- [ ] T051 [P] Add planner usability validation script and evidence template for SC-001 in `/root/311-forecast-system/specs/008-compare-demand-forecasts/usability-validation.md`
- [ ] T052 [P] Update backend/frontend implementation notes to match [quickstart.md](/root/311-forecast-system/specs/008-compare-demand-forecasts/quickstart.md) in `/root/311-forecast-system/specs/008-compare-demand-forecasts/quickstart.md`
- [ ] T053 [P] Add end-to-end acceptance traceability notes for UC-08 and UC-08-AT in `/root/311-forecast-system/specs/008-compare-demand-forecasts/plan.md`
- [ ] T054 Validate OpenAPI, typed schemas, frontend domain models, and frontend page wiring stay aligned with `/root/311-forecast-system/specs/008-compare-demand-forecasts/contracts/demand-comparison-api.yaml`
- [ ] T055 Run quickstart-aligned verification for contract, integration, frontend, observability, performance, and usability-validation tasks in `/root/311-forecast-system/specs/008-compare-demand-forecasts/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies; start immediately.
- **Phase 2: Foundational**: Depends on Phase 1; blocks all user stories.
- **Phase 3: User Story 1**: Depends on Phase 2; defines the MVP.
- **Phase 4: User Story 2**: Depends on Phase 2 and reuses US1 comparison execution flow.
- **Phase 5: User Story 3**: Depends on Phase 2 and builds on the shared execution and persistence surfaces.
- **Phase 6: Polish**: Depends on completion of the intended user stories.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational phase.
- **US2 (P2)**: Depends on shared comparison execution flow from Foundational phase and integrates with US1 page state.
- **US3 (P3)**: Depends on shared comparison execution flow from Foundational phase and integrates with US1 display surfaces.

### Within Each User Story

- Contract, unit, integration, and frontend tests should be written before the corresponding implementation tasks and should fail first.
- Backend services should be completed before route wiring that exposes them.
- Frontend state orchestration should follow API client and component creation.
- Each user story should be validated independently before moving to the next phase.

### Parallel Opportunities

- Phase 1 directory/package creation tasks marked `[P]` can run together.
- In Phase 2, auth, repositories, schemas, and frontend typed client tasks marked `[P]` can run in parallel once the skeleton exists.
- In each user story, test tasks marked `[P]` can run in parallel.
- Backend service/component tasks within a story marked `[P]` can run in parallel when they touch different files.
- US2 and US3 can be split across team members after Phase 2 if US1 page-state integration points are coordinated.

---

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for context and successful comparison responses in /root/311-forecast-system/backend/tests/contract/test_demand_comparison_queries.py"
Task: "Add unit tests for source-selection and allowable granularity rules in /root/311-forecast-system/backend/tests/unit/test_demand_comparison_source_resolution.py"
Task: "Add integration tests for successful scoped comparison execution in /root/311-forecast-system/backend/tests/integration/test_demand_comparison_success.py"
Task: "Add integration tests for request lifecycle logging in /root/311-forecast-system/backend/tests/integration/test_demand_comparison_request_logging.py"
```

```bash
Task: "Implement comparison context service for service-category and optional geography filter metadata in /root/311-forecast-system/backend/app/services/demand_comparison_context_service.py"
Task: "Implement comparison result assembler for normalized chart/table payloads in /root/311-forecast-system/backend/app/services/demand_comparison_result_builder.py"
Task: "Implement frontend filter form for multi-category, optional multi-geography, and continuous time-range selection in /root/311-forecast-system/frontend/src/features/demand-comparisons/components/ComparisonFilters.tsx"
Task: "Implement frontend comparison result view for normalized chart/table rendering in /root/311-forecast-system/frontend/src/features/demand-comparisons/components/ComparisonResultView.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract tests for warning_required request/response semantics in /root/311-forecast-system/backend/tests/contract/test_demand_comparison_warnings.py"
Task: "Add unit tests for high-volume threshold and warning message construction in /root/311-forecast-system/backend/tests/unit/test_demand_comparison_warnings.py"
Task: "Add integration tests for warning acknowledgment and resumed execution in /root/311-forecast-system/backend/tests/integration/test_demand_comparison_warnings.py"
Task: "Add integration tests for high-volume warning logging in /root/311-forecast-system/backend/tests/integration/test_demand_comparison_warning_logging.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract tests for partial-result and failure outcome responses in /root/311-forecast-system/backend/tests/contract/test_demand_comparison_outcomes.py"
Task: "Add unit tests for outcome classification and failure separation in /root/311-forecast-system/backend/tests/unit/test_demand_comparison_outcomes.py"
Task: "Add integration tests for historical-only, forecast-only, partial-forecast-missing, retrieval failure, and alignment failure paths in /root/311-forecast-system/backend/tests/integration/test_demand_comparison_failures.py"
Task: "Add integration tests for missing-data, retrieval-failure, alignment-failure, and render-failure logging in /root/311-forecast-system/backend/tests/integration/test_demand_comparison_failure_logging.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate successful scoped comparison execution and result replacement behavior before adding warning or failure flows.

### Incremental Delivery

1. Deliver US1 for the core planner comparison workflow.
2. Add US2 to gate high-volume requests before retrieval begins.
3. Add US3 to make all partial-result and failure paths explicit and acceptance-testable.
4. Finish with Phase 6 cross-cutting validation and artifact alignment.

### Parallel Team Strategy

1. One developer builds backend foundations while another prepares frontend typed client/types after Phase 1.
2. After Phase 2, one developer can own backend comparison services while another owns frontend comparison UI for US1.
3. US2 warning flow and US3 failure/render handling can proceed in parallel once the shared comparison service contract is stable.

---

## Notes

- All tasks follow the required checklist format with checkbox, task ID, optional parallel marker, required story label for story phases, and exact file path.
- Tests are included because the design artifacts explicitly call for contract, integration, unit, and frontend interaction coverage.
- The suggested MVP scope is **User Story 1** after Setup and Foundational phases.
