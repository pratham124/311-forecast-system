# Research: Add Weather Overlay

## Decision: Extend the existing forecast explorer rather than define a separate weather-analysis view

**Rationale**: UC-09 explicitly treats weather as an optional overlay on the forecast explorer. Reusing the existing explorer context keeps the feature aligned with the current operational workflow and avoids duplicating forecast and historical demand presentation logic.

**Alternatives considered**:
- Create a standalone weather-analysis screen: rejected because it expands scope beyond UC-09 and weakens direct comparison with forecast demand.
- Build a generic charting endpoint unrelated to the explorer context: rejected because it would require the client to reconstruct behavior that belongs in the governed forecast explorer.

## Decision: Source overlay weather observations only from Government of Canada MSC GeoMet through dedicated normalization modules

**Rationale**: The constitution requires MSC GeoMet as the weather source and requires external integrations to remain isolated in dedicated client or ingestion modules. Normalizing GeoMet responses before use preserves layered architecture and prevents the frontend or service layer from depending on third-party response details.

**Alternatives considered**:
- Call GeoMet directly from route handlers: rejected because it violates layering and makes transport code responsible for business behavior.
- Use a different weather provider: rejected because it conflicts with the constitution.

## Decision: Support one selected weather measure at a time in the overlay

**Rationale**: The clarification session resolved the overlay as a single-measure view. Showing one supported measure at a time keeps the overlay readable, simplifies interaction and testing, and avoids conflicting scale interpretations on the forecast explorer.

**Alternatives considered**:
- Show all supported measures together: rejected because it increases visual clutter and complicates alignment semantics.
- Lock the overlay to one fixed default measure: rejected because the accepted clarification preserves user choice among supported measures.

## Decision: Suppress the overlay when the selected geography cannot be matched under approved alignment rules

**Rationale**: The clarified feature requires geographic safety over approximation. A supported geography exists only when approved alignment rules define a direct mapping from the forecast-explorer geography to the approved Edmonton-area weather-station selection and the active demand-view time buckets. Suppressing the overlay avoids presenting misleading weather context when the system cannot confidently match the current explorer selection.

**Alternatives considered**:
- Fall back to the nearest available station geography: rejected because it introduces implicit substitution that the clarification explicitly disallowed.
- Broaden automatically to a larger covering geography: rejected because it weakens interpretability and can imply false local correlation.

## Decision: Cancel or discard in-flight overlay work for superseded selections

**Rationale**: The clarification session fixed stale-result behavior: only the operational manager’s latest geography, time range, and weather-measure selection may produce a visible overlay. Canceling or discarding superseded work prevents stale overlays from appearing after the underlying explorer context has changed.

**Alternatives considered**:
- Let earlier requests complete and render anyway: rejected because it can show stale or incorrect overlay data.
- Lock the explorer until the request finishes: rejected because it degrades usability and is unnecessary for correctness.

## Decision: Use one canonical overlay-state vocabulary across the spec, data model, and API contract

**Rationale**: Signoff requires stable language for non-visible and terminal states. The canonical vocabulary is `disabled`, `loading`, `visible`, `unavailable`, `retrieval-failed`, `misaligned`, `superseded`, and `failed-to-render`, which covers the user-visible off state, in-progress work, successful display, empty successful retrieval, provider retrieval failure, alignment failure, supersession, and final render failure.

**Alternatives considered**:
- Keep different vocabularies for data model and API (`unalignable` versus `misaligned`, `render_failed` versus `failed-to-render`): rejected because it creates contract drift and ambiguous test expectations.
- Hide non-visible states behind generic errors: rejected because UC-09-AT requires explicit graceful degradation cases.

## Decision: Distinguish empty successful retrieval from provider retrieval failure

**Rationale**: UC-09-AT distinguishes no matching records from explicit service failure. Treating them as separate states keeps acceptance criteria testable and gives operations enough context to know whether the provider worked but lacked records or failed before a result could be returned.

**Alternatives considered**:
- Collapse both into one unavailable state: rejected because it hides a real operational difference.
- Treat empty retrieval as a client-side rendering concern: rejected because the distinction occurs before rendering and belongs in backend overlay assembly.

## Decision: Expose `disabled` through GET only, and expose `failed-to-render` through both GET and POST render-events

**Rationale**: `disabled` is the stable user-visible off state of the overlay control and belongs in the current overlay read model, not in a render event. `failed-to-render` originates from a client render attempt and therefore must be posted as an event, but it also needs to surface in later GET responses so the non-visible overlay outcome is stable and observable after the original attempt.

**Alternatives considered**:
- Represent both states only in POST events: rejected because GET would no longer describe the current overlay state of the explorer.
- Represent render failure only in GET: rejected because it would lose the explicit client-reported render event required for observability.
