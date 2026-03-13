# Tasks: Evaluate Forecasting Engine Against Baselines

**Input**: Design documents from `/specs/006-evaluate-forecast-baselines/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/evaluation-api.yaml, quickstart.md

**Tests**: Include backend unit, integration, contract, and acceptance-aligned tests because the plan and quickstart explicitly require verification against `docs/UC-06-AT.md`.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving the constitution-aligned UC-06 backend scope.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Path Conventions

- Backend implementation: `backend/app/`
- Backend tests: `backend/tests/`
- Database migrations: `backend/alembic/versions/`
- Planning artifacts: `specs/006-evaluate-forecast-baselines/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the UC-06 evaluation scaffolding shared by all stories.

- [ ] T001 Create UC-06 backend scaffolding in `backend/app/api/routes/evaluations.py`, `backend/app/repositories/evaluation_repository.py`, `backend/app/schemas/evaluation.py`, `backend/app/services/evaluation_service.py`, `backend/app/services/baseline_service.py`, and `backend/app/services/evaluation_scope_service.py`
- [ ] T002 Configure evaluation-specific settings for forecast-product defaults, baseline labels, and evaluation scheduling in `backend/app/core/config.py`
- [ ] T003 [P] Create UC-06 test scaffolding in `backend/tests/contract/test_evaluation_api.py`, `backend/tests/integration/test_evaluation_success.py`, `backend/tests/integration/test_evaluation_failures.py`, `backend/tests/integration/test_evaluation_partial.py`, and `backend/tests/unit/test_evaluation_service.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared persistence, routing, authorization, and fair-comparison infrastructure required before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add migration-managed UC-06 tables for `EvaluationRun`, `EvaluationResult`, `EvaluationSegment`, `MetricComparisonValue`, and `CurrentEvaluationMarker` in `backend/alembic/versions/006_evaluation_lifecycle.py`
- [ ] T005 [P] Define repository ORM models for UC-06 evaluation entities in `backend/app/repositories/models.py`
- [ ] T006 [P] Define typed backend schemas for evaluation-trigger, run-status, current-result, and segment payloads in `backend/app/schemas/evaluation.py`
- [ ] T007 [P] Implement repository methods for evaluation runs, stored results, segment metrics, current-marker updates, and historical-result retrieval in `backend/app/repositories/evaluation_repository.py`
- [ ] T008 [P] Implement forecast-product source resolution for UC-03 daily lineage and UC-04 weekly lineage in `backend/app/services/evaluation_scope_service.py`
- [ ] T009 [P] Implement fair-comparison window and segment-alignment helpers in `backend/app/services/evaluation_scope_service.py`
- [ ] T010 [P] Implement authenticated evaluation access dependencies and role enforcement in `backend/app/api/dependencies/auth.py`
- [ ] T011 [P] Implement structured logging helpers for evaluation success, partial success, and failure outcomes in `backend/app/core/logging.py`
- [ ] T012 Wire the evaluation router into the backend application in `backend/app/api/routes/evaluations.py` and `backend/app/main.py`

**Checkpoint**: Evaluation persistence, source resolution, auth, typed contracts, and route wiring are in place.

---

## Phase 3: User Story 1 - Review Whether the Forecasting Engine Beats Baselines (Priority: P1) 🎯 MVP

**Goal**: Let a City Planner run or retrieve a completed evaluation that compares the forecasting engine against `seasonal_naive` and `moving_average` baselines for one forecast product and stores reviewable results.

**Independent Test**: Trigger an evaluation with valid actuals, current forecast outputs, and baseline generation available, then confirm that stored results expose engine and baseline metrics for the selected daily or weekly forecast product.

### Tests for User Story 1

- [ ] T013 [P] [US1] Add contract coverage for `POST /api/v1/evaluation-runs/trigger`, `GET /api/v1/evaluation-runs/{evaluationRunId}`, and `GET /api/v1/evaluations/current` success, auth failure, and request-validation behavior in `backend/tests/contract/test_evaluation_api.py`
- [ ] T014 [P] [US1] Add backend unit coverage for daily-vs-weekly source resolution, baseline generation orchestration, and MAE/RMSE/MAPE calculation in `backend/tests/unit/test_evaluation_service.py`
- [ ] T015 [P] [US1] Add integration coverage for successful on-demand and scheduled evaluation runs with stored results in `backend/tests/integration/test_evaluation_success.py`

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement baseline generation for `seasonal_naive` and `moving_average` in `backend/app/services/baseline_service.py`
- [ ] T017 [P] [US1] Implement metric-calculation utilities for MAE, RMSE, and MAPE in `backend/app/services/evaluation_metrics.py`
- [ ] T018 [P] [US1] Implement evaluation-result assembly for overall metrics, baseline coverage, comparison-summary generation, and stored-result persistence in `backend/app/services/evaluation_service.py`
- [ ] T019 [US1] Implement on-demand and scheduled evaluation orchestration for one forecast product at a time in `backend/app/services/evaluation_service.py`
- [ ] T020 [US1] Implement trigger and run-status API handling with thin route logic in `backend/app/api/routes/evaluations.py`
- [ ] T021 [US1] Implement current official evaluation retrieval with fair-comparison metadata and comparison-summary exposure in `backend/app/api/routes/evaluations.py`

**Checkpoint**: User Story 1 delivers a complete evaluation workflow with reviewable stored results for one selected forecast product.

---

## Phase 4: User Story 2 - Understand Performance by Category and Time Window (Priority: P2)

**Goal**: Let a City Planner review overall, service-category, and time-period evaluation summaries, including explicit exclusions when only some metrics are invalid.

**Independent Test**: Complete an evaluation spanning multiple categories and time windows, then confirm the stored result includes segmented summaries and marks a segment partial when one metric is excluded.

### Tests for User Story 2

- [ ] T022 [P] [US2] Add contract coverage for segmented current-evaluation responses and partial-result payload structure in `backend/tests/contract/test_evaluation_api.py`
- [ ] T023 [P] [US2] Add backend unit coverage for category aggregation, time-period aggregation, and exclusion labeling in `backend/tests/unit/test_evaluation_service.py`
- [ ] T024 [P] [US2] Add integration coverage for segmented evaluation results and metric-exclusion persistence in `backend/tests/integration/test_evaluation_partial.py`

### Implementation for User Story 2

- [ ] T025 [P] [US2] Implement category and time-period segment construction in `backend/app/services/evaluation_segments.py`
- [ ] T026 [P] [US2] Implement partial-result handling and exclusion-reason population for invalid metrics in `backend/app/services/evaluation_service.py`
- [ ] T027 [P] [US2] Implement repository persistence for `EvaluationSegment` and `MetricComparisonValue` records in `backend/app/repositories/evaluation_repository.py`
- [ ] T028 [US2] Extend current-evaluation response shaping to include segmented summaries and exclusion details in `backend/app/schemas/evaluation.py` and `backend/app/api/routes/evaluations.py`

**Checkpoint**: User Story 2 adds category/time segmentation and partial-result visibility without changing User Story 1 success-path behavior.

---

## Phase 5: User Story 3 - Preserve the Last Reliable Evaluation When Failures Occur (Priority: P3)

**Goal**: Preserve the prior official evaluation when missing data, missing forecast outputs, baseline failures, or storage failures prevent a new official result from being published.

**Independent Test**: Force each failure class and confirm that the run is recorded as failed, no new official marker is activated, and the previous current evaluation remains retrievable.

### Tests for User Story 3

- [ ] T029 [P] [US3] Add contract coverage for failed run statuses, missing current evaluation, and access-denial separation from business failures in `backend/tests/contract/test_evaluation_api.py`
- [ ] T030 [P] [US3] Add backend unit coverage for missing-input, missing-forecast, baseline-failure, and storage-failure outcome selection in `backend/tests/unit/test_evaluation_service.py`
- [ ] T031 [P] [US3] Add integration coverage for previous-result retention across all UC-06 failure paths in `backend/tests/integration/test_evaluation_failures.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement missing-data and missing-forecast guardrails that fail the run before publication in `backend/app/services/evaluation_scope_service.py` and `backend/app/services/evaluation_service.py`
- [ ] T033 [P] [US3] Implement baseline-generation failure handling and failure-reason recording in `backend/app/services/baseline_service.py` and `backend/app/services/evaluation_service.py`
- [ ] T034 [P] [US3] Implement storage-failure handling that preserves the prior `CurrentEvaluationMarker` in `backend/app/repositories/evaluation_repository.py`
- [ ] T035 [US3] Implement last-known-good official-result activation rules and failure-safe current-marker preservation in `backend/app/services/evaluation_service.py`

