# Tasks: Abnormal Demand Surge Notifications

**Input**: Design documents from `/specs/011-abnormal-demand-surge-notifications/`
**Prerequisites**: [plan.md](/Users/sahmed/Documents/311-forecast-system/specs/011-abnormal-demand-surge-notifications/plan.md), [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/011-abnormal-demand-surge-notifications/spec.md), [research.md](/Users/sahmed/Documents/311-forecast-system/specs/011-abnormal-demand-surge-notifications/research.md), [data-model.md](/Users/sahmed/Documents/311-forecast-system/specs/011-abnormal-demand-surge-notifications/data-model.md), [surge-alerts-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/011-abnormal-demand-surge-notifications/contracts/surge-alerts-api.yaml)

**Tests**: Include contract, integration, and targeted frontend/backend tests because the design explicitly calls for contract coverage, acceptance alignment, and independent verification per user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the project skeleton and shared development tooling required by the implementation plan.

- [ ] T001 Create backend and frontend directory skeletons in `backend/src/api/`, `backend/src/pipelines/`, `backend/src/services/`, `backend/src/repositories/`, `backend/src/models/`, `backend/src/clients/`, `backend/src/core/`, `backend/tests/`, `frontend/src/api/`, `frontend/src/features/surge_alerts/`, `frontend/src/types/`, and `frontend/tests/`
- [ ] T002 Initialize backend application entrypoints and package markers in `backend/src/main.py`, `backend/src/api/__init__.py`, `backend/src/services/__init__.py`, `backend/src/repositories/__init__.py`, `backend/src/models/__init__.py`, `backend/src/clients/__init__.py`, and `backend/src/core/__init__.py`
- [ ] T003 [P] Initialize frontend surge-alert review feature entrypoints in `frontend/src/features/surge_alerts/index.ts`, `frontend/src/api/surge_alerts.ts`, and `frontend/src/types/surge_alerts.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared infrastructure that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create surge-alert persistence models in `backend/src/models/surge_detection_configuration.py`, `backend/src/models/surge_evaluation_run.py`, `backend/src/models/surge_candidate.py`, `backend/src/models/surge_confirmation_outcome.py`, `backend/src/models/surge_state.py`, `backend/src/models/surge_notification_event.py`, and `backend/src/models/surge_notification_channel_attempt.py`
- [X] T005 [P] Create the initial surge-alert schema migration in `backend/src/models/migrations/011_surge_alerts.py`
- [X] T006 [P] Implement shared repository interfaces in `backend/src/repositories/surge_configuration_repository.py`, `backend/src/repositories/surge_evaluation_repository.py`, `backend/src/repositories/surge_state_repository.py`, and `backend/src/repositories/surge_notification_event_repository.py`
- [X] T007 [P] Implement shared API schemas for manual replay triggers plus surge evaluation and event review in `backend/src/api/schemas/surge_alerts.py`
- [X] T008 [P] Implement authenticated routing and authorization scaffolding for surge alerts in `backend/src/api/routes/surge_alerts.py` and `backend/src/core/auth.py`
- [X] T009 [P] Implement notification delivery client abstractions for surge alerts in `backend/src/clients/notification_service.py`
- [X] T010 Implement surge-evaluation pipeline orchestration and structured logging scaffolding in `backend/src/pipelines/surge_alert_evaluation_pipeline.py` and `backend/src/core/logging.py`

**Checkpoint**: Foundation ready. User story implementation can now proceed.

---

## Phase 3: User Story 1 - Receive a confirmed surge alert (Priority: P1) 🎯 MVP

**Goal**: Detect residual-based surge candidates after successful ingestion, confirm them with the dual-threshold rule, create one notification when a scope newly enters surge state, and persist successful delivery outcomes.

**Independent Test**: Complete a successful UC-01 ingestion run for a service category whose newly ingested actual demand produces a residual against the active LightGBM P50 forecast with both a z-score above threshold and a percent-above-forecast above floor, and confirm exactly one notification event is created, delivered, and logged for that scope while it remains in surge state.

### Tests for User Story 1

- [X] T011 [P] [US1] Add contract tests for manual replay `POST /api/v1/surge-alerts/evaluations` in `tests/contract/test_surge_alert_evaluations.py`
- [X] T012 [P] [US1] Add integration tests for confirmed-surge candidate creation, confirmation, and notification-event persistence in `tests/integration/test_confirmed_surge_alerts.py`
- [ ] T013 [P] [US1] Add integration tests for daily and weekly forecast-product evaluation and notification delivery success in `tests/integration/test_surge_forecast_product_evaluation.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement ingestion-linked scope aggregation and active forecast lineage lookup for daily and weekly products in `backend/src/services/surge_scope_service.py`
- [X] T015 [US1] Implement residual calculation, rolling-baseline z-score computation, and percent-above-forecast helpers in `backend/src/services/surge_detection_service.py`
- [X] T016 [US1] Implement dual-threshold confirmation and confirmed-notification creation helpers in `backend/src/services/surge_confirmation_service.py`
- [X] T017 [US1] Implement surge notification-event and channel-attempt persistence for successful deliveries in `backend/src/repositories/surge_notification_event_repository.py`
- [X] T018 [US1] Connect manual-replay route handling to the surge-evaluation pipeline and delivery flow in `backend/src/api/routes/surge_alerts.py` and `backend/src/pipelines/surge_alert_evaluation_pipeline.py`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Avoid alerts for invalid surges (Priority: P2)

