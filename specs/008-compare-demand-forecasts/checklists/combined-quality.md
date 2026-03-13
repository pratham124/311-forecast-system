# Combined Quality Checklist: Compare Demand and Forecasts Across Categories and Geographies

**Purpose**: Consolidate UX, security, data, API, and performance requirement-quality checks for UC-08 into a single lightweight author review checklist.
**Created**: 2026-03-13
**Feature**: [spec.md](/root/311-forecast-system/specs/008-compare-demand-forecasts/spec.md)

## UX Requirements Quality

- [X] CHK001 Are the required filter controls fully specified for categories, geographies, and time range, including whether each supports single-select or multi-select behavior? [Completeness, Spec §FR-001]
- [X] CHK002 Are the comparison presentation modes defined clearly enough to distinguish when charts, tables, or both are expected? [Clarity, Spec §FR-005; Data Model §DemandComparisonResult]
- [X] CHK003 Are planner-visible requirements defined for the high-volume warning state before retrieval begins, including what information the warning must communicate? [Completeness, Spec §User Story 2; Spec §FR-007]
- [X] CHK004 Are planner-visible requirements defined for forecast-only, historical-only, and explicit error states rather than assuming the interface behavior is self-evident? [Completeness, Spec §User Story 3; Spec §FR-010; Spec §FR-011; Spec §FR-013]
- [X] CHK005 Is “allows planners to evaluate differences” translated into measurable presentation requirements rather than a subjective UX outcome? [Ambiguity, Spec §FR-005]
- [X] CHK006 Is the requirement to “explicitly identify” missing forecast combinations specific enough to determine how those missing combinations must be surfaced to the planner? [Clarity, Spec §FR-011a]
- [X] CHK007 Are “in-progress state,” “warning,” “partial-result message,” and “error state” defined with distinct meanings so the UI states cannot collapse into one ambiguous status treatment? [Consistency, Spec §FR-007; Spec §FR-009; Spec §FR-013]
- [X] CHK008 Are UX requirements defined for the transition from a previous comparison to a new filter selection so stale results are not ambiguously presented? [Coverage, Edge Case, Spec §Edge Cases]
- [X] CHK009 Are requirements defined for warning acknowledgment and post-warning continuation without leaving the planner’s selected filter context ambiguous? [Coverage, Spec §User Story 2; Plan §Implementation Step 4]
- [X] CHK010 Are UX requirements complete for the clarified mixed-availability extension, including how available comparisons and missing combinations coexist without misleading the planner? [Coverage, Spec §User Story 3 Scenario 6; Spec §FR-011a]
- [X] CHK011 Are accessibility requirements for filter interaction, warning acknowledgment, and comparison-state messaging explicitly documented anywhere in the feature requirements? [Gap]
- [X] CHK012 Are readability or visual distinction requirements defined for comparing historical versus forecast series across multiple categories and geographies? [Gap, Spec §FR-005]

## Security Requirements Quality

- [X] CHK013 Are authentication requirements specified for every comparison-related surface, including context retrieval, comparison execution, and render-outcome reporting? [Completeness, Plan §Implementation Step 2; Contract §paths]
- [X] CHK014 Are authorization requirements defined clearly enough to distinguish who may view comparisons versus who may trigger comparison requests? [Gap, Plan §Implementation Step 2]
- [X] CHK015 Are requirements defined for protecting operational logs and messages from exposing secrets, raw source rows, or unstable upstream payloads? [Completeness, Plan §Technical Context Constraints; Plan §Implementation Step 8]
- [X] CHK016 Is the phrase “authenticated backend access” specific enough to derive concrete requirement checks, or does the spec need stronger wording about protected resources and access outcomes? [Ambiguity, Plan §Implementation Step 2]
- [X] CHK017 Are security expectations for the render-outcome reporting surface clear enough to prevent unauthenticated or unrelated clients from submitting comparison render events? [Clarity, Plan §Implementation Step 2; Contract §/api/v1/demand-comparisons/{comparisonRequestId}/render-events]
- [X] CHK018 Do the security expectations in the plan align with the spec’s silence on authN/authZ, or should the spec explicitly reference protected planner access to avoid an undocumented dependency? [Consistency, Spec §Assumptions; Plan §Constitution Check]
- [X] CHK019 Are logging requirements consistent with the security constraint that raw source data and secrets must not be exposed through responses or operational records? [Consistency, Spec §FR-014; Plan §Technical Context Constraints; Contract §summary fields]
- [X] CHK020 Are unauthorized, forbidden, and invalid-request outcomes intentionally excluded from the feature requirements, or are they missing scenario classes for API and review quality? [Gap, Coverage]
- [X] CHK021 Are requirements defined for how security-related failures differ from business-state failures such as missing data, retrieval failure, or alignment failure? [Coverage, Gap]
- [X] CHK022 Is the assumption that “City planners already have access” backed by explicit security requirements, or does it leave access control as an undocumented external dependency? [Assumption, Spec §Assumptions]
- [X] CHK023 Are external dependency trust boundaries documented for upstream forecast and historical sources, or is the feature assuming all upstream data is safe without stating data-protection expectations? [Dependency, Gap]

