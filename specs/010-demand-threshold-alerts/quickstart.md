# Quickstart: Demand Threshold Alerts

## Purpose

Use this guide to implement and verify UC-10 as a threshold-crossing alert flow that evaluates published forecast demand, suppresses duplicate alerts until re-armed, attempts all configured channels for each alert, and preserves traceable outcomes for success, suppression, configuration gaps, and delivery failures.

## Implementation Outline

1. Reuse upstream forecast lineage:
   - `ForecastRun`
   - `ForecastVersion` or `WeeklyForecastVersion`
   - `ForecastBucket` or `WeeklyForecastBucket`
2. Add UC-10-specific persistence:
   - `ThresholdConfiguration`
   - `ThresholdEvaluationRun`
   - `ThresholdScopeEvaluation`
   - `ThresholdState`
   - `NotificationEvent`
   - `NotificationChannelAttempt`
3. Build one backend evaluation path that:
   - accepts a published or refreshed forecast reference
   - resolves the applicable threshold for each category and optional geography scope
   - compares forecast values against thresholds
   - creates alert events only on threshold-crossing transitions
   - suppresses duplicate alerts while the same scope remains above threshold
   - attempts all configured channels for each alert
   - treats the alert as delivered when at least one channel succeeds
   - records failed channels for follow-up and records total failures for retry or manual review
4. Keep route handlers thin:
   - evaluation-trigger endpoint for protected operational use
   - alert-event retrieval endpoints for operational review
   - all threshold precedence, suppression, and delivery decisions in services
   - all persistence in repositories
5. Keep frontend integration bounded:
   - consume only normalized backend alert contracts
   - show overall delivery state plus channel-attempt detail where operational review needs it
   - do not implement security-sensitive authorization on the client

## Acceptance Alignment

Map implementation and tests directly to [UC-10](/root/311-forecast-system/docs/UC-10.md) and [UC-10-AT.md](/root/311-forecast-system/docs/UC-10-AT.md):

- AT-01: forecast update triggers threshold evaluation
- AT-02: category-only exceedance creates a notification event with category, forecast value, threshold value, and time window
- AT-03: category-plus-geography exceedance produces a scoped alert only for the exceeding region
- AT-04 and AT-05: at least one successful configured channel marks the alert delivered and logs the successful outcome
- AT-06: missing thresholds record a configuration issue and do not send an alert
- AT-07: values below or equal to threshold produce no notification
- AT-08: total delivery failure records the failure and places the alert in retry or manual review follow-up
- Clarification-backed behavior: duplicate alerts are suppressed until the same scope returns to or below threshold and later exceeds again
- Clarification-backed behavior: all configured channels are attempted, and failed channels are still recorded when another channel succeeds

## Suggested Test Layers

- Unit tests for threshold selection precedence, equal-to-threshold handling, threshold-state transitions, duplicate suppression, and overall delivery-status aggregation
- Integration tests across forecast lineage lookup, threshold resolution, alert-event creation, channel-attempt persistence, and retry/manual-review marking
- Contract tests for [threshold-alerts-api.yaml](/root/311-forecast-system/specs/010-demand-threshold-alerts/contracts/threshold-alerts-api.yaml)
- Frontend interaction tests for authenticated alert-status viewing and channel-failure trace presentation when UI surfaces them

## Implemented File Map

| Layer | File | Purpose |
|---|---|---|
| Pipeline | `backend/app/pipelines/threshold_alert_evaluation_pipeline.py` | Orchestrates evaluation, threshold lookup, suppression, delivery, persistence |
| Service | `backend/app/services/threshold_alert_service.py` | Threshold-crossing decision and state transitions |
| Service | `backend/app/services/threshold_selection_service.py` | Category + geography precedence resolution |
| Service | `backend/app/services/notification_delivery_service.py` | Multi-channel delivery with status aggregation |
| Service | `backend/app/services/forecast_scope_service.py` | Daily/weekly forecast scope extraction |
| Service | `backend/app/services/alert_review_service.py` | Alert event list/detail queries |
| Repository | `backend/app/repositories/threshold_configuration_repository.py` | Threshold CRUD with geography precedence |
| Repository | `backend/app/repositories/threshold_evaluation_repository.py` | Evaluation run and scope evaluation persistence |
| Repository | `backend/app/repositories/threshold_state_repository.py` | Threshold state upsert and re-arm tracking |
| Repository | `backend/app/repositories/notification_event_repository.py` | Alert event and channel attempt persistence |
| Model | `backend/app/models/threshold_alert_models.py` | SQLAlchemy models for all UC-10 tables |
| Migration | `backend/migrations/versions/017_uc10_threshold_alerts.py` | Schema migration |
| Routes | `backend/app/api/routes/forecast_alerts.py` | REST endpoints (trigger + review) |
| Schemas | `backend/app/schemas/forecast_alerts.py` | Pydantic request/response models |
| Frontend | `frontend/src/pages/ForecastAlertsPage.tsx` | Alert review UI with role gating |
| Frontend | `frontend/src/api/forecastAlerts.ts` | API client for alert endpoints |
| Frontend | `frontend/src/types/forecastAlerts.ts` | TypeScript alert types |

## Operational Usage

### Triggering an Evaluation

```
POST /api/v1/forecast-alerts/evaluations
Authorization: Bearer <OperationalManager token>
Content-Type: application/json

{
  “forecast_reference_id”: “<forecast-version-id>”,
  “forecast_product”: “daily”,
  “trigger_source”: “manual_replay”
}
```

### Reviewing Alert History

```
GET /api/v1/forecast-alerts/events
Authorization: Bearer <CityPlanner or OperationalManager token>
```

### Reviewing Alert Detail

```
GET /api/v1/forecast-alerts/events/<notification_event_id>
Authorization: Bearer <CityPlanner or OperationalManager token>
```

## Exit Conditions

Implementation is complete when:

- UC-10 reads only published forecast lineage and configured thresholds as alert inputs
- Threshold selection applies category-plus-geography precedence over category-only (FR-011a)
- Duplicate alerts are suppressed only while a scope remains above threshold and are re-armed when the scope returns to or below threshold (FR-013)
- Multi-channel delivery records every configured channel attempt and uses “at least one success” as the overall delivered rule (FR-007a/b/c)
- Missing-threshold, below-threshold, suppressed, delivered, partial-delivery, and total-failure outcomes remain explicitly distinguishable
- Alert retrieval contracts are typed and authenticated
- Operational records preserve enough detail to diagnose configuration issues, failed channels, and retry/manual-review cases
- Equal-to-threshold values do not trigger alerts (FR-009)
