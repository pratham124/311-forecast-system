# Tasks: UC-02 Validate and Deduplicate Ingested Data

**Input**: Design documents from `/specs/002-validate-deduplicate-data/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include unit, integration, and contract coverage because the plan explicitly requires pytest-based coverage aligned to `docs/UC-02-AT.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` for implementation and tests
- Paths below follow the backend-only structure defined in plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the backend project structure for UC-02 validation and deduplication work

- [ ] T001 Create the UC-02 backend module directories in `backend/app/models/`, `backend/app/pipelines/ingestion/`, `backend/app/repositories/`, `backend/app/services/`, `backend/app/schemas/`, and `backend/tests/`
- [ ] T002 Create the validation feature package markers in `backend/app/pipelines/ingestion/__init__.py`, `backend/app/repositories/__init__.py`, `backend/app/services/__init__.py`, and `backend/app/schemas/__init__.py`
- [ ] T003 [P] Create the UC-02 test package markers in `backend/tests/contract/__init__.py`, `backend/tests/integration/__init__.py`, and `backend/tests/unit/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create the UC-02 persistence schema migration in `backend/alembic/versions/002_uc02_validation_pipeline.py`
- [ ] T005 [P] Define shared UC-02 ORM models in `backend/app/models/validation_models.py`
- [ ] T006 [P] Define shared UC-02 API and service schemas in `backend/app/schemas/validation_status.py`
- [ ] T007 [P] Implement shared validation-run and cleaned-dataset repositories in `backend/app/repositories/validation_repository.py`
- [ ] T008 [P] Implement the shared approval-marker and operational-status repository helpers in `backend/app/repositories/approval_status_repository.py`
- [ ] T009 [P] Implement shared authorization dependencies for operational status surfaces in `backend/app/api/dependencies/authz.py`
- [ ] T010 Implement the shared validation orchestration entry point in `backend/app/pipelines/ingestion/validation_pipeline.py`
- [ ] T011 Add UC-02 traceability notes and requirement mapping references in `specs/002-validate-deduplicate-data/tasks.md`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Approve a clean dataset (Priority: P1) 🎯 MVP

**Goal**: Validate a newly ingested dataset, resolve duplicates into cleaned records, store the cleaned dataset version, and move the approval marker to that cleaned dataset version

**Independent Test**: Submit a dataset that matches required fields, data types, formats, and structural completeness rules and contains duplicates resolvable by policy, then confirm the cleaned dataset becomes the approved active version for downstream use.

### Tests for User Story 1

- [ ] T012 [P] [US1] Add contract test for `GET /api/v1/validation-runs/{validationRunId}` success responses in `backend/tests/contract/test_validation_run_status.py`
- [ ] T013 [P] [US1] Add contract test for `GET /api/v1/datasets/approved/current` success responses in `backend/tests/contract/test_approved_dataset_status.py`
- [ ] T014 [P] [US1] Add integration test for the clean approval flow in `backend/tests/integration/test_validation_approval_flow.py`
- [ ] T015 [P] [US1] Add unit tests for duplicate grouping and consolidation policy in `backend/tests/unit/test_duplicate_resolution_service.py`
- [ ] T016 [P] [US1] Add integration test for the 15-minute UC-02 completion target in `backend/tests/integration/test_validation_completion_timing.py`

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement schema-validation rule evaluation for required fields, data types, formats, and structural completeness in `backend/app/services/schema_validation_service.py`
- [ ] T018 [P] [US1] Implement duplicate analysis and percentage calculation in `backend/app/services/duplicate_analysis_service.py`
- [ ] T019 [P] [US1] Implement duplicate consolidation into one cleaned record per duplicate group in `backend/app/services/duplicate_resolution_service.py`
- [ ] T020 [P] [US1] Implement approval-timing instrumentation in `backend/app/services/validation_metrics_service.py`
- [ ] T021 [US1] Implement cleaned dataset version persistence and approval-marker update in `backend/app/services/cleaned_dataset_service.py`
- [ ] T022 [US1] Wire the approved-path orchestration into `backend/app/pipelines/ingestion/approved_pipeline.py`
- [ ] T023 [US1] Implement the approved dataset route in `backend/app/api/routes/approved_dataset_status.py`
- [ ] T024 [US1] Implement the validation-run status route in `backend/app/api/routes/validation_run_status.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Reject invalid datasets safely (Priority: P2)

**Goal**: Reject schema-invalid datasets, preserve the previously approved cleaned dataset, and expose rejection outcomes to authorized operators without exposing raw source data

**Independent Test**: Submit a dataset with missing required information or malformed values and confirm it receives a `rejected` outcome, duplicate analysis is not run, the previous approved dataset remains active, and authorized operators can inspect the rejection summary.

### Tests for User Story 2

- [ ] T025 [P] [US2] Add integration test for schema rejection preserving the prior approved dataset in `backend/tests/integration/test_schema_rejection_flow.py`
- [ ] T026 [P] [US2] Add unit tests for rejected outcome classification in `backend/tests/unit/test_schema_validation_outcomes.py`

### Implementation for User Story 2

- [ ] T027 [US2] Update validation outcome persistence to classify schema-invalid datasets as `rejected` in `backend/app/repositories/validation_repository.py`
- [ ] T028 [US2] Implement schema-rejection handling and duplicate-analysis short-circuiting in `backend/app/pipelines/ingestion/rejection_pipeline.py`
- [ ] T029 [US2] Implement operationally necessary rejection summaries in `backend/app/services/validation_status_service.py`
- [ ] T030 [US2] Enforce rejection visibility and approved-marker preservation rules in `backend/app/services/approval_status_service.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hold suspicious or failed runs for review (Priority: P3)