**Checkpoint**: User Story 3 completes failure-safe retention and official-result preservation across all defined failure classes.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish acceptance traceability, checklist-driven requirement cleanup, and cross-story verification support.

- [ ] T036 [P] Align implementation verification steps with `docs/UC-06-AT.md` in `specs/006-evaluate-forecast-baselines/quickstart.md`
- [ ] T037 [P] Add performance and official-result-retention assertions for SC-001 through SC-005 in `backend/tests/integration/test_evaluation_success.py`, `backend/tests/integration/test_evaluation_partial.py`, and `backend/tests/integration/test_evaluation_failures.py`
- [ ] T038 [P] Align request/response examples and fair-comparison payload documentation in `specs/006-evaluate-forecast-baselines/contracts/evaluation-api.yaml`
- [ ] T039 Review and resolve remaining unchecked requirement-quality items in `specs/006-evaluate-forecast-baselines/checklists/api-data-security-performance.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: US1**: Depends on Phase 2.
- **Phase 4: US2**: Depends on Phase 2 and on US1 evaluation-result assembly foundations.
- **Phase 5: US3**: Depends on Phase 2 and on US1 run/result lifecycle foundations.
- **Phase 6: Polish**: Depends on completion of the user stories being shipped.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories; this is the MVP.
- **US2 (P2)**: Depends on US1 stored-result and response-shaping foundations; it remains independently testable once those shared pieces exist.
- **US3 (P3)**: Depends on US1 run lifecycle and current-marker foundations; it can proceed independently of US2.

### Within Each User Story

- Test tasks should be completed before or alongside implementation and must fail before implementation is considered complete.
- Source-resolution and metric utilities precede orchestration.
- Orchestration precedes route finalization.
- Persistence updates precede official-marker activation.

### Dependency Graph

`Setup -> Foundational -> US1 -> {US2, US3} -> Polish`

---

## Parallel Opportunities

- Phase 1: T003 can run while T001-T002 are in progress.
- Phase 2: T005-T011 are parallelizable after T004 if migration naming must be settled first.
- US1: T013-T015 can run in parallel; T016-T018 can run in parallel before T019-T021.
- US2: T022-T024 can run in parallel; T025-T027 can run in parallel before T028.
- US3: T029-T031 can run in parallel; T032-T034 can run in parallel before T035.
- US2 and US3 can run in parallel after US1 is complete.

## Parallel Example: User Story 1

```bash
Task: "Add contract coverage for evaluation trigger, run status, and current evaluation retrieval in backend/tests/contract/test_evaluation_api.py"
Task: "Add backend unit coverage for source resolution, baseline generation orchestration, and metric calculation in backend/tests/unit/test_evaluation_service.py"
Task: "Add integration coverage for successful on-demand and scheduled evaluation runs in backend/tests/integration/test_evaluation_success.py"

