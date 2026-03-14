# Data Model: Submit Feedback or Bug Report

## Overview

UC-19 introduces intake and review lineage for user feedback and bug reports while reusing existing authentication and operational logging capabilities from prior use cases. The design captures accepted submissions from anonymous or authenticated users, tracks downstream forwarding outcomes, and exposes reviewer-facing records without requiring direct dependency on external issue-tracker storage.

## New Entity: FeedbackSubmission

**Purpose**: Canonical record for each accepted user submission.

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `feedback_submission_id` | Identifier | Yes | Unique per accepted submission |
| `report_type` | Enum | Yes | Exactly one of `Feedback` or `Bug Report` |
| `description` | String | Yes | Non-empty; bounded max length |
| `contact_email` | String | No | Optional; if present must be valid email format |
| `submitter_kind` | Enum | Yes | `anonymous` or `authenticated` |
| `submitter_user_id` | Identifier | No | Required only when `submitter_kind = authenticated` |
| `processing_status` | Enum | Yes | `accepted`, `deferred_for_retry`, `forwarded`, or `forward_failed` |
| `submitted_at` | Timestamp | Yes | Creation timestamp |
| `last_status_at` | Timestamp | Yes | Last status transition timestamp |

**Validation rules**

- `report_type` is mandatory and restricted to one canonical value.
- `description` is required and must pass content validation before acceptance.
- `submitter_user_id` must be absent for anonymous submissions.
- Accepted records must start in `accepted` or `deferred_for_retry` based on forwarding attempt result timing.

## New Entity: SubmissionStatusEvent

**Purpose**: Immutable timeline of processing outcomes tied to one submission.

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `submission_status_event_id` | Identifier | Yes | Unique event ID |
| `feedback_submission_id` | Identifier | Yes | References `FeedbackSubmission` |
| `event_type` | Enum | Yes | `accepted`, `deferred_for_retry`, `forwarded`, `forward_failed` |
| `event_reason` | String | No | Required when event represents a failure or defer condition |
| `recorded_at` | Timestamp | Yes | Event timestamp |
| `correlation_id` | String | No | Optional tracing token for diagnostics |

**Validation rules**

- Every accepted submission must have at least one status event.
- Failure/defer events must include reason metadata.
- Events are append-only and ordered by `recorded_at`.

## New Entity: ReviewQueueRecord

**Purpose**: Reviewer-facing projection for authorized triage workflows.

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `review_queue_record_id` | Identifier | Yes | Unique review projection ID |
| `feedback_submission_id` | Identifier | Yes | References `FeedbackSubmission` |
| `visibility_status` | Enum | Yes | `visible`, `hidden`, `archived` |
| `triage_status` | Enum | Yes | `new`, `in_review`, `resolved`, `closed` |
| `assigned_reviewer_user_id` | Identifier | No | Optional reviewer assignment |
| `updated_at` | Timestamp | Yes | Last review-state update |

**Validation rules**

- Reviewer visibility requires authorized access at the API layer.
- `triage_status` transitions must be explicit and auditable.
- `ReviewQueueRecord` cannot exist without a corresponding accepted `FeedbackSubmission`.

## Relationships

- One `FeedbackSubmission` has many `SubmissionStatusEvent` records.
- One `FeedbackSubmission` has one `ReviewQueueRecord` projection for reviewer workflows.
- One reviewer may be assigned to many `ReviewQueueRecord` records.

## Canonical Vocabularies

- `report_type`: `Feedback`, `Bug Report`
- `submitter_kind`: `anonymous`, `authenticated`
- `processing_status`: `accepted`, `deferred_for_retry`, `forwarded`, `forward_failed`
- `triage_status`: `new`, `in_review`, `resolved`, `closed`
