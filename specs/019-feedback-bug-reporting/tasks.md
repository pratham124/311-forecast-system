# Tasks: Submit Feedback or Bug Report

**Input**: Design documents from `/specs/019-feedback-bug-reporting/`
**Prerequisites**: [plan.md](/home/asiad/ece493/311-forecast-system/specs/019-feedback-bug-reporting/plan.md), [spec.md](/home/asiad/ece493/311-forecast-system/specs/019-feedback-bug-reporting/spec.md), [research.md](/home/asiad/ece493/311-forecast-system/specs/019-feedback-bug-reporting/research.md), [data-model.md](/home/asiad/ece493/311-forecast-system/specs/019-feedback-bug-reporting/data-model.md), [feedback-reporting-api.yaml](/home/asiad/ece493/311-forecast-system/specs/019-feedback-bug-reporting/contracts/feedback-reporting-api.yaml), [quickstart.md](/home/asiad/ece493/311-forecast-system/specs/019-feedback-bug-reporting/quickstart.md)

**Tests**: Test tasks are not included because the feature specification does not explicitly request a TDD-first test task workflow.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when task files do not overlap and no incomplete dependency exists
- **[Story]**: User story label for traceability (`[US1]`, `[US2]`, `[US3]`)
- All tasks include exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create UC-19 module scaffolding for backend, frontend, and shared test locations.