**Goal**: Block approval for review-needed, duplicate-processing failure, storage failure, or degraded outcome-persistence cases while keeping the previously approved cleaned dataset active and distinguishable from blocked candidates

**Independent Test**: Submit one dataset that exceeds the duplicate percentage threshold and another that triggers duplicate-processing, storage, or status-persistence failure, then confirm each candidate remains not approved and the previous approved dataset stays active.

### Tests for User Story 3

- [ ] T031 [P] [US3] Add contract tests for unauthorized, forbidden, missing-resource, and invalid-query review-needed status-surface responses in `backend/tests/contract/test_validation_status_errors.py`
- [ ] T032 [P] [US3] Add contract test for `GET /api/v1/datasets/review-needed` in `backend/tests/contract/test_review_needed_status.py`
- [ ] T033 [P] [US3] Add integration test for review-needed threshold handling in `backend/tests/integration/test_review_needed_flow.py`
- [ ] T034 [P] [US3] Add integration test for failed outcome and degraded outcome-persistence safety in `backend/tests/integration/test_failed_outcome_safety.py`
- [ ] T035 [P] [US3] Add integration test for the 2-minute operator visibility target in `backend/tests/integration/test_operator_visibility_timing.py`

### Implementation for User Story 3

- [ ] T036 [P] [US3] Implement review-needed record persistence and summary exposure in `backend/app/repositories/review_needed_repository.py`
- [ ] T037 [P] [US3] Implement failed-outcome and degraded-persistence safety handling in `backend/app/services/operational_status_service.py`
- [ ] T038 [P] [US3] Implement operator-visibility timing instrumentation in `backend/app/services/operator_visibility_metrics_service.py`
- [ ] T039 [US3] Wire review-needed, failed, and degraded-state handling into `backend/app/pipelines/ingestion/blocked_outcome_pipeline.py`
- [ ] T040 [US3] Implement the review-needed status route in `backend/app/api/routes/review_needed_status.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Add cross-story unit coverage for approval-marker invariants in `backend/tests/unit/test_approval_marker_invariants.py`
- [ ] T042 [P] Add cross-story integration coverage for operator visibility across approved, in-progress, rejected, failed, and review-needed candidates in `backend/tests/integration/test_operational_status_visibility.py`
- [ ] T043 Harden structured logging and summary-only status exposure in `backend/app/core/logging.py`
- [ ] T044 Update the implementation walkthrough and validation steps in `specs/002-validate-deduplicate-data/quickstart.md`
- [ ] T045 Run the quickstart verification flow and record any follow-up notes in `specs/002-validate-deduplicate-data/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and should reuse the validation and approval infrastructure from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) and should build on shared status and approval infrastructure from US1

