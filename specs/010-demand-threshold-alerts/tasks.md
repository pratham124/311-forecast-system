# Tasks: Demand Threshold Alerts

**Input**: Design documents from `/specs/010-demand-threshold-alerts/`
**Prerequisites**: [plan.md](/root/311-forecast-system/specs/010-demand-threshold-alerts/plan.md), [spec.md](/root/311-forecast-system/specs/010-demand-threshold-alerts/spec.md), [research.md](/root/311-forecast-system/specs/010-demand-threshold-alerts/research.md), [data-model.md](/root/311-forecast-system/specs/010-demand-threshold-alerts/data-model.md), [threshold-alerts-api.yaml](/root/311-forecast-system/specs/010-demand-threshold-alerts/contracts/threshold-alerts-api.yaml)

**Tests**: Include contract, integration, and targeted frontend/backend tests because the design explicitly calls for contract coverage, acceptance alignment, and independent verification per user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`, `US4`)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the project skeleton and shared development tooling required by the implementation plan.

- [ ] T001 Create backend and frontend directory skeletons in `backend/src/api/`, `backend/src/pipelines/`, `backend/src/services/`, `backend/src/repositories/`, `backend/src/models/`, `backend/src/clients/`, `backend/src/core/`, `backend/tests/`, `frontend/src/api/`, `frontend/src/features/alerts/`, `frontend/src/types/`, and `frontend/tests/`
- [ ] T002 Initialize backend application entrypoints and package markers in `backend/src/main.py`, `backend/src/api/__init__.py`, `backend/src/services/__init__.py`, `backend/src/repositories/__init__.py`, `backend/src/models/__init__.py`, `backend/src/clients/__init__.py`, and `backend/src/core/__init__.py`
- [ ] T003 [P] Initialize frontend alert-review feature entrypoints in `frontend/src/features/alerts/index.ts`, `frontend/src/api/forecast_alerts.ts`, and `frontend/src/types/forecast_alerts.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared infrastructure that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create threshold-alert persistence models in `backend/src/models/threshold_configuration.py`, `backend/src/models/threshold_evaluation_run.py`, `backend/src/models/threshold_scope_evaluation.py`, `backend/src/models/threshold_state.py`, `backend/src/models/notification_event.py`, and `backend/src/models/notification_channel_attempt.py`
- [ ] T005 [P] Create the initial threshold-alert schema migration in `backend/src/models/migrations/010_threshold_alerts.py`
- [ ] T006 [P] Implement shared repository interfaces in `backend/src/repositories/threshold_configuration_repository.py`, `backend/src/repositories/threshold_evaluation_repository.py`, and `backend/src/repositories/notification_event_repository.py`
- [ ] T007 [P] Implement shared API schemas for evaluation triggers and alert review in `backend/src/api/schemas/forecast_alerts.py`
- [ ] T008 [P] Implement authenticated routing and authorization scaffolding for forecast alerts in `backend/src/api/routes/forecast_alerts.py` and `backend/src/core/auth.py`
- [ ] T009 [P] Implement notification delivery client abstractions in `backend/src/clients/notification_service.py`
- [ ] T010 Implement alert-evaluation pipeline orchestration and structured logging scaffolding in `backend/src/pipelines/threshold_alert_evaluation_pipeline.py` and `backend/src/core/logging.py`

**Checkpoint**: Foundation ready. User story implementation can now proceed.

---

## Phase 3: User Story 1 - Receive actionable spike alerts (Priority: P1) 🎯 MVP

**Goal**: Evaluate published forecast buckets against thresholds and create one alert event when a scope newly crosses above threshold.

**Independent Test**: Configure a category threshold, trigger evaluation for a published forecast bucket above threshold for one forecast window type and forecast window, and confirm one alert event is created with the category, forecast bucket value, threshold value, forecast window type, and forecast window.

### Tests for User Story 1

