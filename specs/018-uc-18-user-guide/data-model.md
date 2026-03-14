# Data Model: Access User Guide

## Overview

UC-18 introduces a small set of user-guide delivery and observability models. The feature reuses the platform’s authenticated user context and documentation storage without redefining those upstream concerns, then adds normalized guide-content and access-event models required to support readable display, section navigation, retrieval-failure handling, and render-failure handling.

## Reused Shared Entities and Context

UC-18 depends on shared platform concepts that are not redefined here:

- Authenticated user identity and session context from the platform’s backend authentication layer
- Existing help or user-guide entry points embedded in product screens
- Documentation storage or service that holds the current published user guide content
- Shared structured logging and operational correlation conventions

## Canonical UC-18 Vocabulary

### Guide Outcome

- `retrieved`
- `retrieval_failed`
- `rendered`
- `render_failed`

### Failure Category

- `guide_unavailable`
- `guide_render_failed`

### Guide Status

- `available`
- `unavailable`
- `error`

## Reused Source Entity: UserGuideContent

**Purpose**: Represents the current published user guide content that is made available to signed-in users.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `guide_content_id` | Identifier | Yes | Unique identifier for the current published guide |
| `title` | String | Yes | Human-readable guide title |
| `published_at` | Timestamp | Yes | Time the current guide became the published guide |
| `body` | Rich text | Yes | Full instructional content prepared for readable display |
| `sections` | Collection | Yes | Ordered set of available sections or pages |
| `status` | Enum | Yes | Must be `available` for the active guide |

**Validation rules**

- Only one `UserGuideContent` record may be the current published guide at a time.
- `sections` must be ordered and must cover every navigable section or page presented to users.
- `body` and `sections` must be derived from the same published guide version.
- `status` for the current guide must be `available`.

## New Entity: GuideSection

**Purpose**: Represents one navigable section or page within the current published guide.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `guide_content_id` | Identifier | Yes | References the current published guide |
| `section_id` | Identifier | Yes | Unique within one guide |
| `label` | String | Yes | User-facing section or page title |
| `order_index` | Integer | Yes | Determines navigation order |
| `content_excerpt` | Rich text | No | Optional section-specific content fragment if the guide is served in parts |
| `anchor_target` | String | No | Stable in-guide navigation target when applicable |

**Validation rules**

- `section_id` must be unique within the guide identified by `guide_content_id`.
- `order_index` values must form a consistent navigation order without duplicates.
- `label` must be present for every section users can navigate to.
- `anchor_target`, when present, must map to a stable navigation target inside the guide content.

## New Entity: GuideAccessEvent

**Purpose**: Records one attempt by a signed-in user to open the user guide, including successful retrieval and retrieval-failure outcomes.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `guide_access_event_id` | Identifier | Yes | Unique per guide-open attempt |
| `guide_content_id` | Identifier | No | Present when a guide was successfully resolved |
| `user_id` | Identifier | Yes | References the signed-in user who opened the guide |
| `entry_point` | String | Yes | Identifies the product surface where the guide was opened |
| `requested_at` | Timestamp | Yes | Time the guide-open request began |
| `outcome` | Enum | Yes | `retrieved`, `retrieval_failed`, `rendered`, or `render_failed` |
| `failure_category` | Enum | No | Required when `outcome` is a failure |
| `failure_message` | String | No | User-facing explanation for failure cases |
| `completed_at` | Timestamp | No | Required when the attempt reaches a terminal outcome |
| `correlation_id` | String | No | Shared operational identifier when supported |

**Validation rules**

- `user_id` must belong to an authenticated session.
- `guide_content_id` is required when `outcome` is `retrieved`, `rendered`, or `render_failed`.
- `failure_category` and `failure_message` are required when `outcome` is `retrieval_failed` or `render_failed`.
- `completed_at` is required for terminal outcomes.
- `failure_message` must explain that the guide is unavailable and that the problem is not caused by normal user navigation.

## New Derived Entity: UserGuideView

**Purpose**: Represents the stable backend-to-frontend payload used to render the current published guide or an explicit error state.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `guide_access_event_id` | Identifier | Yes | Links the payload to one guide-open attempt |
| `status` | Enum | Yes | `available`, `unavailable`, or `error` |
| `title` | String | No | Required when `status = available` |
| `published_at` | Timestamp | No | Required when `status = available` |
| `body` | Rich text | No | Required when `status = available` |
| `sections` | Collection | No | Required when `status = available` |
| `status_message` | String | No | Required when `status = unavailable` or `status = error` |
| `entry_point` | String | Yes | Echoes where the guide was opened from |

**Validation rules**

- `title`, `published_at`, `body`, and `sections` are required when `status = available`.
- `status_message` is required when `status = unavailable` or `status = error`.
- `body` and `sections` must not be present when `status = unavailable` or `status = error`.
- `status_message` must distinguish unavailable content from normal user navigation.
- `sections` must use the ordered `GuideSection` structure.

## New Derived Entity: GuideRenderOutcome

**Purpose**: Captures the final client-visible rendering result after the backend has returned a guide payload.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `guide_access_event_id` | Identifier | Yes | References one guide-open attempt |
| `render_outcome` | Enum | Yes | `rendered` or `render_failed` |
| `reported_at` | Timestamp | Yes | Time the frontend reported the render result |
| `failure_message` | String | No | Required when `render_outcome = render_failed` |

**Validation rules**

- `guide_access_event_id` must reference an existing `GuideAccessEvent` with a retrieved guide payload.
- `failure_message` is required when `render_outcome = render_failed`.
- `failure_message` must not imply that the user caused the error through normal guide navigation.

## Relationships

- One `UserGuideContent` record may have many `GuideSection` rows.
- One signed-in user may create many `GuideAccessEvent` rows over time.
- One `GuideAccessEvent` may produce zero or one `GuideRenderOutcome`.
- One successful `GuideAccessEvent` produces exactly one `UserGuideView` payload for the requesting client.

## Derived Invariants

- UC-18 must never expose the guide to unsigned users.
- Only one guide may be the current published guide at a time.
- A guide retrieval failure must never return blank, stale, or partial guide content.
- A render failure must never expose corrupted or partially rendered content as a successful guide view.
- Navigation uses only the ordered sections or pages returned for the current published guide.
