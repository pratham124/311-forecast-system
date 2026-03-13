# Checklists Report

Below is a report of the checklist items that we found were not completed after running /speckit.checklists. We created 4 checklists for each use case: API, UX, data model, and security. Then we identified checklist items that were not complete and analyzed them. The analysis is available below for each use case:

Below is a template of how we should write the checklists report based on how it was done in lab2.
Ask Codex to mark the checklists items it thinks are complete after it generates the checklists, then include here any checklist items you think are necessary that you address.

## Use Case 2 (TEMPLATE)
Again, almost all checklist items were complete and validated in UC-02. The following item was not satisfied:

- [ ] CHK004 Is the definition of “unique email” unambiguous (case sensitivity, normalization)? [Clarity, Spec §Acceptance Scenarios, Gap]

This are necessary for the CMS, so I prompted to add this to the specification and plan. In particular, emails should be case insensitive.

## Use Case 1
Almost all checklist items were complete and validated in UC-01. The following items were not satisfied:

Ingestion.md:
- [ ] CHK003 Are the conditions for creating a new dataset version versus leaving the current dataset unchanged explicitly defined for all run outcomes? [Completeness, Spec §FR-005, Spec §FR-008]
- [ ] CHK006 Is "latest 311 service request records since the last successful pull" defined unambiguously enough to avoid conflicting interpretations of the pull window? [Clarity, Ambiguity, Spec §FR-003]
- [ ] CHK008 Is "queryable" defined with sufficient precision to indicate which current-dataset facts must be retrievable for verification? [Clarity, Ambiguity, Spec §FR-012]
- [ ] CHK009 Is "enough run detail" quantified or exemplified clearly enough to make logging requirements objectively reviewable? [Clarity, Ambiguity, Spec §FR-010]
- [ ] CHK010 Is "partial or candidate dataset" defined consistently enough to distinguish rejected data, unstored data, and stored-but-inactive data? [Clarity, Ambiguity, Spec §FR-007, Spec §SC-003]
- [ ] CHK013 Do the monitoring expectations remain consistent between the spec, success criteria, and plan artifacts, especially for failed runs? [Consistency, Spec §FR-011, Spec §SC-004, Gap]
- [ ] CHK024 Are boundary conditions addressed for the first-ever successful pull when no previous successful pull window exists? [Edge Case, Gap, Spec §FR-003]
- [ ] CHK033 Is there any unresolved ambiguity between "failure notification is recorded" in the use case contract and the spec’s looser wording around monitoring visibility? [Ambiguity, Conflict, Spec §FR-011]

security-data.md:
- [ ] CHK001 Are authentication requirements specified for every protected trigger and query surface, including run status, current dataset state, and failure notification access? [Completeness, Spec §FR-013]
- [ ] CHK003 Are authorization requirements defined for each actor type that needs access, rather than only stating "basic role-based authorization" at a high level? [Completeness, Ambiguity, Spec §FR-013]
- [ ] CHK006 Is "authenticated access" specific enough to determine what authentication strength or trust boundary is required for backend endpoints? [Clarity, Ambiguity, Spec §FR-013]
- [ ] CHK007 Is "basic role-based authorization appropriate for operational users and automated backend processes" defined with enough precision to avoid conflicting role interpretations? [Clarity, Ambiguity, Spec §FR-013]
- [ ] CHK008 Is "human-readable failure summary" constrained enough to avoid accidental inclusion of secrets, credentials, or excessive source payload detail in monitoring records? [Clarity, Ambiguity, Spec §FR-011]
- [ ] CHK009 Is "validate every retrieved dataset for required structure, required fields, valid data types, and completeness" specific enough to define the minimum acceptance threshold for data quality? [Clarity, Spec §FR-004]
- [ ] CHK019 Are security requirements defined for both scheduled execution and test-trigger execution of the same ingestion workflow, including any differences in allowed actors? [Coverage, Gap, Spec §FR-001, Spec §FR-013, Research §Decision: Model the scheduler as a production scheduled trigger with a test harness entry point that executes the same ingestion workflow]
- [ ] CHK020 Are requirements specified for how sensitive data should be handled across all failure classes, including authentication failure, source unavailability, validation failure, and storage failure? [Coverage, Gap, Spec §Edge Cases, Spec §FR-010, Spec §FR-011]
- [ ] CHK022 Does the spec define whether failure summaries or logs may include malformed source records, and if so, what redaction or minimization rules apply? [Edge Case, Gap, Spec §FR-010, Spec §FR-011]
- [ ] CHK025 Are confidentiality requirements defined for source credentials and any operational metadata that could reveal protected backend access patterns? [Non-Functional, Security, Gap, Spec §FR-002, Spec §FR-013]
- [ ] CHK030 Is there any unresolved ambiguity about whether "queryable" data surfaces are intended for operational humans only, automated processes only, or both? [Ambiguity, Spec §FR-012, Spec §FR-013]
- [ ] CHK031 Do any requirements conflict between minimizing persisted invalid data and preserving enough failed-run evidence for monitoring and diagnosis? [Conflict, Spec §FR-007, Spec §FR-010, Spec §FR-011, Spec §Edge Cases]

