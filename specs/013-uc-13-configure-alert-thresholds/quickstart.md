# Quickstart: Configure Alert Thresholds and Notification Channels

## Purpose

Use this guide to implement and verify UC-13 as an authenticated shared-configuration flow that loads the one active alert policy, lets an operational manager update threshold rules, supported channel selections, and scoped frequency or deduplication preferences, and safely activates a new configuration version only after validation succeeds.

## Implementation Outline

1. Reuse shared lineage and vocabularies from prior use cases without redefining those entities:
   - UC-10 threshold-alert evaluation and notification semantics
   - UC-11 surge-alert lineage where cross-feature alert behavior vocabulary is reused
   - UC-12 observability conventions for explicit success and failure outcomes
   - shared authentication, role-aware access, and structured logging conventions already established in the platform
2. Add only UC-13-specific persistence:
   - `AlertConfigurationVersion`
   - `ActiveAlertConfigurationMarker`
   - `AlertConfigurationThresholdRule`
   - `AlertConfigurationChannelSelection`
   - `AlertConfigurationDeliveryPreference`
   - `AlertConfigurationUpdateAttempt`
3. Build one backend configuration path that:
   - loads the active configuration marker and expands the active version into a frontend-ready payload
   - resolves the platform-supported notification channel options shown to the manager
   - accepts threshold rules by service category and optional geography
   - accepts one or more selected supported channels
   - accepts scoped frequency controls, deduplication controls, or both
   - validates threshold ranges, channel support, required-channel selection, and delivery-preference rules before persistence
   - creates one immutable configuration version only when validation succeeds
   - moves the active marker to the new version atomically
   - records one update-attempt outcome for success, validation rejection, or storage failure
4. Keep route handlers thin:
   - one authenticated `GET` endpoint for loading the active configuration
   - one authenticated `PUT` endpoint for validating and replacing the active configuration
   - all validation, versioning, activation, and observability decisions in services
   - all persistence in repositories
5. Keep frontend integration bounded:
   - load and render the single shared active configuration
   - preserve local draft state until save is submitted
   - show field-level validation errors without replacing the active saved configuration
   - confirm successful save and refresh local state from the returned active version
   - show explicit save-failure messaging when storage fails and reload the previous active configuration on refresh

## Acceptance Alignment

Map implementation and tests directly to [UC-13](/Users/sahmed/Documents/311-forecast-system/docs/UC-13.md) and [UC-13-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-13-AT.md):

- AT-01: load the single active configuration with thresholds, supported channels, and delivery preferences
- AT-02 through AT-04: support draft editing for thresholds, supported channels, and scoped frequency or deduplication preferences
- AT-05 and AT-06: validate and save a new configuration version, confirm success, and record a traceable success outcome
- AT-07: ensure later alert behavior reads the newly active configuration
- AT-08: reject invalid threshold values without changing the active configuration
- AT-09: reject unsupported channels without changing the active configuration
- AT-10: log storage failure, show failure messaging, and preserve the previous active configuration

## Suggested Test Layers

- Unit tests for scope normalization, threshold-rule validation, required-channel validation, supported-channel validation, delivery-preference validation, and save-outcome derivation
- Integration tests across active-configuration loading, immutable version creation, active-marker replacement, validation rejection, and storage-failure continuity
- Contract tests for [alert-configuration-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/013-uc-13-configure-alert-thresholds/contracts/alert-configuration-api.yaml)
- Frontend interaction tests for authenticated settings load, draft editing, validation errors, successful save confirmation, and failed-save recovery behavior

## Exit Conditions

Implementation is ready for task breakdown when:

- UC-13 loads exactly one shared active alert configuration for the system
- every saved configuration version contains at least one supported notification channel
- threshold rules and delivery preferences preserve category-only versus category-plus-geography scope distinctly
- successful saves create a new immutable configuration version and atomically activate it
- validation rejection and storage failure both preserve the previous active configuration
- later alert evaluation reads only the version referenced by the active configuration marker
- save outcomes remain explicitly traceable through structured update-attempt records
