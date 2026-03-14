# Tasks: Configure Alert Thresholds and Notification Channels

**Input**: Design documents from `/specs/013-uc-13-configure-alert-thresholds/`
**Prerequisites**: [plan.md](/Users/sahmed/Documents/311-forecast-system/specs/013-uc-13-configure-alert-thresholds/plan.md), [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/013-uc-13-configure-alert-thresholds/spec.md), [research.md](/Users/sahmed/Documents/311-forecast-system/specs/013-uc-13-configure-alert-thresholds/research.md), [data-model.md](/Users/sahmed/Documents/311-forecast-system/specs/013-uc-13-configure-alert-thresholds/data-model.md), [alert-configuration-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/013-uc-13-configure-alert-thresholds/contracts/alert-configuration-api.yaml), [quickstart.md](/Users/sahmed/Documents/311-forecast-system/specs/013-uc-13-configure-alert-thresholds/quickstart.md)

**Tests**: Include backend unit, integration, and contract tests plus frontend interaction tests because UC-13 requires authenticated settings load, field validation, successful activation, and active-configuration continuity on failure.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently while preserving the shared alert-configuration versioning architecture.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the task touches different files and does not depend on incomplete work
- **[Story]**: User story mapping for implementation and test traceability
- All task descriptions include exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the planned backend, frontend, and test scaffolding for the shared alert-configuration workflow.