### Within Each User Story

- Contract, integration, and unit tests should be written before or alongside implementation and should fail before the matching implementation is completed
- Schemas and repositories before orchestration changes
- Services before API routes
- Core story behavior before cross-story polish

### Parallel Opportunities

- `T003`, `T005`, `T006`, `T007`, `T008`, and `T009` can run in parallel after directory setup
- In **US1**, `T012`, `T013`, `T014`, `T015`, and `T016` can run in parallel, and `T017`, `T018`, `T019`, and `T020` can run in parallel
- In **US2**, `T025` and `T026` can run in parallel
- In **US3**, `T031`, `T032`, `T033`, `T034`, and `T035` can run in parallel, and `T036`, `T037`, and `T038` can run in parallel
- In **Polish**, `T041` and `T042` can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch US1 tests together:
Task: "Add contract test for GET /api/v1/validation-runs/{validationRunId} success responses in backend/tests/contract/test_validation_run_status.py"
Task: "Add contract test for GET /api/v1/datasets/approved/current success responses in backend/tests/contract/test_approved_dataset_status.py"
Task: "Add integration test for the clean approval flow in backend/tests/integration/test_validation_approval_flow.py"
Task: "Add unit tests for duplicate grouping and consolidation policy in backend/tests/unit/test_duplicate_resolution_service.py"
Task: "Add integration test for the 15-minute UC-02 completion target in backend/tests/integration/test_validation_completion_timing.py"

# Launch US1 services together:
Task: "Implement schema-validation rule evaluation for required fields, data types, formats, and structural completeness in backend/app/services/schema_validation_service.py"
Task: "Implement duplicate analysis and percentage calculation in backend/app/services/duplicate_analysis_service.py"
Task: "Implement duplicate consolidation into one cleaned record per duplicate group in backend/app/services/duplicate_resolution_service.py"
Task: "Implement approval-timing instrumentation in backend/app/services/validation_metrics_service.py"
```

---

## Parallel Example: User Story 3

```bash
# Launch US3 test coverage together:
Task: "Add contract tests for unauthorized, forbidden, missing-resource, and invalid-query status-surface responses in backend/tests/contract/test_validation_status_errors.py"
Task: "Add contract test for GET /api/v1/datasets/review-needed in backend/tests/contract/test_review_needed_status.py"
Task: "Add integration test for review-needed threshold handling in backend/tests/integration/test_review_needed_flow.py"
Task: "Add integration test for failed outcome and degraded outcome-persistence safety in backend/tests/integration/test_failed_outcome_safety.py"
Task: "Add integration test for the 2-minute operator visibility target in backend/tests/integration/test_operator_visibility_timing.py"

# Launch US3 persistence and service work together:
Task: "Implement review-needed record persistence and summary exposure in backend/app/repositories/review_needed_repository.py"
Task: "Implement failed-outcome and degraded-persistence safety handling in backend/app/services/operational_status_service.py"
Task: "Implement operator-visibility timing instrumentation in backend/app/services/operator_visibility_metrics_service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run the US1 contract, integration, and unit tests independently
5. Demo the approved cleaned-dataset flow before moving to rejection and blocked-outcome scenarios

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready
2. Add User Story 1 → validate approved cleaned-dataset flow → deploy/demo MVP
3. Add User Story 2 → validate rejected outcome behavior → deploy/demo
4. Add User Story 3 → validate review-needed, failed, and degraded-state behavior → deploy/demo
5. Finish cross-story polish and visibility validation

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 services and approved dataset route
   - Developer B: User Story 2 rejection handling and rejection summaries
   - Developer C: User Story 3 blocked-outcome services and review-needed repository
3. Merge stories in priority order after each story passes its independent tests

---

## Notes

- All tasks follow the required checklist format with checkbox, task ID, story label where required, and file path
- `[P]` marks tasks that can be completed in parallel without waiting on another incomplete task in the same phase
- User Story 1 is the recommended MVP scope
- Tasks explicitly trace to UC-02 through the task title and UC-02-scoped story work
- No manual review, manual approval, or reprocessing workflow tasks are included