## Data Requirements Quality

- [X] CHK024 Are the comparison entities and their purposes fully documented for requests, results, series points, missing combinations, and outcome records? [Completeness, Spec §Key Entities; Data Model §New Entity sections]
- [X] CHK025 Are the lineage relationships to approved historical data and active forecast products defined clearly enough to prevent a new comparison-specific source of truth from being inferred? [Completeness, Plan §Summary; Data Model §Reused Entities]
- [X] CHK026 Are the category and geographic classification requirements specific enough to define what makes a classification “defined” and eligible for comparison use? [Clarity, Spec §FR-015; Spec §Assumptions]
- [X] CHK027 Is the distinction between “no matching data” and “retrieval failure” explicit enough in both the spec and data model to support unambiguous stored outcomes? [Clarity, Spec §FR-010; Spec §FR-011; Spec §FR-011b; Spec §FR-011c; Data Model §DemandComparisonRequest]
- [X] CHK028 Is the clarified mixed-availability extension defined precisely enough to tell when `partial_forecast_missing` applies versus `forecast_only`? [Ambiguity, Spec §FR-011; Spec §FR-011a; Data Model §DemandComparisonRequest]
- [X] CHK029 Are comparison granularity requirements defined clearly enough to determine when hourly, daily, or weekly normalization is allowed? [Clarity, Data Model §DemandComparisonResult; Contract §DemandComparisonResponse]
- [X] CHK030 Do the outcome vocabularies remain consistent across the spec, data model, plan, and contract for success, partial-result, retrieval-failure, alignment-failure, and render-failure states? [Consistency, Spec §Functional Requirements; Data Model §DemandComparisonRequest; Plan §Phase 1 Design Summary; Contract §DemandComparisonResponse]
- [X] CHK031 Are the forecast product names and forecast granularity definitions aligned with the earlier forecast specs rather than introducing conflicting terminology? [Consistency, Data Model §DemandComparisonRequest; Contract §DemandComparisonResponse; Assumption against prior specs]
- [X] CHK032 Are requirements defined for partial historical coverage within a selected time range, or does the spec leave that data-boundary scenario underspecified? [Coverage, Edge Case, Spec §Edge Cases]
- [X] CHK033 Are requirements defined for requests with no geography filter so the data model does not rely on implied null semantics? [Gap, Data Model §DemandComparisonRequest]
- [X] CHK034 Are validation rules documented for mutually exclusive forecast source references and their relationship to the selected comparison range? [Coverage, Data Model §DemandComparisonRequest]
- [X] CHK035 Are assumptions about upstream approved datasets and active forecast markers documented as enforceable requirements rather than only background context? [Assumption, Spec §Assumptions; Plan §Implementation Step 1]

## API Requirements Quality