- [ ] T001 Create the planned backend, frontend, and test directories in `backend/src/api/routes/`, `backend/src/api/schemas/`, `backend/src/services/`, `backend/src/repositories/`, `backend/src/models/`, `backend/src/pipelines/`, `backend/src/clients/`, `backend/src/core/`, `frontend/src/api/`, `frontend/src/features/alert-configurations/components/`, `frontend/src/features/alert-configurations/hooks/`, `frontend/src/features/alert-configurations/state/`, `frontend/src/pages/`, `frontend/src/types/`, `frontend/tests/`, `tests/contract/`, `tests/integration/`, and `tests/unit/`
- [ ] T002 Create backend Python module scaffolding for alert-configuration retrieval and save orchestration in `backend/src/api/routes/alert_configurations.py`, `backend/src/api/schemas/alert_configurations.py`, `backend/src/services/alert_configuration_query_service.py`, `backend/src/services/alert_configuration_command_service.py`, `backend/src/services/alert_configuration_validation_service.py`, `backend/src/repositories/alert_configuration_repository.py`, and `backend/src/models/alert_configuration.py`
- [ ] T003 [P] Create frontend TypeScript scaffolding for the settings page, API access, and typed state in `frontend/src/api/alertConfigurationsApi.ts`, `frontend/src/types/alertConfigurations.ts`, `frontend/src/features/alert-configurations/hooks/useAlertConfiguration.ts`, `frontend/src/features/alert-configurations/state/alertConfigurationDraft.ts`, and `frontend/src/pages/AlertConfigurationPage.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared persistence, typed contracts, authorization, supported-channel resolution, and observability before story-specific behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create the UC-13 persistence models and canonical vocabularies for `AlertConfigurationVersion`, `ActiveAlertConfigurationMarker`, `AlertConfigurationThresholdRule`, `AlertConfigurationChannelSelection`, `AlertConfigurationDeliveryPreference`, and `AlertConfigurationUpdateAttempt` in `backend/src/models/alert_configuration.py`
- [ ] T005 [P] Create the initial alert-configuration schema migration in `backend/src/models/migrations/013_alert_configurations.py`
- [ ] T006 [P] Implement repository methods for active-marker lookup, immutable version creation, threshold-rule persistence, channel-selection persistence, delivery-preference persistence, update-attempt persistence, and atomic marker replacement in `backend/src/repositories/alert_configuration_repository.py`
- [ ] T007 [P] Define typed request and response schemas for active-configuration load, save success, validation rejection, and storage failure in `backend/src/api/schemas/alert_configurations.py`
- [ ] T008 [P] Implement authenticated and role-aware route dependencies for alert-configuration endpoints in `backend/src/core/auth.py` and `backend/src/api/routes/alert_configurations.py`
- [ ] T009 [P] Implement supported-notification-channel capability lookup and normalization in `backend/src/clients/notification_channel_capability_client.py`
- [ ] T010 [P] Implement structured logging helpers for configuration-load success, validation rejection, successful activation, and storage failure in `backend/src/core/logging.py`
- [ ] T011 [P] Create frontend typed contracts and API client support for active-configuration `GET` and `PUT` calls in `frontend/src/types/alertConfigurations.ts` and `frontend/src/api/alertConfigurationsApi.ts`
- [ ] T012 Implement shared validation helpers for threshold rules, required channel selection, supported-channel checks, and scoped frequency or deduplication rules in `backend/src/services/alert_configuration_validation_service.py`
- [ ] T013 Implement the shared query and command service skeletons for active-configuration expansion, immutable version creation, and update-attempt outcome handling in `backend/src/services/alert_configuration_query_service.py` and `backend/src/services/alert_configuration_command_service.py`

**Checkpoint**: Shared persistence, authorization, supported-channel resolution, validation, logging, and typed contracts are ready. User story implementation can begin.

---

## Phase 3: User Story 1 - Update alert thresholds and channels successfully (Priority: P1) 🎯 MVP

**Goal**: Let an authorized operational manager load the shared active alert configuration, edit threshold rules and scoped delivery preferences, save a new immutable configuration version, and have future alerts consume the new active version.

**Independent Test**: Load the active configuration, edit category-only and category-plus-geography threshold rules plus supported channels and scoped frequency or deduplication preferences, save successfully, and verify the new version is active, logged, and returned to the UI.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add contract tests for authenticated `GET /api/v1/alert-configurations/active` success, `401`, and `403`, plus authenticated `PUT` success in `tests/contract/test_alert_configuration_api.py`
- [ ] T015 [P] [US1] Add backend unit tests for scope normalization, category-only versus category-plus-geography distinction, immutable version-number allocation, and successful save-outcome derivation in `tests/unit/test_alert_configuration_services.py`
- [ ] T016 [P] [US1] Add integration tests for active-configuration load, successful version creation, atomic active-marker replacement, persisted channel selections, persisted scoped delivery preferences, and success logging in `tests/integration/test_alert_configuration_success.py`
- [ ] T017 [P] [US1] Add frontend interaction tests for authenticated settings load, draft editing, successful save confirmation, and returned active-configuration refresh in `frontend/tests/test_alert_configuration_success.tsx`

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement active-configuration retrieval and frontend-read-model assembly in `backend/src/services/alert_configuration_query_service.py`
- [ ] T019 [P] [US1] Implement immutable configuration-version creation, threshold-rule persistence, channel-selection persistence, delivery-preference persistence, and active-marker replacement in `backend/src/services/alert_configuration_command_service.py`
- [ ] T020 [US1] Implement the authenticated active-configuration load and save endpoints with thin request handling in `backend/src/api/routes/alert_configurations.py`
- [ ] T021 [P] [US1] Build the alert-configuration editor UI for threshold rules, channel selection, scoped frequency controls, and scoped deduplication controls in `frontend/src/features/alert-configurations/components/AlertConfigurationForm.tsx`
- [ ] T022 [US1] Implement the alert-configuration hook, draft-state transitions, and page composition for load, edit, save-success, and active-version refresh behavior in `frontend/src/features/alert-configurations/hooks/useAlertConfiguration.ts`, `frontend/src/features/alert-configurations/state/alertConfigurationDraft.ts`, and `frontend/src/pages/AlertConfigurationPage.tsx`
- [ ] T023 [US1] Integrate active alert consumers with the shared configuration marker so later threshold-alert and surge-alert evaluations read the current active configuration in `backend/src/pipelines/threshold_alert_evaluation_pipeline.py` and `backend/src/pipelines/surge_alert_evaluation_pipeline.py`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Prevent invalid or unsupported configuration from being applied (Priority: P2)

**Goal**: Reject invalid threshold values, zero-channel saves, unsupported channels, and invalid scoped delivery preferences while preserving the previously active configuration.

**Independent Test**: Submit invalid thresholds, no selected channels, unsupported channels, and invalid frequency or deduplication values, then verify field-level validation errors are returned, no new version is activated, and the previous active configuration remains in force.

### Tests for User Story 2

- [ ] T024 [P] [US2] Add contract tests for `PUT /api/v1/alert-configurations/active` `422` validation-rejection responses covering invalid thresholds, zero selected channels, unsupported channels, and invalid scoped delivery preferences in `tests/contract/test_alert_configuration_validation.py`
- [ ] T025 [P] [US2] Add backend unit tests for threshold-policy validation, supported-channel validation, required-channel enforcement, and delivery-preference validation rules in `tests/unit/test_alert_configuration_validation.py`
- [ ] T026 [P] [US2] Add integration tests verifying validation rejection leaves the previous active configuration unchanged and records `validation_rejected` update attempts in `tests/integration/test_alert_configuration_validation_rejection.py`
- [ ] T027 [P] [US2] Add frontend interaction tests for field-level validation errors, unsupported-channel feedback, and retained previously active configuration after failed saves in `frontend/tests/test_alert_configuration_validation.tsx`

### Implementation for User Story 2

- [ ] T028 [US2] Implement validation-rejection outcome assembly, validation-error summaries, and update-attempt recording for failed saves in `backend/src/services/alert_configuration_command_service.py`
- [ ] T029 [P] [US2] Persist validation-rejected update attempts without creating a new configuration version or moving the active marker in `backend/src/repositories/alert_configuration_repository.py`
- [ ] T030 [P] [US2] Build frontend validation messaging for threshold, channel, and scoped delivery-preference errors in `frontend/src/features/alert-configurations/components/AlertConfigurationValidationSummary.tsx`
- [ ] T031 [US2] Integrate validation-rejection response handling and draft error presentation into `frontend/src/features/alert-configurations/hooks/useAlertConfiguration.ts` and `frontend/src/pages/AlertConfigurationPage.tsx`

**Checkpoint**: User Stories 1 and 2 are independently functional and testable.

---

## Phase 5: User Story 3 - Preserve the active configuration when persistence fails (Priority: P3)

**Goal**: Surface a clear save-failure state when storage fails, log the failure, retain the previous active version, and keep later alert behavior stable.

**Independent Test**: Force a persistence failure during an otherwise valid save and verify the UI shows a save-failure message, structured logs capture the error, a `storage_failed` update attempt is retained, and the previously active configuration remains active on reload and in later alert evaluation.

### Tests for User Story 3

- [ ] T032 [P] [US3] Add contract tests for `PUT /api/v1/alert-configurations/active` `503` storage-failure responses in `tests/contract/test_alert_configuration_storage_failure.py`
- [ ] T033 [P] [US3] Add backend unit tests for storage-failure outcome derivation, previous-active-version retention, and failure-message shaping in `tests/unit/test_alert_configuration_storage_failure.py`
- [ ] T034 [P] [US3] Add integration tests for injected persistence failure, unchanged active marker, retained prior version, `storage_failed` update-attempt persistence, and failure logging in `tests/integration/test_alert_configuration_storage_failure.py`
- [ ] T035 [P] [US3] Add frontend interaction tests for save-failure messaging, retained saved values after reload, and no false success confirmation in `frontend/tests/test_alert_configuration_storage_failure.tsx`

### Implementation for User Story 3

- [ ] T036 [US3] Implement storage-failure handling, rollback-safe command behavior, and `storage_failed` outcome creation in `backend/src/services/alert_configuration_command_service.py`
- [ ] T037 [P] [US3] Persist storage-failure update attempts and preserve the existing active marker without partial activation in `backend/src/repositories/alert_configuration_repository.py`
- [ ] T038 [P] [US3] Build frontend save-failure messaging and recovery-state rendering in `frontend/src/features/alert-configurations/components/AlertConfigurationSaveFailure.tsx`
- [ ] T039 [US3] Integrate storage-failure response handling and reload-safe retained-active-state behavior into `frontend/src/features/alert-configurations/hooks/useAlertConfiguration.ts` and `frontend/src/pages/AlertConfigurationPage.tsx`

**Checkpoint**: All user stories are independently functional and reviewable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish traceability, contract alignment, and cross-feature verification for the shared alert-configuration workflow.

- [ ] T040 [P] Map implementation and verification steps for AT-01 through AT-10 in `specs/013-uc-13-configure-alert-thresholds/quickstart.md`
- [ ] T041 [P] Align request and response examples for active load, validation rejection, storage failure, and successful save outcomes in `specs/013-uc-13-configure-alert-thresholds/contracts/alert-configuration-api.yaml`
- [ ] T042 [P] Add observability and correlation-id assertions for successful save, validation rejection, and storage failure flows in `tests/integration/test_alert_configuration_success.py`, `tests/integration/test_alert_configuration_validation_rejection.py`, and `tests/integration/test_alert_configuration_storage_failure.py`
- [ ] T043 Run end-to-end verification for contract, unit, integration, and frontend interaction suites covering alert-configuration loading and save outcomes in `tests/contract/`, `tests/unit/`, `tests/integration/`, and `frontend/tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies.
- **Phase 2: Foundational**: Depends on Phase 1 and blocks all user story work.
- **Phase 3: US1**: Depends on Phase 2 only; this is the MVP slice.
- **Phase 4: US2**: Depends on Phase 2 and on the successful save pipeline established in US1.
- **Phase 5: US3**: Depends on Phase 2 and on the command and persistence path established in US1.
- **Phase 6: Polish**: Depends on the user stories being shipped.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational.
- **US2 (P2)**: Depends on US1 load and save orchestration, but remains independently testable through validation-rejection behavior.
- **US3 (P3)**: Depends on US1 command and persistence flow; it can proceed independently of US2 once the save path exists.

