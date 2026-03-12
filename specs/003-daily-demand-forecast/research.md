# Research: Generate 1-Day Demand Forecast

## Decision: Consume the UC-02 approved cleaned dataset as the only forecast input lineage

**Rationale**: UC-01 defines ingestion lineage and UC-02 defines the approved cleaned dataset that downstream consumers should trust. Using the approved cleaned dataset as the forecast source keeps UC-03 aligned with the existing last-known-good dataset lifecycle and avoids generating operational forecasts from raw or unapproved inputs.

**Alternatives considered**:
- Forecast directly from the UC-01 ingested dataset: rejected because it bypasses the validation and deduplication guarantees added in UC-02.
- Rebuild an isolated forecast input store unrelated to UC-01 and UC-02: rejected because it would duplicate lineage and make active-data provenance harder to verify.

## Decision: Keep UC-03 as a feature-specific 1-day hourly operational forecast without redefining the constitution's broader default forecast product

**Rationale**: `docs/UC-03.md` and `docs/UC-03-AT.md` define a next-24-hour operational forecast in hourly buckets. The constitution separately defines the project's broader default forecasting direction as daily next-7-day service-category forecasting. Making that distinction explicit preserves UC-03 scope and behavior while preventing this feature plan from being misread as a replacement for the broader default product direction.

**Alternatives considered**:
- Recast UC-03 as the constitution's broader 7-day daily product: rejected because it changes use-case scope and breaks UC-03 acceptance intent.
- Ignore the distinction entirely: rejected because it leaves the plan constitution-ambiguous.

## Decision: Store the 1-day forecast as 24 consecutive hourly buckets with category-mandatory and geography-optional slices

**Rationale**: The clarified feature requirement fixed the planning output to hourly buckets across the next 24 hours. Modeling the forecast as 24 hourly slices preserves operational staffing value while staying aligned with the acceptance tests and allowing geography omission without degrading the required category-level forecast.

**Alternatives considered**:
- One aggregate daily forecast value: rejected because it removes the intra-day detail needed for dispatch and staffing.
- Shift-level or multi-hour buckets: rejected because the accepted clarification chose hourly granularity.

## Decision: Give UC-03 its own forecast lifecycle entities instead of reusing the UC-02 approval marker

**Rationale**: The active approved cleaned dataset and the active forecast are separate operational concepts with different replacement rules. A dedicated forecast run, version, bucket, and current-marker lifecycle preserves last-known-good behavior for forecasts without weakening the dataset approval model established in UC-02.

**Alternatives considered**:
- Overload the UC-02 approval marker to point to the active forecast: rejected because it would mix source-data approval with forecast activation.
- Keep only an ephemeral in-memory current forecast: rejected because acceptance tests require persistent current-forecast visibility.

## Decision: Use one orchestration path for scheduled and on-demand forecast generation

**Rationale**: UC-03 must support both scheduled generation and direct operational requests. Running both through the same service and pipeline path minimizes drift in reuse behavior, failure handling, activation safety, and observability.

**Alternatives considered**:
- Separate code paths for scheduled and manual generation: rejected because it increases regression risk and weakens acceptance parity.
- Scheduled generation only: rejected because the use case explicitly requires on-demand requests.

## Decision: Source weather enrichment only from Government of Canada MSC GeoMet through dedicated modules

**Rationale**: The constitution requires MSC GeoMet as the weather source and requires external integrations to remain isolated in dedicated client or ingestion modules. Keeping weather acquisition in dedicated modules preserves architecture boundaries, makes station selection explicit, and avoids embedding third-party details in routes, repositories, or model code.

**Alternatives considered**:
- Pull weather data directly inside routes or service methods: rejected because it violates the layered architecture.
- Use a different weather provider: rejected because it conflicts with the constitution.

## Decision: Source holiday enrichment only from the Nager.Date Canada API through dedicated modules

**Rationale**: The constitution names the Nager.Date Canada API as the holiday source. Dedicated client or ingestion modules keep the external contract isolated and allow the forecasting pipeline to depend only on normalized internal holiday features.

