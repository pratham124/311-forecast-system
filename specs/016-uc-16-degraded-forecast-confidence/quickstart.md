# Quickstart: Indicate Degraded Forecast Confidence in UI

## Purpose

Use this guide to implement and verify UC-16 as an authenticated operational-manager workflow that augments the existing forecast view with a degraded-confidence indicator when centralized rules confirm elevated uncertainty, suppresses misleading warnings when signals are missing or dismissed as non-material, and records traceable preparation and render outcomes for every request.

## Implementation Outline

1. Reuse shared lineage and vocabulary from prior use cases without redefining those entities:
   - UC-03 and UC-04 retained forecast lineage
   - UC-05 forecast-visualization context and frontend display conventions
   - UC-06 through UC-09 evaluation, anomaly, and weather-alignment signals that may contribute confidence evidence
   - UC-10 through UC-14 authenticated access and interactive observability patterns
   - UC-15 storm-mode or weather-driven diagnostic context when it contributes to degraded-confidence reasons
   - shared authentication, authorization, and structured logging conventions used across the platform
2. Add only UC-16-specific persistence:
   - `ForecastConfidenceRequest`
   - `ForecastConfidenceSignalResolution`
   - `ForecastConfidenceAssessmentResult`
   - `ForecastConfidenceRenderEvent`
3. Build one backend confidence-status path that:
   - resolves the forecast scope for the current view
   - loads the forecast context required for the view without duplicating the forecast source
   - retrieves confidence or quality signals for the same scope when they are available
   - applies one centrally managed degraded-confidence and materiality rule set
   - prepares one typed confidence-display result with explicit degraded, normal, missing-signal, dismissed, or error semantics
   - persists request, signal-resolution, prepared-result, and render-event observability
4. Keep route handlers thin:
   - one authenticated `GET` endpoint for loading the normalized confidence-display state
   - one authenticated `POST` endpoint for reporting final render success or failure
   - all forecast-context resolution, signal normalization, rule evaluation, and status derivation in services
   - all persistence in repositories
5. Keep frontend integration bounded:
   - request confidence status as part of the forecast-view experience for authorized users
   - show a clear degraded-confidence indicator only when `indicatorState = display_required`
   - keep the forecast visible when confidence signals are missing, dismissed, or the indicator render fails
   - show generic explanatory reason categories such as missing inputs, shock, or anomaly when supplied
   - report the final render outcome back to the backend for observability

## Acceptance Alignment

Map implementation and tests directly to [UC-16](/Users/sahmed/Documents/311-forecast-system/docs/UC-16.md) and [UC-16-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-16-AT.md):

- AT-01: load the forecast visualization for an authorized operational manager without blocking errors
- AT-02: retrieve forecast context and associated confidence or quality signals for the same scope
- AT-03: detect degraded confidence from supported signal categories and log the detection outcome
- AT-04 and AT-05: prepare and display a clear degraded-confidence indicator alongside the forecast without blocking forecast access
- AT-06: preserve traceable detection and display outcomes for the same request or correlation context
- AT-07: log missing signals and show the forecast without a misleading warning
- AT-08: dismiss non-material candidate degradation signals and keep the forecast display normal
- AT-09: log indicator render failure and allow the forecast to remain viewable without falsely recording successful warning display

## Suggested Test Layers

- Unit tests for scope resolution, signal normalization, centralized rule evaluation, reason-category derivation, and confidence-view status mapping
- Integration tests across request persistence, signal-resolution outcomes, prepared-result persistence, missing-signal fallback, dismissed-signal fallback, and render-event handling
- Contract tests for [degraded-forecast-confidence-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/016-uc-16-degraded-forecast-confidence/contracts/degraded-forecast-confidence-api.yaml)
- Frontend interaction tests for degraded-warning display, normal display, missing-signal messaging, dismissed-signal behavior, and indicator render-failure handling

## Exit Conditions

Implementation is ready for task breakdown when:

- authorized users can load confidence status for the same scope shown in the forecast view
- degraded-confidence warnings appear only when centralized rules confirm material degradation
- missing signals and dismissed signals both suppress warnings while remaining distinguishable in observability
- user-facing reason categories remain clear, generic, and stable
- forecast access remains available when signals are unavailable or the indicator fails to render
- final client render outcomes are traceable without mutating the prepared assessment result
