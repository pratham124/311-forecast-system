# Quickstart: Abnormal Demand Surge Notifications

## Purpose

Use this guide to implement and verify UC-11 as an ingestion-triggered surge-alert flow that compares newly ingested actual demand to active LightGBM P50 forecasts, confirms abnormal surges with a dual-threshold residual rule, suppresses duplicate notifications while a scope remains in surge state, and preserves traceable outcomes for filtered candidates, detector failures, and delivery failures.

## Implementation Outline

1. Reuse shared lineage and vocabulary from prior use cases without redefining those entities:
   - UC-01: `IngestionRun`, `DatasetVersion`
   - UC-02: approved cleaned-dataset lineage only where historical residual context depends on approved demand views
   - UC-03 and UC-04: `ForecastRun`, `ForecastVersion`, `ForecastBucket`, `CurrentForecastMarker`, `WeeklyForecastRun`, `WeeklyForecastVersion`, `WeeklyForecastBucket`, `CurrentWeeklyForecastMarker`
   - UC-10: delivery-status vocabulary and notification-review expectations only
2. Add UC-11-specific persistence:
   - `SurgeDetectionConfiguration`
   - `SurgeEvaluationRun`
   - `SurgeCandidate`
   - `SurgeConfirmationOutcome`
   - `SurgeState`
   - `SurgeNotificationEvent`
   - `SurgeNotificationChannelAttempt`
3. Build one backend evaluation path that:
   - starts immediately after a successful UC-01 ingestion run completes
   - aggregates newly ingested actual demand to the canonical service-category and optional-geography scope
   - resolves the active LightGBM P50 forecast for the same scope
   - computes residual, rolling-baseline z-score, and percent-above-forecast
   - treats positive actual demand over a zero P50 forecast as passing the percent-above-forecast floor while allowing the numeric percent metric to remain null
   - creates a candidate only when the anomaly gate is crossed
   - confirms a surge only when both configured confirmation thresholds pass
   - creates a notification only when the scope newly enters confirmed surge state
   - suppresses repeat notifications while that same scope remains in surge state
   - re-arms notification eligibility only after the scope returns to normal
   - records all configured channel attempts and reviewable delivery outcomes
4. Keep route handlers thin:
   - manual-replay trigger endpoint for protected operational use and acceptance testing
   - surge-evaluation retrieval endpoints for operational review of detector-failed, filtered, suppressed, and zero-notification runs
   - surge-event retrieval endpoints for operational review of confirmed notifications and delivery outcomes
   - all residual, confirmation, suppression, and delivery decisions in services
   - all persistence in repositories
5. Keep frontend integration bounded:
   - consume only normalized backend surge-alert contracts
   - show confirmation metrics and overall delivery state plus channel-attempt detail where review needs it
   - do not implement security-sensitive authorization on the client

## Acceptance Alignment

Map implementation and tests directly to [UC-11](/Users/sahmed/Documents/311-forecast-system/docs/UC-11.md) and [UC-11-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-11-AT.md):

- AT-01: ingestion-linked demand monitoring produces evaluated surge candidates
- AT-02: a detector spike is confirmed before any notification is created
- AT-03: confirmed surges create a notification event with category, optional geography, surge magnitude, and detection or confirmation time
- AT-04 and AT-05: successful delivery reaches the operational manager and is logged with correlated review data
- AT-06: detector processing errors are logged and do not create notifications
- AT-07: filtered false positives produce no notification event
- AT-08: delivery failures leave a traceable follow-up state for retry or manual review
- Clarification-backed behavior: repeated confirmed evaluations for an already-active surge scope do not send additional notifications until the scope returns to normal

## Suggested Test Layers

- Unit tests for residual calculation, rolling-baseline z-score calculation, dual-threshold confirmation, surge-state transitions, and delivery-status aggregation
- Integration tests across ingestion-run lookup, active-forecast resolution, candidate creation, confirmation persistence, surge-state updates, and channel-attempt persistence
- Contract tests for [surge-alerts-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/011-abnormal-demand-surge-notifications/contracts/surge-alerts-api.yaml)
- Frontend interaction tests for authenticated surge-evaluation review, surge-event review, and failed-channel trace presentation when UI surfaces them

## Exit Conditions

Implementation is ready for task breakdown when:

- UC-11 reads only successful ingestion outputs, active forecast lineage, and surge-specific configuration as alert inputs
- Surge confirmation requires both configured thresholds for the same scope and evaluation
- Duplicate notifications are suppressed only while a scope remains in confirmed surge state and re-arm only after return to normal
- Detector-failed, filtered, suppressed, delivered, partial-delivery, retry-pending, and manual-review-required outcomes remain explicitly distinguishable
- Review APIs expose non-notification evaluation outcomes as structured data rather than requiring raw-log inspection
- Surge retrieval contracts are typed and authenticated
- Operational records preserve enough detail to diagnose detector errors, filtered candidates, failed channels, and retry or manual-review cases
