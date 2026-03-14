# Research: Indicate Degraded Forecast Confidence in UI

## Decision: Reuse the existing forecast-visualization flow instead of introducing a second confidence page

**Rationale**: UC-16 is triggered when an operational manager opens a forecast view, and the degraded-confidence indicator is meaningful only in the context of that same forecast. Reusing the established forecast-visualization flow keeps the warning tied to the exact scope, window, and forecast values being viewed.

**Alternatives considered**:
- Create a separate confidence-inspection screen: rejected because it separates the warning from the forecast it qualifies.
- Return only logs or diagnostics for degraded confidence: rejected because the core user outcome is an in-context UI indication.

## Decision: Persist one request-scoped confidence-load record per view attempt

**Rationale**: UC-16 requires traceability across signal retrieval, validation, display preparation, render success, and render failure. A request-scoped record provides one stable anchor for those outcomes without mutating shared forecast or signal lineage.

**Alternatives considered**:
- Persist only free-form logs: rejected because it weakens reviewability and makes acceptance-test correlation harder.
- Avoid persistence and rely only on synchronous response behavior: rejected because render failures happen after response delivery and still need a durable correlation path.

## Decision: Apply one centrally managed degraded-confidence rule set across supported scopes

**Rationale**: The spec explicitly requires one configuration-managed set of degradation and materiality rules. Centralizing the rule set prevents UI inconsistency where identical conditions could show different warning behavior in different forecast views.

**Alternatives considered**:
- Allow per-scope overrides now: rejected because the spec explicitly keeps scope-specific rules out of scope.
- Let the frontend infer degraded confidence from raw flags: rejected because it would split rule ownership and bypass backend governance.

## Decision: Distinguish missing signals from dismissed non-material signals

**Rationale**: Both paths end with no warning shown, but they mean different things operationally. Missing signals mean confidence could not be assessed, while dismissed signals mean a candidate warning was reviewed and found not material.

**Alternatives considered**:
- Collapse both paths into one generic normal state: rejected because it loses critical observability and makes troubleshooting misleading.
- Treat missing signals as degraded by default: rejected because the spec forbids unsupported warnings.

## Decision: Report final render outcomes separately from prepared assessment results

**Rationale**: The backend can correctly detect degraded confidence and prepare an indicator while the client still fails to render it. A separate render-event report preserves the distinction between successful backend assessment and unsuccessful UI display.

**Alternatives considered**:
- Treat response generation as equivalent to successful display: rejected because it hides frontend and charting failures.
- Mutate the prepared assessment result after render failure: rejected because the prepared assessment should remain an immutable record of backend intent.

## Decision: Normalize user-facing reason categories to generic labels

**Rationale**: UC-16 needs to communicate elevated uncertainty clearly without exposing internal rule details or low-level model diagnostics. Generic categories such as missing inputs, shock, and anomaly satisfy the requirement for explanatory information while preserving a stable UI vocabulary.

**Alternatives considered**:
- Expose raw upstream signal names directly: rejected because those names may be unstable, overly technical, or implementation-specific.
- Show only a generic warning with no reason categories ever: rejected because the spec allows and encourages explanatory categories when appropriate information is available.