- [X] CHK036 Are all intended API surfaces documented, including comparison context retrieval, comparison execution, and render-outcome reporting? [Completeness, Plan §Implementation Step 8; Contract §paths]
- [X] CHK037 Are request-field requirements complete for category filters, geography filters, time range, and warning acknowledgment behavior? [Completeness, Contract §DemandComparisonQueryRequest; Spec §FR-001; Spec §FR-008]
- [X] CHK038 Are response requirements complete for warning-required, success, partial-result, and explicit failure outcomes? [Completeness, Contract §DemandComparisonResponse; Spec §FR-007; Spec §FR-010 to §FR-013]
- [X] CHK039 Is the contract clear about when `warning_required` is returned versus when a comparison request has actually executed? [Clarity, Contract §DemandComparisonResponse; Plan §Implementation Step 4]
- [X] CHK040 Are error outcome requirements sufficiently specific to distinguish retrieval failure from alignment failure at the API contract level? [Clarity, Contract §DemandComparisonResponse; Spec §FR-011b; Spec §FR-011c; Spec §FR-012]
- [X] CHK041 Is the API contract explicit enough about whether `forecastProduct`, `forecastGranularity`, and source version identifiers are required, optional, or mutually dependent? [Clarity, Contract §DemandComparisonResponse; Data Model §DemandComparisonResult]
- [X] CHK042 Do the response outcome values align with the spec and data model, especially for `historical_only`, `forecast_only`, and the clarified `partial_forecast_missing` extension? [Consistency, Spec §FR-010; Spec §FR-011; Spec §FR-011a; Data Model §DemandComparisonRequest; Contract §DemandComparisonResponse]
- [X] CHK043 Is the separate render-event reporting pattern consistent with the feature’s stated requirement for render-failure handling and logging? [Consistency, Spec §FR-013; Plan §Phase 1 Design Summary; Contract §/api/v1/demand-comparisons/{comparisonRequestId}/render-events]
- [X] CHK044 Are API-facing requirements measurable enough to determine whether response shapes and status distinctions satisfy UC-08 acceptance coverage without inferring missing rules? [Measurability, Plan §Verify acceptance behavior; Contract §schemas]
- [X] CHK045 Are failure-response requirements complete for invalid input and access-control outcomes, or are those intentionally outside the current API requirement scope? [Gap, Coverage]
- [X] CHK046 Is the dependency on upstream historical and forecast lineage reflected in the contract clearly enough to avoid leaking internal storage assumptions into API requirements? [Dependency, Contract §source...Id fields; Plan §Implementation Step 1]
- [X] CHK047 Are versioning expectations for the comparison API intentionally defined or intentionally omitted? [Gap, API Versioning]

## Performance Requirements Quality

- [X] CHK048 Are performance targets defined for the primary comparison journey, not just for generic “completed requests”? [Completeness, Spec §SC-002; Plan §Performance Goals]
- [X] CHK049 Are explicit performance requirements defined for warning-required high-volume requests, including the timeliness of warning delivery before retrieval begins? [Completeness, Spec §FR-007; Spec §SC-003]
- [X] CHK050 Are performance expectations documented for partial-result paths such as forecast-only and historical-only outcomes, or are those response classes left without timing requirements? [Gap, Spec §FR-010; Spec §FR-011; Spec §SC-002]
- [X] CHK051 Is “within 10 seconds for at least 95% of non-high-volume requests” precise enough about start and stop timing boundaries to be objectively measured? [Clarity, Plan §Performance Goals; Spec §SC-002]
- [X] CHK052 Are “exceptionally large” and “system-defined large-request threshold” specified clearly enough to support measurable performance and warning requirements? [Ambiguity, Spec §FR-007; Spec §Assumptions]
- [X] CHK053 Do performance expectations stay consistent between the spec success criteria and the plan’s technical performance goals? [Consistency, Spec §SC-002; Plan §Performance Goals]
- [X] CHK054 Are performance-related degradation expectations consistent with the requirement to block on alignment failure and to surface explicit retrieval failures? [Consistency, Spec §FR-011b; Spec §FR-011c; Spec §FR-012; Plan §Implementation Step 5]
- [X] CHK055 Are requirements defined for what performance guarantees still apply after a planner acknowledges a high-volume warning? [Coverage, Spec §User Story 2; Plan §Implementation Step 4]
- [X] CHK056 Are performance requirements defined for render-failure reporting timeliness, or is that non-functional path intentionally left unspecified? [Gap, Plan §Implementation Step 7; Contract §DemandComparisonRenderEvent]
- [X] CHK057 Can the performance requirements be measured without relying on implementation-specific assumptions such as internal caching or database behavior? [Measurability, Spec §Success Criteria; Plan §Technical Context]
- [X] CHK058 Are scalability assumptions for multi-category and multi-geography requests documented clearly enough to justify the chosen performance thresholds? [Assumption, Plan §Scale/Scope; Spec §Edge Cases]

## Notes

- This file consolidates the domain checklists from `ux.md`, `security.md`, `data.md`, `api.md`, and `performance.md`.
- The original per-domain checklist files are retained for focused review when needed.
