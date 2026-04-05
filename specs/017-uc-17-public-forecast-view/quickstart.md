# Quickstart: View Public Forecast of 311 Demand by Category

## Purpose

Use this guide to implement and verify UC-17 as an anonymous public portal that reads the current approved public-safe 311 forecast, shows understandable category-level demand outlooks, clearly marks incomplete coverage, sanitizes restricted details before display, and records successful or failed public display outcomes.

## Implementation Outline

1. Reuse shared platform capabilities without redefining them:
   - retained forecast lineage and current approved-version semantics from UC-03 and UC-04
   - public-facing visualization conventions established by UC-05
   - structured request-correlation and display-event patterns established through UC-12 through UC-16
   - shared logging and typed API conventions
2. Add only UC-17-specific models needed for portal delivery and observability:
   - `PublicForecastPortalRequest`
   - `PublicForecastSanitizationOutcome`
   - `PublicForecastVisualizationPayload`
   - `PublicForecastDisplayEvent`
   - `PublicForecastView`
3. Build one backend public-load path that:
   - accepts an anonymous page-load request
   - resolves the current approved public-safe forecast version
   - captures one request-scoped portal record
   - applies public-safety filtering before any payload is returned
   - prepares category summaries with forecast window label and publication timestamp
   - marks incomplete category coverage explicitly when not all intended categories are present
   - returns either an `available` public view or an explicit `unavailable` or `error` state
4. Keep route handlers thin:
   - one anonymous `GET` endpoint for loading the current public forecast view
   - one anonymous request-scoped `POST` endpoint for reporting final display success or render failure
   - all source resolution, sanitization, status assignment, and event persistence in services and repositories
5. Keep frontend integration bounded:
   - load the public view using the normalized backend contract only
   - render charts, indicators, or summaries from sanitized category summaries
   - show an incomplete-coverage message when indicated by the payload
   - show a clear unavailable or error state instead of blank, stale, partial, corrupted, or unsanitized content
   - report final display success or render failure using the returned public forecast request id

## Acceptance Alignment

Map implementation and tests directly to [UC-17](/Users/sahmed/Documents/311-forecast-system/docs/UC-17.md) and [UC-17-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-17-AT.md):

- AT-01: anonymous public portal loads with a forecast content region or loading state and no initial error
- AT-02: backend retrieves approved public-safe forecast demand by category and records retrieval success
- AT-03: backend prepares a public-facing representation with no internal operational metadata
- AT-04: charts or summaries render understandable category-level demand outlooks for residents
- AT-05: successful public display is logged with request timing and outcome context
- AT-06: missing approved forecast data produces a clear error state and logged missing-data outcome
- AT-07: restricted details trigger sanitization and only safe summary content is displayed
- AT-08: visualization rendering failure produces a clear error state, withholds partial visuals, and records render failure

## Suggested Test Layers

- Unit tests for approved public-version resolution, category-summary normalization, sanitization rules, incomplete-coverage detection, and status-message assignment
- Integration tests across anonymous forecast retrieval, missing-data behavior, sanitization behavior, and display-event reporting
- Contract tests for [public-forecast-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/017-uc-17-public-forecast-view/contracts/public-forecast-api.yaml)
- Frontend interaction tests for portal load, understandable summary display, incomplete-coverage messaging, missing-data state, sanitized display, and render-failure handling

## Verification Steps

1. Open the public route and confirm the page shows a loading state before data arrives.
2. Verify an `available` response renders service-category cards, forecast-window text, and a publication timestamp.
3. Verify a sanitized response shows the sanitization summary and an explicit incomplete-coverage notice instead of inventing missing categories.
4. Verify an `unavailable` response shows a clear public message and no category summaries.
5. Force a render failure and confirm the error state replaces the public view while a `render_failed` event is submitted for the same `publicForecastRequestId`.

## Exit Conditions

Implementation is ready for task breakdown when:

- the portal is reachable without authentication
- the backend returns only the current approved public-safe forecast version
- successful responses contain only public-safe category-level content plus forecast-window and publication metadata
- incomplete category coverage is explicit and never implied as zero demand
- successful display, missing-data, sanitization, and render-failure outcomes are queryable
- unsanitized, blank, stale, partial, or corrupted public content is never shown as a successful forecast view