### Within Each User Story

- Contract, unit, integration, and frontend interaction tests should be written before or alongside implementation and must fail before implementation is considered complete.
- Backend validation and persistence behavior precede route finalization.
- Route and frontend state handling depend on the relevant backend services and typed contracts.
- Cross-feature alert-consumer alignment follows successful active-configuration activation logic.

### Explicit Task Prerequisites

- `T002` depends on `T001`.
- `T003` depends on `T001`.
- `T005` depends on `T004`.
- `T012` depends on `T004`, `T007`, and `T009`.
- `T013` depends on `T004`, `T006`, `T009`, `T010`, and `T012`.
- `T018` depends on `T013`.
- `T019` depends on `T013`.
- `T020` depends on `T007`, `T008`, `T018`, and `T019`.
- `T021` depends on `T011`.
- `T022` depends on `T011`, `T020`, and `T021`.
- `T023` depends on `T019`.
- `T028` depends on `T012` and `T019`.
- `T029` depends on `T006` and `T028`.
- `T030` depends on `T021`.
- `T031` depends on `T022` and `T030`.
- `T036` depends on `T019`.
- `T037` depends on `T006` and `T036`.
- `T038` depends on `T021`.
- `T039` depends on `T022`, `T036`, and `T038`.
- `T043` depends on `T020`, `T031`, `T039`, and the related test tasks for each story.