These are necessary, so I prompted to add this to the specification and plan.

## Use Case 2
Almost all checklist items were complete and validated in UC-02; I prompted Codex to generate the API, data, security, performance checklists as one file. The following items were not satisfied:

- [ ] CHK006 Is "non-conflicting values" defined clearly enough to determine when duplicate consolidation is allowed versus blocked? [Ambiguity, Spec §FR-005a]
- [ ] CHK007 Is the distinction between "rejected," "failed," and "review-needed" outcomes defined with clear decision boundaries? [Clarity, Spec §FR-003, Spec §FR-009, Spec §FR-014]
- [ ] CHK009 Do the duplicate-threshold requirements align consistently between the general threshold statement and the percentage-based clarification? [Consistency, Spec §FR-010, Spec §FR-011]
- [ ] CHK010 Are status terms used consistently across the spec, plan, data model, and contract (`approved`, `rejected`, `failed`, `review_needed`)? [Consistency, Spec §FR-009, plan.md, data-model.md, contracts/validation-api.yaml]
- [ ] CHK011 Are approval-marker requirements consistent between the spec and the reused UC-01 data lineage described in the plan and data model? [Consistency, Spec §FR-006, Spec §FR-008, data-model.md]
- [ ] CHK021 Are API contract quality requirements defined for missing-resource, unauthorized, and invalid-query scenarios on operational status surfaces? [API, Gap]
- [ ] CHK024 Are externally configured validation rules, duplicate-identification rules, and threshold assumptions defined with enough precision to know what must exist before UC-02 can work? [Assumption, Spec §Assumptions]

These are necessary, so I prompted to add this to the specification and plan.

## Use Case 3
Almost all checklist items were complete and validated in UC-03; I prompted Codex to generate the API, data, security, performance checklists as one file. The following items were not satisfied:

- [ ] CHK003 Are response expectations defined for all relevant API failure classes, including unauthorized, forbidden, not found, invalid request, missing input data, engine failure, and storage failure? [Gap, Spec §FR-011-FR-015; Contract §Paths]
- [ ] CHK004 Is the reuse-versus-regenerate decision specified clearly enough that an API consumer can tell when a request should return the current forecast instead of producing a new one? [Clarity, Spec §FR-002-FR-004; Spec §User Story 2; Contract §ForecastRunStatus]
- [ ] CHK005 Are the forecast data entities and lineage relationships defined clearly enough to distinguish the active approved dataset marker from the active forecast marker? [Consistency, Spec §Key Entities; Data Model §Reused Entities; Data Model §CurrentForecastMarker]
- [ ] CHK007 Are the hourly bucket requirements specific enough to remove ambiguity about interval boundaries, 24-bucket coverage, service-category segmentation, and optional geography omission? [Clarity, Spec §Clarifications; Spec §FR-004-FR-007; Data Model §ForecastBucket]
- [ ] CHK010 Are data protection requirements specified clearly enough to prohibit raw source payloads, feature matrices, and secrets from appearing in API responses, logs, or operational summaries? [Completeness, Plan §Constraints; Plan §Implementation Step 9; Contract §summary]
- [ ] CHK011 Is the boundary between authentication/authorization requirements and general operational failure handling explicit enough to avoid ambiguity in the term "failed" across security and non-security cases? [Ambiguity, Spec §FR-011-FR-015; Data Model §ForecastRun; Contract §ForecastRunStatus]
- [ ] CHK012 Are unauthorized, forbidden, and missing-resource expectations consistent between the written requirements and the forecast API contract? [Consistency, Contract §Paths; Spec §FR-015; Gap]
- [ ] CHK016 Are concurrency, scheduling overlap, or load assumptions for scheduled and on-demand forecast requests documented or intentionally excluded? [Gap, Spec §FR-001-FR-004; Plan §Scale/Scope]

