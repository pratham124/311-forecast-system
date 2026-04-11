# Data Model: Weather-Aware Forecasting and Storm-Mode Alerting

## Overview

UC-15 is modeled as a **behavioral alignment layer** across shared forecasting and alerting concepts rather than as a standalone storm-mode data subsystem.

The key clarification is that **storm mode in UC-15 is equivalent to the surge/anomaly operational state from UC-11**. UC-15 therefore reuses existing shared lineage concepts and avoids introducing a second storm-mode state model.

## Reused Shared Entities and Vocabulary

UC-15 reuses shared concepts without redefining upstream entities:

- Forecast lineage and forecast outputs (including uncertainty-oriented outputs)
- Weather-context inputs used by forecast behavior
- Surge/anomaly confirmation state as the canonical storm-mode state
- Alert evaluation outcomes under baseline or storm-mode-aware context
- Notification outcomes including successful delivery, retry-eligible status, and manual follow-up status
- Operational traceability concepts (run context, timestamps, correlation context, and review records)

## Canonical UC-15 Vocabulary

### Storm Mode State

- `active` (equivalent to confirmed surge/anomaly state)
- `inactive`

### Forecast Behavior Context

- `weather_aware`
- `baseline_compatible`

### Alert Behavior Context

- `storm_mode_aware`
- `baseline`

### Notification Follow-Up Status

- `delivered`
- `retry_pending`
- `manual_review_required`
- `failed`

## UC-15 Modeling Decision

UC-15 introduces **no mandatory new independent entity set** for storm mode. Instead, UC-15 requires:

1. Weather-aware forecast behavior to remain observable for supported scenarios.
2. Storm mode references to map to the same surge/anomaly state used by UC-11.
3. Alert and notification outcomes to remain traceable under that shared state.

## Derived Read Models (Conceptual)

The following conceptual read views remain sufficient for UC-15 acceptance and operations review:

### WeatherAwareForecastReview

**Purpose**: Summarize whether forecast behavior for a scenario was weather-aware or baseline-compatible.

Representative fields:

- `review_context_id`
- `evaluated_scope`
- `forecast_behavior_context` (`weather_aware` or `baseline_compatible`)
- `weather_context_status` (`available`, `unavailable`, `unusable`)
- `recorded_at`

### StormModeOperationalReview

**Purpose**: Summarize storm-mode (UC-11 equivalent) state and downstream alert/notification outcomes for review.

Representative fields:

- `review_context_id`
- `storm_mode_state` (`active` or `inactive`)
- `storm_mode_source` (`uc11_surge_state`)
- `alert_behavior_context` (`storm_mode_aware` or `baseline`)
- `notification_follow_up_status`
- `recorded_at`

## Relationships

- One operational review context may include one weather-aware forecast review and one or more storm-mode operational review outcomes.
- Storm-mode operational review outcomes must reference the shared surge/anomaly state semantics.
- Notification follow-up outcomes remain linked to alert outcomes and must remain reviewable.

## Derived Invariants

- UC-15 must not define a second independent storm-mode state that conflicts with UC-11.
- Storm mode terminology in UC-15 must always resolve to the UC-11 surge/anomaly operational state.
- Weather-unavailable or weather-unusable conditions must map to baseline-compatible forecast behavior.
- Storm-mode-aware alert behavior must be applied only when shared storm mode is active for the evaluated scope.
- Notification delivery and follow-up outcomes must remain traceable under one operational context.