## Parallel Opportunities

- Phase 1: `T003` can run in parallel with `T002` after `T001`.
- Phase 2: `T005` through `T011` can run in parallel after `T004`; `T012` and `T013` begin once the shared persistence, schema, capability, and logging scaffolding are ready.
- US1: `T014`, `T015`, `T016`, and `T017` can run in parallel; `T018` and `T019` can run in parallel before `T020`; `T021` can proceed in parallel with backend service work after typed frontend contracts exist.
- US2: `T024`, `T025`, `T026`, and `T027` can run in parallel; `T029` and `T030` can run in parallel after `T028`.
- US3: `T032`, `T033`, `T034`, and `T035` can run in parallel; `T037` and `T038` can run in parallel after `T036`.
- Phase 6: `T040`, `T041`, and `T042` can run in parallel before `T043`.

## Parallel Example: User Story 1

```bash
Task: "Add contract tests for GET /api/v1/alert-configurations/active and successful PUT /api/v1/alert-configurations/active handling in tests/contract/test_alert_configuration_api.py"
Task: "Add backend unit tests for scope normalization and immutable version-number allocation in tests/unit/test_alert_configuration_services.py"
Task: "Add integration tests for active-marker replacement and persisted channel selections in tests/integration/test_alert_configuration_success.py"
Task: "Add frontend interaction tests for settings load, draft editing, and successful save confirmation in frontend/tests/test_alert_configuration_success.tsx"
```

```bash
Task: "Implement active-configuration retrieval and frontend-read-model assembly in backend/src/services/alert_configuration_query_service.py"
Task: "Implement immutable configuration-version creation and active-marker replacement in backend/src/services/alert_configuration_command_service.py"
Task: "Build the alert-configuration editor UI in frontend/src/features/alert-configurations/components/AlertConfigurationForm.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add contract tests for validation-rejection responses covering invalid thresholds, zero selected channels, and unsupported channels in tests/contract/test_alert_configuration_validation.py"
Task: "Add integration tests verifying validation rejection leaves the previous active configuration unchanged in tests/integration/test_alert_configuration_validation_rejection.py"
Task: "Add frontend interaction tests for field-level validation errors and unsupported-channel feedback in frontend/tests/test_alert_configuration_validation.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "Add contract tests for PUT /api/v1/alert-configurations/active 503 storage-failure responses in tests/contract/test_alert_configuration_storage_failure.py"
Task: "Add integration tests for injected persistence failure and unchanged active marker in tests/integration/test_alert_configuration_storage_failure.py"
Task: "Add frontend interaction tests for save-failure messaging and retained saved values after reload in frontend/tests/test_alert_configuration_storage_failure.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the full authenticated configuration load and successful activation flow before expanding scope.

### Incremental Delivery

1. Deliver US1 to establish the shared active-configuration retrieval, editing, and successful save path.
2. Add US2 to reject invalid or unsupported configurations without moving the active marker.
3. Add US3 to harden storage-failure handling and preserve operational continuity when persistence fails.
4. Finish with Phase 6 traceability, contract alignment, and cross-cutting verification.

### Parallel Team Strategy

1. One engineer can own persistence, migration, and command-service work in Phase 2.
2. In US1, backend query and command work can proceed in parallel with frontend form and state work after shared types are in place.
3. In later phases, validation handling and storage-failure handling can be split between backend outcome logic and frontend response-state rendering.
