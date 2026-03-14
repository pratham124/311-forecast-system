# Quickstart: Storm Mode Forecast Adjustments

## Purpose

Use this guide to implement and verify UC-15 as a backend-driven storm-mode workflow that monitors approved weather signals, validates storm triggers for the affected scope, activates storm mode only when validation succeeds, widens forecast uncertainty and increases alert sensitivity only where allowed, reuses the existing notification workflow for alert delivery, and degrades safely to baseline behavior when weather data is unavailable, triggers are rejected, forecast adjustment fails, or notification delivery fails.

## Implementation Outline

1. Reuse shared lineage and vocabulary from prior use cases without redefining those entities:
   - UC-01 and UC-02 approved demand lineage
   - UC-03 and UC-04 retained forecast lineage
   - UC-09 approved weather-provider and geography-alignment conventions
   - UC-10 and UC-11 shared alert-notification and delivery-status records
   - UC-12 through UC-14 authenticated observability and typed diagnostic patterns
   - shared authentication, authorization, and structured logging conventions used across the platform
2. Add only UC-15-specific persistence:
   - `StormModeEvaluationRun`
   - `StormModeTriggerAssessment`
   - `StormModeActivation`
   - `StormModeForecastAdjustment`
   - `StormModeAlertEvaluation`
3. Build one backend storm-mode path that:
   - monitors approved weather inputs on the configured evaluation path
   - detects candidate storm conditions and validates them against business criteria
   - activates storm mode only for the affected category, optional geography, and time window
   - widens uncertainty for linked forecast outputs when adjustment succeeds
   - reverts both uncertainty and alert sensitivity to baseline when adjustment fails
   - applies more sensitive alert parameters only for scopes that qualify
   - creates alerts through the existing shared notification workflow when storm-adjusted logic determines an alert is needed
   - persists one correlated run, trigger, activation, forecast-adjustment, and alert-evaluation trail
4. Keep route handlers thin:
   - authenticated `GET` endpoints for current storm-mode activations and detailed evaluation diagnostics
   - all monitoring, validation, activation, adjustment, and linkage logic in pipelines and services
   - all persistence in repositories
5. Keep downstream integration bounded:
   - existing forecast-generation and alerting services remain the execution owners
   - UC-15 injects validated storm-mode parameters into those services rather than replacing them
   - existing notification records remain the source of truth for delivery attempts and retry state

## Acceptance Alignment

Map implementation and tests directly to [UC-15](/Users/sahmed/Documents/311-forecast-system/docs/UC-15.md) and [UC-15-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-15-AT.md):

- AT-01 and AT-02: monitor weather feeds, detect candidate severe conditions, validate them, and activate storm mode only for affected scopes
- AT-03 and AT-05: widen forecast uncertainty for the same affected scope and make the storm influence inspectable
- AT-04 and AT-06: apply more sensitive alert parameters where allowed and verify the effective parameters differ from baseline in the intended direction
- AT-07 and AT-08: create alerts through the existing notification workflow and preserve a full correlated lifecycle record
- AT-09 and AT-10: keep the system on baseline behavior when weather data is unavailable or a candidate trigger is rejected
- AT-11: revert forecast uncertainty and alert sensitivity to baseline when storm-mode adjustment fails
- AT-12: preserve notification failure and retry-eligible state through the shared notification workflow

## Suggested Test Layers

- Unit tests for weather-trigger normalization, storm-criteria validation, scope matching, activation-state derivation, uncertainty-widening selection, baseline reversion, and alert-sensitivity derivation
- Integration tests across weather retrieval, trigger assessment persistence, activation persistence, forecast-adjustment linkage, alert-evaluation linkage, and shared notification-event references
- Contract tests for [storm-mode-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/015-uc-15-weather-storm-mode/contracts/storm-mode-api.yaml)
- Acceptance-style tests for validated activation, weather-unavailable fallback, rejected-trigger fallback, forecast-adjustment failure, and notification-delivery retry state

## Exit Conditions

Implementation is ready for task breakdown when:

- storm mode activates only after validated trigger assessment for the affected scope
- unaffected scopes always remain on baseline uncertainty and baseline alert sensitivity
- effective uncertainty and alert-sensitivity parameters are inspectable through persisted records or authenticated diagnostics
- forecast-adjustment failure forces both uncertainty and alert sensitivity back to baseline for the same scope
- linked notification outcomes reuse the existing delivery-status source of truth instead of duplicating notification persistence
- successful and failure-path evaluations remain traceable through one run-level correlation context