- [ ] T001 Create backend feature module scaffolding in `backend/src/api/routes/feedback_submissions.py`, `backend/src/api/schemas/feedback_submissions.py`, `backend/src/services/feedback_intake_service.py`, `backend/src/services/feedback_forwarding_service.py`, `backend/src/services/feedback_review_service.py`, `backend/src/repositories/feedback_submission_repository.py`, and `backend/src/models/feedback_submission.py`
- [ ] T002 [P] Create frontend feature module scaffolding in `frontend/src/api/feedbackSubmissionsApi.ts`, `frontend/src/types/feedbackSubmissions.ts`, `frontend/src/features/feedback/components/FeedbackSubmissionForm.tsx`, `frontend/src/features/feedback/hooks/useFeedbackSubmission.ts`, and `frontend/src/pages/FeedbackSubmissionPage.tsx`
- [ ] T003 [P] Create reviewer feature scaffolding in `frontend/src/features/feedback-review/components/FeedbackSubmissionList.tsx`, `frontend/src/features/feedback-review/components/FeedbackSubmissionDetail.tsx`, `frontend/src/features/feedback-review/hooks/useFeedbackReview.ts`, and `frontend/src/pages/FeedbackReviewPage.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement core persistence, schema, auth boundaries, and contract-aligned status vocabulary required by all user stories.

**⚠️ CRITICAL**: User story implementation starts only after this phase is complete.

- [ ] T004 Implement domain models for `FeedbackSubmission`, `SubmissionStatusEvent`, and `ReviewQueueRecord` in `backend/src/models/feedback_submission.py`, `backend/src/models/submission_status_event.py`, and `backend/src/models/review_queue_record.py`
- [ ] T005 [P] Add schema migration for feedback entities and indexes in `backend/src/models/migrations/019_feedback_submission_entities.py`
- [ ] T006 [P] Implement repository CRUD and status-event append operations in `backend/src/repositories/feedback_submission_repository.py`
- [ ] T007 [P] Define request and response schemas with canonical vocabularies in `backend/src/api/schemas/feedback_submissions.py`
- [ ] T008 [P] Implement route-level auth dependencies for anonymous submission and reviewer-only reads in `backend/src/api/routes/feedback_submissions.py` and `backend/src/core/auth.py`
- [ ] T009 [P] Implement structured operational logging fields for submission, forwarding, and review access outcomes in `backend/src/core/logging.py` and `backend/src/services/feedback_intake_service.py`
- [ ] T010 [P] Implement typed frontend contract models that match backend schema vocabulary in `frontend/src/types/feedbackSubmissions.ts`
- [ ] T011 Implement API client methods for create/list/detail submission flows in `frontend/src/api/feedbackSubmissionsApi.ts`

**Checkpoint**: Shared data model, schema contracts, auth boundaries, and logging are ready.

---

## Phase 3: User Story 1 - Submit feedback successfully (Priority: P1) 🎯 MVP

**Goal**: Allow anonymous or authenticated users to submit valid feedback/bug reports and receive explicit success confirmation.

**Independent Test**: Submit a valid report with required fields and verify accepted outcome plus reviewer-visible stored submission with selected type and timestamp.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement form-level required field and report-type validation logic in `frontend/src/features/feedback/hooks/useFeedbackSubmission.ts` and `frontend/src/features/feedback/components/FeedbackSubmissionForm.tsx`
- [ ] T013 [P] [US1] Implement intake service validation and accepted-submission creation flow in `backend/src/services/feedback_intake_service.py`
- [ ] T014 [US1] Implement `POST /api/v1/feedback-submissions` endpoint behavior for accepted submissions in `backend/src/api/routes/feedback_submissions.py`
- [ ] T015 [P] [US1] Implement reviewer-list and reviewer-detail service methods for accepted submissions in `backend/src/services/feedback_review_service.py`
- [ ] T016 [US1] Implement reviewer `GET /api/v1/feedback-submissions` and `GET /api/v1/feedback-submissions/{feedbackSubmissionId}` endpoints in `backend/src/api/routes/feedback_submissions.py`
- [ ] T017 [P] [US1] Implement submission page user outcome messaging for accepted results in `frontend/src/pages/FeedbackSubmissionPage.tsx` and `frontend/src/features/feedback/components/FeedbackSubmissionForm.tsx`
- [ ] T018 [P] [US1] Implement reviewer list and detail page data loading in `frontend/src/features/feedback-review/hooks/useFeedbackReview.ts`, `frontend/src/pages/FeedbackReviewPage.tsx`, `frontend/src/features/feedback-review/components/FeedbackSubmissionList.tsx`, and `frontend/src/features/feedback-review/components/FeedbackSubmissionDetail.tsx`

**Checkpoint**: User Story 1 is independently functional and demonstrable.

---

## Phase 4: User Story 2 - Correct invalid input (Priority: P2)

**Goal**: Provide actionable validation errors for incomplete or malformed submissions and prevent invalid processing.

**Independent Test**: Submit forms with missing required fields and malformed values; verify specific corrective guidance and no accepted submission record.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Add explicit field-level validation error schema mapping in `backend/src/api/schemas/feedback_submissions.py` and `backend/src/services/feedback_intake_service.py`
- [ ] T020 [US2] Implement route-level invalid-request response mapping for submission validation failures in `backend/src/api/routes/feedback_submissions.py`
- [ ] T021 [P] [US2] Implement frontend error-message rendering for missing report type and invalid field values in `frontend/src/features/feedback/components/FeedbackSubmissionForm.tsx`
- [ ] T022 [US2] Implement submission hook handling for validation-failure response states and retry flow in `frontend/src/features/feedback/hooks/useFeedbackSubmission.ts`
- [ ] T023 [US2] Add repository guard path to avoid accepted-record persistence on validation failure in `backend/src/repositories/feedback_submission_repository.py` and `backend/src/services/feedback_intake_service.py`

**Checkpoint**: User Story 2 is independently functional and prevents invalid submissions from entering accepted flow.

---

## Phase 5: User Story 3 - Preserve reports during external failures (Priority: P3)

**Goal**: Retain accepted reports and provide truthful user outcomes when external issue-tracking forwarding is unavailable or fails.

**Independent Test**: Submit valid input while downstream forwarding is unavailable and verify retained submission, deferred status/event history, and delayed-processing user messaging.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement forwarding service integration adapter and failure classification in `backend/src/services/feedback_forwarding_service.py` and `backend/src/clients/issue_tracker_client.py`
- [ ] T025 [US3] Implement deferred status transition and status-event persistence for forwarding failures in `backend/src/services/feedback_intake_service.py` and `backend/src/repositories/feedback_submission_repository.py`
- [ ] T026 [P] [US3] Implement retry service workflow for deferred submissions in `backend/src/services/feedback_retry_service.py`
- [ ] T027 [US3] Implement user outcome mapping for accepted-with-delay and failure messaging in `backend/src/api/routes/feedback_submissions.py` and `frontend/src/pages/FeedbackSubmissionPage.tsx`
- [ ] T028 [P] [US3] Implement reviewer-detail visibility of status-event timeline for deferred/forward-failed states in `frontend/src/features/feedback-review/components/FeedbackSubmissionDetail.tsx` and `frontend/src/features/feedback-review/hooks/useFeedbackReview.ts`
- [ ] T029 [US3] Implement structured logging for integration outage, defer, retry, and forwarding terminal outcomes in `backend/src/core/logging.py`, `backend/src/services/feedback_forwarding_service.py`, and `backend/src/services/feedback_retry_service.py`

**Checkpoint**: User Story 3 is independently functional with failure-safe retention and traceable status history.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize traceability alignment, docs consistency, and implementation readiness checks across all stories.

- [ ] T030 [P] Align UC-19 quickstart implementation steps with completed task flow in `specs/019-feedback-bug-reporting/quickstart.md`
- [ ] T031 [P] Align API examples and status vocabulary consistency in `specs/019-feedback-bug-reporting/contracts/feedback-reporting-api.yaml`
- [ ] T032 [P] Resolve unchecked requirements-quality gaps by updating requirement text where needed in `specs/019-feedback-bug-reporting/spec.md`, `specs/019-feedback-bug-reporting/plan.md`, and `specs/019-feedback-bug-reporting/data-model.md`
- [ ] T033 Run end-to-end readiness validation against UC-19 scenarios in `specs/019-feedback-bug-reporting/spec.md`, `docs/UC-19.md`, and `docs/UC-19-AT.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user story work.
- **Phase 3 (US1)**: Depends on Phase 2 only and defines MVP scope.
- **Phase 4 (US2)**: Depends on Phase 2 and on US1 intake/validation flow reuse.
- **Phase 5 (US3)**: Depends on Phase 2 and on US1 accepted-submission pipeline.
- **Phase 6 (Polish)**: Depends on the selected user stories being completed.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational with no dependency on US2/US3.
- **US2 (P2)**: Depends on US1 submission flow surfaces but remains independently testable via invalid-input scenarios.
- **US3 (P3)**: Depends on US1 acceptance and persistence flow but remains independently testable via forwarding-failure scenarios.

