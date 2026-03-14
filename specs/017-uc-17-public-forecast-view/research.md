# Research: View Public Forecast of 311 Demand by Category

## Decision: Read only the current approved public-safe forecast version

**Rationale**: UC-17 is a public consumption surface, not a forecast-production or approval workflow. Reusing the current approved public-safe version keeps the portal downstream of the shared forecast lineage and avoids conflicting public views.

**Alternatives considered**:
- Select the newest retained forecast regardless of approval state: rejected because the spec requires approved public-safe content only.
- Generate or rescore a forecast during the public request: rejected because UC-17 must not create forecasts on demand.

## Decision: Persist one request-scoped portal record for every public page-load attempt

**Rationale**: UC-17 must trace retrieval success, sanitization actions, missing-data conditions, and final display outcomes for the same portal interaction. A request-scoped record provides one stable correlation anchor without mutating shared forecast lineage.

**Alternatives considered**:
- Use only free-form logs: rejected because acceptance testing and operational review require queryable request-level outcomes.
- Persist only final success or failure events: rejected because sanitization and preparation outcomes would be disconnected from the originating request.

## Decision: Enforce public-safety filtering in the backend before response delivery

**Rationale**: The anonymous frontend cannot be trusted as the enforcement point for disclosure rules. Backend sanitization guarantees that restricted forecast metadata is removed or summarized before any payload can reach the browser.

**Alternatives considered**:
- Return full forecast payloads and hide restricted fields in the frontend: rejected because it exposes data the portal must never disclose.
- Fail the entire request whenever a restricted field exists: rejected because the spec allows sanitized summaries when safe public output can still be produced.

## Decision: Represent incomplete category coverage explicitly in the public payload

**Rationale**: The spec forbids implying omitted categories have zero demand. A dedicated coverage status and message let the portal show only included categories while warning that coverage is incomplete.

**Alternatives considered**:
- Fill omitted categories with zero values: rejected because it produces misleading public information.
- Omit the message and let users infer missing categories: rejected because the public view must remain understandable and not silently incomplete.

## Decision: Report final display outcomes separately from backend payload preparation

**Rationale**: The backend may retrieve and sanitize the forecast successfully while the client still fails to render the chart or summary. Separate display-event reporting preserves the distinction between successful preparation and unsuccessful public display.

**Alternatives considered**:
- Treat a successful `GET` response as equivalent to successful display: rejected because it hides frontend rendering failures.
- Mutate the prepared payload record after a render failure: rejected because the prepared result should remain an immutable record of backend output.

## Decision: Use one normalized response model for available and unavailable portal states

**Rationale**: The portal needs a stable contract whether the forecast is available, missing, or preparation failed. One normalized response model lets the frontend handle success and explicit error states without inventing hidden fallback behavior.

**Alternatives considered**:
- Return only raw category arrays on success and rely on HTTP errors for all failures: rejected because the UI also needs typed user-facing status messaging and request identifiers for observability.
- Create separate endpoints for success and failure introspection: rejected because the public page load should remain a single retrieval flow.