**Alternatives considered**:
- Hardcode holiday calendars in the forecast pipeline: rejected because it bypasses the designated external source and weakens maintainability.
- Use a different holiday API: rejected because it conflicts with the constitution.

## Decision: Reuse the current forecast only when it already covers the requested upcoming 24-hour window

**Rationale**: The spec requires serving an existing current forecast rather than rerunning the model when the forecast is already current. Tying reuse to the target horizon keeps the behavior testable and avoids unnecessary generation while ensuring stale forecasts are not treated as current.

**Alternatives considered**:
- Always regenerate on every request: rejected because it conflicts with the explicit reuse scenario.
- Reuse any forecast generated earlier on the same calendar day: rejected because it can produce stale results if the covered window differs from the requested next 24 hours.

## Decision: Persist predictive quantiles and a baseline comparator alongside the operational forecast

**Rationale**: The constitution requires predictive quantiles `P10`, `P50`, and `P90` and retention of a baseline forecast for comparison. Persisting those fields with the forecast output satisfies the constitutional forecasting safeguard while still allowing the operational workflow to focus on the hourly forecast itself.

**Alternatives considered**:
- Persist only one point forecast value: rejected because it loses constitution-mandated uncertainty coverage.
- Compute quantiles or baseline only transiently in memory: rejected because it weakens auditability and observability for forecast quality.

## Decision: Preserve constitution layering and backend-enforced access control on all UC-03 forecast surfaces

**Rationale**: The constitution requires thin FastAPI routes, service and pipeline business logic, repository-based persistence, dedicated integration modules, and backend-enforced JWT auth with RBAC. Making those boundaries explicit in UC-03 prevents business logic from drifting into route handlers and keeps denied access separate from forecast-run failures.

**Alternatives considered**:
- Collapse orchestration into routes for speed of implementation: rejected because it violates the constitution and weakens testability.
- Depend on frontend-only gating for trigger or read access: rejected because backend enforcement is required.

## Decision: Expose backend observability through run-status and current-forecast contracts only

**Rationale**: UC-03 acceptance coverage needs trigger control, forecast-run visibility, and current-forecast visibility, but not a dashboard or model-tuning UI. Backend contracts keep the feature bounded and consistent with the prior backend-only planning artifacts.

**Alternatives considered**:
- Add UI contracts now: rejected because presentation work is outside the current feature scope.
- Rely only on logs for verification: rejected because acceptance tests need a queryable current forecast and run status.

## Decision: Keep trigger, run-status, and current-forecast surfaces distinct and treat access or request errors separately from forecast-run outcomes

**Rationale**: The updated spec distinguishes the responsibilities of the generation trigger, run-status read, and current-forecast read surfaces, and it requires unauthorized, forbidden, missing-resource, and invalid-request outcomes to remain separate from business failures such as missing input data or engine failure. Preserving that boundary keeps contracts, logging, and run history unambiguous.

**Alternatives considered**:
- Collapse all forecast interactions into one surface: rejected because it blurs responsibility boundaries and weakens acceptance clarity.
- Record access denials as failed forecast runs: rejected because the spec explicitly separates access and request errors from generation outcomes.

## Decision: Retain stored forecast versions and failed forecast-run records as operational history

**Rationale**: The updated spec makes retention of stored forecast versions and failed forecast-run records explicit. Keeping that history supports operational diagnosis and acceptance visibility without changing the feature’s runtime behavior or adding manual workflows.

**Alternatives considered**:
- Retain only the current forecast: rejected because it conflicts with the updated spec.
- Treat retention as undefined implementation detail: rejected because the updated spec resolves it at the requirements level.

## Decision: Fail safe on missing data, engine failure, and storage failure by preserving the prior active forecast

**Rationale**: The use case, acceptance tests, and constitution all require last-known-good activation semantics. Forecast generation therefore cannot change the current marker until storage succeeds, and every terminal failure must leave the previous valid forecast active.

**Alternatives considered**:
- Replace the current forecast immediately after model execution: rejected because it allows partial activation if storage fails.
- Clear the current forecast on any failed run: rejected because it would reduce operational continuity instead of preserving it.