**Goal**: Filter detector false positives and suppress repeat notifications while a scope remains in active surge state, without creating or sending invalid alerts.

**Independent Test**: Complete ingestion-triggered evaluations where one candidate fails either the z-score or percent-above-forecast confirmation check and another candidate remains above both thresholds for an already active surge scope, and confirm the first is persisted as filtered with no notification and the second is persisted as suppressed with no duplicate notification until the scope returns to normal.

### Tests for User Story 2

- [X] T019 [P] [US2] Add integration tests for filtered candidates that fail one confirmation threshold in `tests/integration/test_filtered_surge_candidates.py`
- [X] T020 [P] [US2] Add unit tests for dual-threshold confirmation decisions in `tests/unit/test_surge_confirmation.py`
- [X] T021 [P] [US2] Add integration tests for active-surge duplicate suppression and re-arming after return to normal in `tests/integration/test_surge_state_suppression.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement confirmation-outcome persistence for `filtered` and `suppressed_active_surge` results in `backend/src/repositories/surge_evaluation_repository.py`
- [X] T023 [US2] Implement surge-state transitions and notification re-arming logic in `backend/src/services/surge_state_service.py`
- [X] T024 [US2] Integrate filtered-candidate handling, duplicate suppression, and return-to-normal state updates into `backend/src/pipelines/surge_alert_evaluation_pipeline.py`
- [X] T025 [US2] Persist per-scope surge state and active-surge linkage without duplicate notification creation in `backend/src/repositories/surge_state_repository.py`

**Checkpoint**: User Stories 1 and 2 are both independently functional and testable.

---

## Phase 5: User Story 3 - Preserve traceability when detection or delivery fails (Priority: P3)

**Goal**: Persist detector failures, failed or partial delivery outcomes, and reviewable surge-evaluation plus surge-event history with authenticated retrieval of evaluation details, event details, and channel-attempt traces.

**Independent Test**: Force a detector processing failure after a successful ingestion run and a delivery failure after a confirmed surge, then retrieve surge-evaluation history, evaluation detail, surge-event history, and event detail records to confirm failure reasons, follow-up statuses, channel attempts, correlation identifiers, and no invalid notification send occurred for the detector-failure case.

### Tests for User Story 3

- [ ] T026 [P] [US3] Add integration tests for detector failures, partial delivery, and total delivery failure outcomes in `tests/integration/test_surge_alert_failures.py`
- [X] T027 [P] [US3] Add contract tests for surge-evaluation and surge-event retrieval endpoints in `tests/contract/test_surge_alert_events.py`
- [ ] T028 [P] [US3] Add contract assertions for surge-evaluation review payload fields, surge-event review payload fields, and channel-attempt detail in `tests/contract/test_surge_alert_review_payload.py`
- [X] T029 [P] [US3] Add frontend interaction tests for surge-evaluation review, surge-event review, and failed-channel visibility in `frontend/tests/test_surge_alert_review.tsx`
- [ ] T030 [P] [US3] Add performance validation for the 5-minute surge confirmation and persistence target in `tests/integration/test_surge_alert_latency.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement detector-failure persistence, confirmation-failure outcomes, and run-level failure summarization in `backend/src/repositories/surge_evaluation_repository.py`
- [X] T032 [US3] Implement multi-channel delivery aggregation with `delivered`, `partial_delivery`, `retry_pending`, and `manual_review_required` statuses in `backend/src/services/surge_notification_delivery_service.py`
- [X] T033 [US3] Persist failed channel attempts, follow-up reasons, and shared correlation identifiers in `backend/src/repositories/surge_notification_event_repository.py`
- [X] T034 [US3] Implement surge-evaluation and surge-event list/detail query services in `backend/src/services/surge_alert_review_service.py`
- [X] T035 [US3] Implement surge-evaluation and surge-event retrieval endpoints in `backend/src/api/routes/surge_alerts.py`
- [X] T036 [US3] Implement frontend surge-alert API list/detail retrieval methods and typed contracts for evaluations and events in `frontend/src/api/surge_alerts.ts` and `frontend/src/types/surge_alerts.ts`
- [X] T037 [US3] Build typed surge-alert review UI state and rendering for evaluation outcomes, confirmation metrics, overall delivery outcomes, and failed channels in `frontend/src/features/surge_alerts/surge_alert_review.tsx`
- [X] T038 [US3] Integrate detector-failure handling and delivery-failure follow-up logic into `backend/src/pipelines/surge_alert_evaluation_pipeline.py`