These are necessary, so I prompted to add this to the specification and plan.

## Use Case 4
For this use case, all checklist items were complete and validated. This makes sense considering we have explicitly defined this use case and already performed clarifications to meet any gaps in our spec. No changes needed to be addressed.

## Use Case 5
For this use case, all checklist items were complete and validated. This makes sense considering we have explicitly defined UC-05 and already performed clarifications to address the key gaps in our spec (uncertainty band standard, historical context window, and fallback staleness limit). No changes needed to be addressed.

## Use Case 6
Almost all checklist items were complete and validated in UC-06; the following item was not satisfied:

- [ ] CHK010 Are baseline-method requirements complete enough to define which baseline methods must be represented in published results and how additional baseline methods would be named or differentiated? [Gap, Spec §FR-006, FR-019; Spec §Assumptions; Data Model §MetricComparisonValue]

It is necessary to have good baseline-method requirements explicitly defined, so I prompted Codex to consider moving averages and updated the spec/plan to fufill this.

## Use Case 7
For this use case, all checklist items were complete and validated. This makes sense considering we have explicitly defined UC-07 and already performed clarifications to address the key gaps in our spec (i.e. geographic filtering scope). No changes needed to be addressed.

## Use Case 8

I prompted Codex to combine into one checklist. Majority of checklist items were complete and validated in UC-08; the following item was not satisfied:

- [] CHK001 Are the required filter controls fully specified for service categories, geographic areas, and time range, including whether category and geography selection are single-select or multi-select and whether geography is optional for a valid request? [Completeness, Spec §FR-001; Contract §DemandComparisonQueryRequest; Data Model §DemandComparisonRequest]
- [] CHK003 Are planner-visible requirements defined for the high-volume warning state before retrieval begins, including what information the warning must communicate about expected delay or processing impact? [Completeness, Spec §User Story 2; Spec §FR-007; Contract §HighVolumeWarning]
- [] CHK008 Are UX requirements defined for replacing a previously displayed comparison after the planner changes filters, so stale results are not ambiguously shown alongside or instead of the new scope? [Coverage, Spec §Edge Cases; Spec §FR-006; Plan §Implementation Step 7]
- [] CHK013 Are authentication requirements specified in the feature requirements for every comparison-related surface, including context retrieval, comparison execution, and render-outcome reporting, instead of appearing only in the plan and contract? [Completeness, Plan §Implementation Step 2; Contract §paths; Gap]
- [] CHK017 Are security requirements defined clearly enough for the render-outcome reporting surface to prevent unauthenticated or unrelated clients from submitting render events for comparison requests they do not own? [Clarity, Plan §Implementation Step 2; Contract §/api/v1/demand-comparisons/{comparisonRequestId}/render-events]
- [] CHK026 Are category and geographic classification requirements specific enough to define what makes a classification “defined” and eligible for comparison use, rather than leaving alignment eligibility implicit? [Clarity, Spec §FR-015; Spec §Assumptions; Data Model §Derived Invariants]
- [] CHK029 Are comparison granularity requirements defined clearly enough to determine when hourly, daily, or weekly normalization is allowed for a request and which forecast source may be used for each case? [Clarity, Data Model §DemandComparisonResult; Contract §DemandComparisonResponse; Plan §Implementation Step 1]
- [] CHK030 Do the outcome vocabularies remain fully consistent across the spec, data model, plan, and contract, especially for retrieval failure, alignment failure, and render failure states and where each of those states is exposed? [Consistency, Spec §FR-011b-FR-014; Data Model §DemandComparisonRequest; Data Model §DemandComparisonOutcomeRecord; Contract §DemandComparisonResponse]
- [] CHK031 Are forecast product names and forecast granularity definitions verified to align with the upstream UC-03 and UC-04 forecast specifications, so UC-08 does not introduce conflicting source terminology? [Consistency, Plan §Summary; Data Model §Reused Entities; Contract §DemandComparisonResponse]
- [] CHK032 Are requirements defined for the edge case where historical data exists for only part of the selected time range, so the system behavior is explicit instead of inferred from the broader missing-data rules? [Coverage, Spec §Edge Cases; Spec §FR-010-FR-012]
- [] CHK033 Are requirements defined for requests with no geography filter, or else is geography required consistently across the spec, contract, and data model so null or empty geography semantics are not left ambiguous? [Gap, Spec §FR-001; Contract §DemandComparisonQueryRequest; Data Model §DemandComparisonRequest]
- [] CHK034 Are validation and selection rules documented for mutually exclusive forecast source references and their relationship to the selected comparison range and requested granularity, rather than only stating that both sources cannot be populated together? [Coverage, Data Model §DemandComparisonRequest; Plan §Implementation Step 1]
- [] CHK035 Is the dependency on approved historical lineage and active forecast lineage expressed as an enforceable requirement in the specification, rather than only as an assumption or implementation-plan constraint? [Assumption, Spec §Assumptions; Plan §Summary; Plan §Implementation Step 1]
- [] CHK040 Are API failure outcomes specific enough to distinguish historical retrieval failure from forecast retrieval failure at the contract level, rather than collapsing both into a single retrieval_failed outcome while the specification treats them separately? [Clarity, Spec §User Story 3 Scenarios 3-4; Spec §FR-011b; Spec §FR-011c; Contract §DemandComparisonResponse]
- [] CHK041 Is the API contract explicit enough about when forecastProduct, forecastGranularity, sourceForecastVersionId, and sourceWeeklyForecastVersionId are required, optional, or mutually dependent, instead of leaving those rules only in the data model? [Clarity, Contract §DemandComparisonResponse; Data Model §DemandComparisonRequest; Data Model §DemandComparisonResult]
- [] CHK044 Are API-facing response expectations measurable and complete enough that acceptance behavior can be verified without inferring missing rules about terminal states, partial-result semantics, or warning-required semantics? [Measurability, Contract §schemas; Plan §Verify acceptance behavior; Spec §FR-007-FR-014]
- [] CHK051 Is the non-high-volume performance target defined with clear start and stop timing boundaries, so “within 10 seconds” can be measured objectively for results, partial-result states, and explicit error outcomes? [Clarity, Spec §SC-002; Plan §Performance Goals]
- [] CHK052 Is the “system-defined large-request threshold” specified clearly enough to support objective validation of when a high-volume warning must be shown before retrieval begins? [Ambiguity, Spec §FR-007; Spec §Assumptions; Spec §SC-003]