Task: "Implement baseline generation for seasonal_naive and moving_average in backend/app/services/baseline_service.py"
Task: "Implement metric-calculation utilities for MAE, RMSE, and MAPE in backend/app/services/evaluation_metrics.py"
Task: "Implement evaluation-result assembly for overall metrics and persistence in backend/app/services/evaluation_service.py"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract coverage for segmented current-evaluation responses in backend/tests/contract/test_evaluation_api.py"
Task: "Add backend unit coverage for category aggregation, time-period aggregation, and exclusion labeling in backend/tests/unit/test_evaluation_service.py"
Task: "Add integration coverage for segmented evaluation results and metric-exclusion persistence in backend/tests/integration/test_evaluation_partial.py"

Task: "Implement category and time-period segment construction in backend/app/services/evaluation_segments.py"
Task: "Implement partial-result handling and exclusion-reason population in backend/app/services/evaluation_service.py"
Task: "Implement repository persistence for EvaluationSegment and MetricComparisonValue records in backend/app/repositories/evaluation_repository.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract coverage for failed run statuses and current-result retention behavior in backend/tests/contract/test_evaluation_api.py"
Task: "Add backend unit coverage for missing-input, missing-forecast, baseline-failure, and storage-failure outcomes in backend/tests/unit/test_evaluation_service.py"
Task: "Add integration coverage for previous-result retention across all UC-06 failure paths in backend/tests/integration/test_evaluation_failures.py"

Task: "Implement missing-data and missing-forecast guardrails in backend/app/services/evaluation_scope_service.py"
Task: "Implement baseline-generation failure handling in backend/app/services/baseline_service.py"
Task: "Implement storage-failure handling that preserves the prior CurrentEvaluationMarker in backend/app/repositories/evaluation_repository.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3.
4. Validate successful evaluation triggering, storage, and current-result retrieval before expanding scope.

### Incremental Delivery

1. Deliver US1 to establish the stored evaluation workflow and planner-facing retrieval.
2. Add US2 to expose segmented summaries and partial-result exclusions.
3. Add US3 to harden failure handling and last-known-good retention.
4. Finish with Phase 6 traceability and remaining checklist cleanup.

### Parallel Team Strategy

1. One engineer can own migrations/models/repositories in Phase 2.
2. One engineer can own source resolution and baseline/metric services while another owns API schemas/routes in US1.
3. After US1, one engineer can implement segmented results for US2 while another implements failure retention for US3.

---

## Notes

- The task list preserves UC-06’s requirement to reuse UC-02 through UC-04 lineage instead of redefining forecast or dataset entities.
- Every user story phase is independently testable against the spec and `docs/UC-06-AT.md`.
- All tasks follow the required checklist format with task IDs, optional parallel markers, story labels where required, and exact file paths.
- `tasks.md` remains a planning checklist rather than a place to record execution results.