### Explicit Task Prerequisites

- `T004` depends on `T001`.
- `T005` depends on `T004`.
- `T006` depends on `T004`.
- `T007` depends on `T004`.
- `T008` depends on `T001`.
- `T011` depends on `T007` and `T010`.
- `T013` depends on `T006` and `T007`.
- `T014` depends on `T008` and `T013`.
- `T016` depends on `T008` and `T015`.
- `T020` depends on `T019`.
- `T022` depends on `T021`.
- `T023` depends on `T006` and `T020`.
- `T025` depends on `T024`.
- `T026` depends on `T025`.
- `T027` depends on `T025`.
- `T029` depends on `T024` and `T026`.
- `T033` depends on `T031` and `T032`.

## Parallel Opportunities

- **Phase 1**: `T002` and `T003` can run in parallel after `T001`.
- **Phase 2**: `T005`, `T006`, `T007`, `T008`, `T009`, and `T010` can run in parallel after `T004`.
- **US1**: `T012`, `T013`, `T015`, and `T017` can run in parallel before endpoint and page integration tasks.
- **US2**: `T019` and `T021` can run in parallel, followed by `T020` and `T022`.
- **US3**: `T024` and `T028` can run in parallel; `T025` and `T029` follow once forwarding classification is in place.
- **Phase 6**: `T030`, `T031`, and `T032` can run in parallel.

## Parallel Example: User Story 1

```bash
Task: "Implement form-level required field and report-type validation logic in frontend/src/features/feedback/hooks/useFeedbackSubmission.ts and frontend/src/features/feedback/components/FeedbackSubmissionForm.tsx"
Task: "Implement intake service validation and accepted-submission creation flow in backend/src/services/feedback_intake_service.py"
Task: "Implement reviewer-list and reviewer-detail service methods for accepted submissions in backend/src/services/feedback_review_service.py"
Task: "Implement submission page user outcome messaging for accepted results in frontend/src/pages/FeedbackSubmissionPage.tsx and frontend/src/features/feedback/components/FeedbackSubmissionForm.tsx"
```

## Parallel Example: User Story 2

```bash
Task: "Add explicit field-level validation error schema mapping in backend/src/api/schemas/feedback_submissions.py and backend/src/services/feedback_intake_service.py"
Task: "Implement frontend error-message rendering for missing report type and invalid field values in frontend/src/features/feedback/components/FeedbackSubmissionForm.tsx"
```

## Parallel Example: User Story 3

```bash
Task: "Implement forwarding service integration adapter and failure classification in backend/src/services/feedback_forwarding_service.py and backend/src/clients/issue_tracker_client.py"
Task: "Implement reviewer-detail visibility of status-event timeline for deferred/forward-failed states in frontend/src/features/feedback-review/components/FeedbackSubmissionDetail.tsx and frontend/src/features/feedback-review/hooks/useFeedbackReview.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate US1 independent test and review workflow visibility.

### Incremental Delivery

1. Deliver US1 for baseline submission and reviewer retrieval.
2. Add US2 for validation-quality and correction flow robustness.
3. Add US3 for forwarding-failure resilience and deferred processing transparency.
4. Apply Phase 6 polish and readiness validation.

### Parallel Team Strategy

1. One engineer handles backend domain/repository/auth setup while another handles frontend typing and page scaffolding.
2. After Foundation, backend intake/forwarding and frontend form/reviewer flows can proceed concurrently.
3. US2 and US3 can be split by concern (validation vs resilience) once US1 pipeline is stable.

---

## Notes

- All tasks follow the required checklist format with task IDs, optional `[P]` markers, `[US#]` labels for story phases, and file paths.
- Tasks are organized for independent story implementation and validation.
- MVP scope is explicitly US1 (Phase 3).