- [ ] T011 [P] [US1] Add contract tests for `POST /api/v1/forecast-alerts/evaluations` in `tests/contract/test_threshold_alert_evaluations.py`
- [ ] T012 [P] [US1] Add integration tests for threshold-crossing alert creation in `tests/integration/test_threshold_crossing_alerts.py`
- [ ] T013 [P] [US1] Add integration tests for daily and weekly forecast-window-type evaluation in `tests/integration/test_forecast_window_type_evaluation.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement forecast lineage lookup and canonical scope extraction for daily and weekly products in `backend/src/services/forecast_scope_service.py`
- [ ] T015 [US1] Implement threshold comparison and threshold-crossing detection helpers in `backend/src/services/threshold_alert_service.py`
- [ ] T016 [US1] Implement notification event creation and persistence for newly crossed scopes in `backend/src/repositories/notification_event_repository.py`
- [ ] T017 [US1] Connect evaluation-trigger route handling to the alert-evaluation pipeline in `backend/src/api/routes/forecast_alerts.py` and `backend/src/pipelines/threshold_alert_evaluation_pipeline.py`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Use geography-specific thresholds (Priority: P2)

**Goal**: Apply geography-specific thresholds correctly, including deterministic precedence over category-only thresholds for the same regional forecast bucket.

**Independent Test**: Configure both a category-only threshold and a category-plus-geography threshold, trigger a regional forecast exceedance, and confirm only the geography-specific threshold is evaluated for that regional scope while other regions still fall back to category-only thresholds when appropriate.

### Tests for User Story 2

- [ ] T018 [P] [US2] Add integration tests for geography-specific threshold precedence and scoped alerting in `tests/integration/test_geography_threshold_precedence.py`
- [ ] T019 [P] [US2] Add unit tests for threshold-selection precedence in `tests/unit/test_threshold_selection.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement threshold selection logic for category-only versus category-plus-geography rules in `backend/src/services/threshold_selection_service.py`
- [ ] T021 [US2] Integrate precedence-aware threshold resolution into the alert-evaluation pipeline in `backend/src/pipelines/threshold_alert_evaluation_pipeline.py`
- [ ] T022 [US2] Persist geography-scoped evaluation outcomes without double evaluation in `backend/src/repositories/threshold_evaluation_repository.py`
- [ ] T023 [US2] Update frontend alert types to include optional geography and canonical forecast-window fields in `frontend/src/types/forecast_alerts.ts`

**Checkpoint**: User Stories 1 and 2 are both independently functional and testable.

---

## Phase 5: User Story 3 - Preserve traceability when alerts cannot be sent (Priority: P3)

**Goal**: Record configuration gaps, suppressed duplicates, partial-delivery results, and total delivery failures with deterministic threshold-state behavior.

**Independent Test**: Trigger evaluations for missing-threshold, repeated-still-above-threshold, partial-channel-success, and total-delivery-failure cases and confirm the correct per-scope outcomes, threshold-state transitions, and follow-up statuses are persisted.

### Tests for User Story 3