**Checkpoint**: All user stories are independently functional and reviewable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final alignment, documentation, and end-to-end validation across stories.

- [ ] T039 [P] Update quickstart and operational usage guidance in `specs/011-abnormal-demand-surge-notifications/quickstart.md`
- [ ] T040 [P] Update use-case and acceptance-test traceability references in `docs/UC-11.md` and `docs/UC-11-AT.md`
- [ ] T041 Run end-to-end validation for contract, integration, frontend, and unit test suites in `tests/contract/`, `tests/integration/`, `tests/unit/`, and `frontend/tests/`
- [ ] T042 Perform final observability and security review for authenticated replay and surge-review flows in `backend/src/core/logging.py`, `backend/src/core/auth.py`, and `backend/src/api/routes/surge_alerts.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies; can start immediately.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: User Story 1**: Depends on Phase 2 only; this is the MVP slice.
- **Phase 4: User Story 2**: Depends on Phase 2 and builds on the shared detection and notification flow from US1, but remains independently testable once implemented.
- **Phase 5: User Story 3**: Depends on Phase 2 and the shared surge candidate, notification-event, and delivery infrastructure from US1.
- **Phase 6: Polish**: Depends on the user stories selected for delivery.

### User Story Dependencies

- **US1 (P1)**: No dependencies on other user stories after Foundational.
- **US2 (P2)**: Depends on the shared detection and notification path from Foundational and reuses US1 confirmation and notification flow.
- **US3 (P3)**: Depends on the shared evaluation and surge-notification flow from US1 and benefits from the suppression and state behavior added in US2.

### Within Each User Story

- Contract, integration, unit, and frontend tests should be written before or alongside implementation and should fail before the implementation is considered complete.
- Services depend on foundational models, repositories, auth, and schemas.
- Route and frontend tasks depend on the relevant backend services and typed contracts for both evaluation review and event review.

### Detailed Task Dependencies

- `T002` depends on `T001`.
- `T003` depends on `T001`.
- `T005` depends on `T004`.
- `T010` depends on `T004`, `T006`, and `T009`.
- `T014` depends on `T004` and `T010`.
- `T015` depends on `T004` and `T014`.
- `T016` depends on `T015`.
- `T017` depends on `T004` and `T006`.
- `T018` depends on `T007`, `T008`, `T010`, `T014`, `T015`, `T016`, and `T017`.
- `T022` depends on `T006` and `T016`.
- `T023` depends on `T016`.
- `T024` depends on `T018`, `T022`, and `T023`.
- `T025` depends on `T006` and `T023`.
- `T031` depends on `T006` and `T024`.
- `T032` depends on `T009` and `T017`.
- `T033` depends on `T017` and `T032`.
- `T034` depends on `T006`, `T031`, and `T033`.
- `T035` depends on `T007`, `T008`, and `T034`.
- `T036` depends on `T003` and `T035`.
- `T037` depends on `T034`, `T035`, and `T036`.
- `T038` depends on `T024`, `T031`, `T032`, and `T033`.
- `T041` depends on `T018`, `T024`, `T035`, `T036`, `T037`, and `T038`.
- `T042` depends on `T008`, `T018`, `T035`, and `T038`.

## Parallel Opportunities

- After `T001`, `T002` and `T003` can run in parallel.
- After `T004`, the remaining independent foundational tasks `T005`, `T006`, `T007`, `T008`, and `T009` can run in parallel; `T010` begins once `T004`, `T006`, and `T009` complete.
- In US1, `T011`, `T012`, and `T013` can run in parallel before the dependency chain `T014` → `T015` → `T016`, alongside `T017` once `T004` and `T006` are complete.
- In US2, `T019`, `T020`, and `T021` can run in parallel before `T022` and `T023`, then `T024` and `T025` proceed in dependency order.
- In US3, `T026`, `T027`, `T028`, `T029`, and `T030` can run in parallel; `T031` and `T032` can then proceed independently, followed by `T033`, `T034`, `T035`, `T036`, `T037`, and `T038`.
- In Polish, `T039` and `T040` can run in parallel before `T041` and `T042`.

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for POST /api/v1/surge-alerts/evaluations in tests/contract/test_surge_alert_evaluations.py"
Task: "Add integration tests for confirmed-surge candidate creation, confirmation, and notification-event persistence in tests/integration/test_confirmed_surge_alerts.py"
```

## Parallel Example: User Story 2

```bash
Task: "Add integration tests for filtered candidates that fail one confirmation threshold in tests/integration/test_filtered_surge_candidates.py"
Task: "Add integration tests for active-surge duplicate suppression and re-arming after return to normal in tests/integration/test_surge_state_suppression.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add integration tests for detector failures, partial delivery, and total delivery failure outcomes in tests/integration/test_surge_alert_failures.py"
Task: "Add contract tests for surge-evaluation and surge-event retrieval endpoints in tests/contract/test_surge_alert_events.py"
Task: "Add frontend interaction tests for surge-evaluation review, surge-event review, and failed-channel visibility in frontend/tests/test_surge_alert_review.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the ingestion-triggered confirmed-surge flow and notification creation independently.

### Incremental Delivery

1. Deliver US1 for confirmed surge detection, notification creation, and successful delivery logging.
2. Add US2 for false-positive filtering, duplicate suppression, and notification re-arming after return to normal.
3. Add US3 for traceable detector failures, delivery failures, and authenticated surge-evaluation plus surge-event review.

### Parallel Team Strategy

1. Complete Setup and Foundational work together.
2. After Phase 2, assign:
   - Developer A: US1
   - Developer B: US2
   - Developer C: US3
