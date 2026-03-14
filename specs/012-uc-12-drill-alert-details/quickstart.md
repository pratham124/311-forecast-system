# Quickstart: Drill Alert Details and Context

## Purpose

Use this guide to implement and verify UC-12 as an authenticated alert drill-down flow that loads forecast distribution context, the top 5 contributing drivers, and the previous 7 days of anomaly context for one selected alert, while preserving explicit partial and error semantics plus end-to-end observability.

## Implementation Outline

1. Reuse shared lineage and vocabularies from prior use cases without redefining those entities:
   - UC-05 and UC-09 for charting and normalized visualization patterns
   - UC-10 `NotificationEvent` lineage for threshold-alert drill-down
   - UC-11 `SurgeNotificationEvent` lineage for surge-alert drill-down
   - shared authentication, role-aware access, and structured logging conventions already established in the platform
2. Add only UC-12-specific persistence and read models:
   - `AlertDetailLoadRecord`
   - `ForecastDistributionContext`
   - `DriverAttributionContext`
   - `AnomalyContextWindow`
   - `AlertDetailView`
3. Build one backend detail-load path that:
   - accepts a selected upstream alert id and alert source
   - records a new detail-load attempt before retrieval begins
   - resolves the selected alert to its canonical scope and time context
   - retrieves forecast distribution support data for that alert
   - retrieves driver attribution support data and trims output to the top 5 ranked drivers
   - retrieves anomaly context bounded to the previous 7 days
   - normalizes component results into canonical `available`, `unavailable`, or `failed` statuses
   - prepares one stable `AlertDetailView` payload with `rendered`, `partial`, or `error` semantics
   - persists final retrieval and preparation outcomes on the load record
4. Keep route handlers thin:
   - one authenticated `GET` endpoint for retrieving alert-detail context by alert source and alert id
   - one authenticated `POST` endpoint for recording final render outcomes for observability
   - all alert lookup, context retrieval, normalization, and state assignment in services
   - all persistence in repositories
5. Keep frontend integration bounded:
   - show selected alert metadata immediately while the detail view loads
   - render all three components together when `viewStatus = rendered`
   - render only reliable components with explicit unavailable messaging when `viewStatus = partial`
   - show an error state instead of any misleading partial or corrupted view when `viewStatus = error`
   - report final render success or render failure back to the backend using the load id returned in the detail payload

## Acceptance Alignment

Map implementation and tests directly to [UC-12](/Users/sahmed/Documents/311-forecast-system/docs/UC-12.md) and [UC-12-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-12-AT.md):

- AT-01 through AT-04: selected alert is identifiable and each supporting component is retrieved with traceable logging
- AT-05: backend preparation combines retrieved context into a visualization-ready shape
- AT-06 and AT-07: the complete view renders coherently and logs retrieval, preparation, and render success
- AT-08 through AT-10: one missing component at a time produces a truthful partial view rather than an empty chart
- accepted clarification-backed behavior: if two or more components are unavailable but one reliable component remains, the remaining context is still shown with each unavailable component clearly marked
- AT-11 and AT-12: retrieval failure and render failure both produce a full error state with correlated failure logging

## Suggested Test Layers

- Unit tests for alert-source resolution, top-5 driver trimming, 7-day anomaly-window bounding, component-status assignment, and overall view-status derivation
- Integration tests across alert lookup, source-context retrieval, load-record persistence, partial-view assembly, and error-path observability
- Contract tests for [alert-detail-context-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/012-uc-12-drill-alert-details/contracts/alert-detail-context-api.yaml)
- Frontend interaction tests for loading, rendered, partial, and error states plus render-event reporting

## Exit Conditions

Implementation is ready for task breakdown when:

- UC-12 reads existing alert lineage rather than creating a new alert source of truth
- the backend payload always keeps the selected alert identified
- driver attribution is limited to the top 5 ranked contributors
- anomaly context is limited to the previous 7 days
- partial views never present unavailable components as unlabeled empty visualizations
- retrieval failures and render failures remain explicitly distinguishable from missing-component partial views
- observability records preserve enough detail to trace component retrieval, preparation, final render outcome, and any failure category for the selected alert