- [ ] T024 [P] [US3] Add integration tests for missing-threshold, suppressed-duplicate, and total-failure outcomes in `tests/integration/test_threshold_alert_failures.py`
- [ ] T025 [P] [US3] Add unit tests for threshold-state transitions after threshold changes in `tests/unit/test_threshold_state_transitions.py`
- [ ] T026 [P] [US3] Add performance validation for the 5-minute successful delivery target in `tests/integration/test_alert_delivery_latency.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement threshold-state persistence and re-arming logic in `backend/src/repositories/threshold_state_repository.py`
- [ ] T028 [US3] Implement multi-channel delivery aggregation with `delivered`, `partial_delivery`, `retry_pending`, and `manual_review_required` statuses in `backend/src/services/notification_delivery_service.py`
- [ ] T029 [US3] Implement threshold-change reconciliation for threshold state and active threshold linkage in `backend/src/repositories/threshold_state_repository.py`
- [ ] T030 [US3] Persist channel-attempt records and failed follow-up reasons in `backend/src/repositories/notification_event_repository.py`
- [ ] T031 [US3] Integrate duplicate suppression and delivery-failure follow-up logic into the alert-evaluation pipeline in `backend/src/pipelines/threshold_alert_evaluation_pipeline.py`

**Checkpoint**: User Stories 1 through 3 are independently functional and traceable.

---

## Phase 6: User Story 4 - Review alert outcomes and channel failures (Priority: P3)

**Goal**: Provide authenticated alert review access that exposes the operational details needed to inspect delivered, partial-delivery, and failed alerts.

**Independent Test**: Retrieve alert-event history and a single alert detail view after successful, partial-delivery, and failed alerts have been recorded and confirm the response includes service category, optional geography, forecast window type, forecast window, forecast bucket value, threshold value, overall delivery outcome, and failed channel details when present.

### Tests for User Story 4

- [ ] T032 [P] [US4] Add contract tests for alert-event retrieval endpoints in `tests/contract/test_threshold_alert_events.py`
- [ ] T033 [P] [US4] Add contract assertions for all `FR-012a` alert review fields in `tests/contract/test_threshold_alert_review_payload.py`
- [ ] T034 [P] [US4] Add frontend interaction tests for alert review and channel-failure visibility in `frontend/tests/test_alert_review.tsx`

### Implementation for User Story 4

- [ ] T035 [US4] Implement alert-event list and detail query services in `backend/src/services/alert_review_service.py`
- [ ] T036 [US4] Implement alert-event retrieval endpoints in `backend/src/api/routes/forecast_alerts.py`
- [ ] T037 [US4] Implement frontend alert-review API list/detail retrieval methods in `frontend/src/api/forecast_alerts.ts`
- [ ] T038 [US4] Build typed alert-review UI state and rendering for overall outcomes and failed channels in `frontend/src/features/alerts/alert_review.tsx`

**Checkpoint**: All user stories are independently functional and reviewable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final alignment, documentation, and end-to-end validation across stories.

- [ ] T039 [P] Update quickstart and operational usage guidance in `specs/010-demand-threshold-alerts/quickstart.md`
- [ ] T040 [P] Update use-case and acceptance-test traceability references in `docs/UC-10.md` and `docs/UC-10-AT.md`
- [ ] T041 Run end-to-end validation for contract, integration, and frontend test suites in `tests/contract/`, `tests/integration/`, `tests/unit/`, and `frontend/tests/`
- [ ] T042 Perform final observability and security review for authenticated alert evaluation and review flows in `backend/src/core/logging.py`, `backend/src/core/auth.py`, and `backend/src/api/routes/forecast_alerts.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies; can start immediately.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: User Story 1**: Depends on Phase 2 only; this is the MVP slice.
- **Phase 4: User Story 2**: Depends on Phase 2 and builds on the shared evaluation flow from US1, but remains independently testable once implemented.
- **Phase 5: User Story 3**: Depends on Phase 2 and the shared alert/event infrastructure from US1; threshold-state behavior and delivery aggregation can be added without US4.
- **Phase 6: User Story 4**: Depends on Phase 2 and benefits from alert/event data produced by US1-US3.
- **Phase 7: Polish**: Depends on the user stories selected for delivery.

### User Story Dependencies

- **US1 (P1)**: No dependencies on other user stories after Foundational.
- **US2 (P2)**: Depends on the shared evaluation path from Foundational and reuses US1 alert creation flow.
- **US3 (P3)**: Depends on the shared evaluation and notification event flow from US1.
- **US4 (P3)**: Depends on persisted alert data and is most valuable after US1 and US3, but does not change their core behavior.

### Within Each User Story

- Contract/integration/unit/frontend tests should be written before or alongside implementation and should fail before the implementation is considered complete.
- Services depend on foundational models, repositories, auth, and schemas.
- Route and frontend tasks depend on the relevant backend services and typed contracts.

### Detailed Task Dependencies

- `T002` depends on `T001`.
- `T003` depends on `T001`.
- `T005` depends on `T004`.
- `T010` depends on `T004`, `T006`, and `T009`.
- `T014` depends on `T004` and `T010`.
- `T015` depends on `T004` and `T014`.
- `T016` depends on `T004` and `T006`.
- `T017` depends on `T007`, `T008`, `T010`, `T014`, `T015`, and `T016`.
- `T020` depends on `T014` and `T015`.
- `T021` depends on `T017` and `T020`.
- `T022` depends on `T006` and `T021`.
- `T023` depends on `T003` and the backend field shape stabilized by `T021` and `T022`.
- `T027` depends on `T004`.
- `T028` depends on `T009`.
- `T029` depends on `T027`.
- `T030` depends on `T016`.
- `T031` depends on `T017`, `T027`, `T028`, `T029`, and `T030`.
- `T035` depends on `T006`, `T022`, and `T031`.
- `T036` depends on `T007`, `T008`, and `T035`.
- `T037` depends on `T003`, `T023`, and `T036`.
- `T038` depends on the backend alert review service in `T035`, the backend retrieval endpoints in `T036`, the frontend alert-review API retrieval implementation in `T037`, and the typed frontend alert field shapes from `T023`.
- `T041` depends on `T017`, `T021`, `T031`, `T036`, `T037`, and `T038`.
- `T042` depends on `T008`, `T017`, `T031`, and `T036`.

## Parallel Opportunities

- After `T001`, `T002` and `T003` can run in parallel.
- After `T004`, `T006`, and `T009`, the remaining independent foundational tasks `T007` and `T008` can run in parallel, and `T005` can proceed once `T004` completes.
- In US1, `T011`, `T012`, and `T013` can run in parallel before the dependency chain `T014` → `T015`, alongside `T016` once `T004` and `T006` are complete.
- In US2, `T018` and `T019` can run in parallel before `T020`, then `T021`, then `T022`; `T023` begins only after `T003`, `T021`, and `T022`.
- In US3, `T024`, `T025`, and `T026` can run in parallel; `T027` and `T028` can then proceed independently, followed by `T029`, `T030`, and finally `T031`.
- In US4, `T032`, `T033`, and `T034` can run in parallel; `T035`, `T036`, and `T037` then proceed in dependency order, and `T038` begins only after all frontend and backend review prerequisites are complete.
- In Polish, `T039` and `T040` can run in parallel before `T041` and `T042`.

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for POST /api/v1/forecast-alerts/evaluations in tests/contract/test_threshold_alert_evaluations.py"
Task: "Add integration tests for threshold-crossing alert creation in tests/integration/test_threshold_crossing_alerts.py"
```

## Parallel Example: User Story 2

```bash
Task: "Add integration tests for geography-specific threshold precedence and scoped alerting in tests/integration/test_geography_threshold_precedence.py"
Task: "Add unit tests for threshold-selection precedence in tests/unit/test_threshold_selection.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add integration tests for missing-threshold, suppressed-duplicate, and total-failure outcomes in tests/integration/test_threshold_alert_failures.py"
Task: "Add unit tests for threshold-state transitions after threshold changes in tests/unit/test_threshold_state_transitions.py"
Task: "Add performance validation for the 5-minute successful delivery target in tests/integration/test_alert_delivery_latency.py"
```

## Parallel Example: User Story 4

```bash
Task: "Add contract tests for alert-event retrieval endpoints in tests/contract/test_threshold_alert_events.py"
Task: "Add contract assertions for all FR-012a alert review fields in tests/contract/test_threshold_alert_review_payload.py"
Task: "Add frontend interaction tests for alert review and channel-failure visibility in frontend/tests/test_alert_review.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the evaluation-trigger flow and alert-event creation independently.

### Incremental Delivery

1. Deliver US1 for baseline threshold-crossing alerts.
2. Add US2 for geography-specific thresholding and precedence.
3. Add US3 for traceability, duplicate suppression, and failure-state handling.
4. Add US4 for operational review of recorded alert outcomes.

### Parallel Team Strategy

1. Complete Setup and Foundational work together.
2. After Phase 2, assign:
   - Developer A: US1
   - Developer B: US2
   - Developer C: US3
3. Add US4 once alert-event data shape is stable enough for review UI work and the frontend alert-review API retrieval methods are in place.

## Notes

- All tasks follow the required checklist format with checkbox, task ID, optional `[P]`, required story label for story phases, and exact file paths.
- User stories remain independently testable, with US1 as the recommended MVP scope.
- The task list stays within the current UC-10 scope and does not add threshold-management or unrelated UI work.
