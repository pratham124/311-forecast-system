# Quickstart: Access User Guide

## Purpose

Use this guide to implement and verify UC-18 as an authenticated in-product help flow that allows any signed-in user to open the current published guide, read it in a readable instructional format, navigate available sections or pages, and receive explicit unavailable or render-error states with full observability.

## Implementation Outline

1. Reuse shared platform capabilities without redefining them:
   - authenticated user context and backend authorization
   - existing product help or user-guide entry points
   - documentation storage or service that holds the current published guide
   - shared structured logging and typed API conventions
2. Add only UC-18-specific models needed for guide delivery and observability:
   - `GuideAccessEvent`
   - `GuideSection`
   - `UserGuideView`
   - `GuideRenderOutcome`
3. Build one backend guide-load path that:
   - accepts the product entry point from which the guide was opened
   - verifies the caller is signed in
   - resolves the current published guide
   - normalizes guide content into readable body content plus ordered section or page metadata
   - records one guide-access event for the attempt
   - returns either an `available` guide payload or an explicit `unavailable` or `error` state
4. Keep route handlers thin:
   - one authenticated `GET` endpoint for loading the current guide
   - one authenticated `POST` endpoint for reporting final render success or render failure
   - all guide retrieval, status assignment, and event persistence in services and repositories
5. Keep frontend integration bounded:
   - expose a help or user-guide option on intended product surfaces
   - open the guide using the normalized backend contract only
   - render ordered sections or pages in a readable instructional layout
   - keep navigation within the loaded guide session rather than forcing reopen
   - show a clear unavailable or error state instead of blank, stale, partial, or corrupted content
   - report final render success or render failure using the returned guide access event id

## Acceptance Alignment

Map implementation and tests directly to [UC-18](/root/311-forecast-system/docs/UC-18.md) and [UC-18-AT.md](/root/311-forecast-system/docs/UC-18-AT.md):

- AT-01: user selects the help or user guide option from a supported product surface
- AT-02: backend retrieves the current published guide and records retrieval success
- AT-03: the guide is displayed in a readable instructional format without an error state
- AT-04: section or page navigation works without forcing the user to reopen the guide
- AT-05: successful guide access is logged with time of access and outcome
- AT-06: documentation-unavailable conditions produce a clear error state and logged retrieval failure
- AT-07: display rendering failures produce a clear error state, withhold corrupted or partial content, and log render failure

## Suggested Test Layers

- Unit tests for current-guide resolution, section ordering, outcome assignment, failure-message normalization, and access-event persistence
- Integration tests across authenticated guide retrieval, unavailable-guide behavior, render-outcome reporting, and event logging
- Contract tests for [user-guide-api.yaml](/root/311-forecast-system/specs/013-access-user-guide/contracts/user-guide-api.yaml)
- Frontend interaction tests for guide open, section navigation, unavailable state, and render-failure handling

## Exit Conditions

Implementation is ready for task breakdown when:

- any signed-in user can open the guide from supported product surfaces
- the backend returns only the current published guide
- guide sections or pages are navigable without reopening the guide
- successful access, retrieval failures, and render failures are all queryable outcomes
- retrieval failures never show blank, stale, or partial guide content
- render failures never leave corrupted or partially rendered content visible