These are necessary, so I prompted to add this to the specification and plan.

## Use Case 9

I prompted Codex to combine all the checklists into one. Majority of checklist items were complete and validated in UC-09; the following item was not satisfied:

- [] CHK005 Does the contract documentation specify all non-visible terminal states needed by the requirements, including whether `disabled` and `render_failed` are intentionally represented outside the `GET` response? [Gap, Spec §FR-008-FR-013, Data Model §OverlayDisplayState, Contract GET /api/v1/forecast-explorer/weather-overlay]
- [] CHK007 Is "supported geography" defined precisely enough to distinguish accepted matches from rejected geography requests under the approved alignment rules? [Clarity, Spec §User Story 1, Spec §FR-003, Spec §Assumptions]
- [] CHK008 Is "supported selection" in the 5-second performance target bounded clearly enough to exclude invalid, unavailable, or superseded requests? [Clarity, Spec §SC-001, Plan §Performance Goals]
- [] CHK011 Are the overlay state definitions consistent between the spec, data model, and API contract, with no missing or conflicting statuses across documents? [Consistency, Spec §FR-007-FR-013, Data Model §OverlayDisplayState, Contract §WeatherOverlayResponse]
- [] CHK023 Are requirements defined for empty but successful weather-provider responses versus explicit retrieval failures, so reviewers can distinguish missing-data behavior from service-error behavior? [Coverage, Spec §User Story 2, Data Model §WeatherObservationSet]
- [] CHK027 Are API requirements complete for validation errors, status-code intent, and stable response shapes across success and explicit non-visible states? [Non-Functional, Contract responses, Contract §WeatherOverlayResponse]
- [] CHK028 Are the assumptions about approved geography-alignment rules and Edmonton-area station selection documented precisely enough to avoid hidden planning decisions? [Assumption, Spec §Assumptions, Plan §Implementation Steps 2-3]
- [] CHK031 Does the current documentation resolve the duplicate `Overlay Display State` definition in the spec, or is a canonical single definition still needed? [Conflict, Spec §Key Entities]
- [] CHK032 Is it unambiguous whether the contract should expose a `disabled` state, given that the data model includes it but the `GET` contract omits it? [Ambiguity, Data Model §OverlayDisplayState, Contract §WeatherOverlayResponse]

These are necessary, so I prompted to add this to the specification and plan.

## Use Case 10

I prompted Codex to combine all the checklists into one. Majority of checklist items were complete and validated in UC-10; the following item was not satisfied: