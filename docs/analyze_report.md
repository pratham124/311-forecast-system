# Analyze Report

Below is a report of running /speckit.analyze for each use case. We've included the generated analysis table that speckit made and any actions taken to resolve any issues.

Below is a template of how we should write the analyze reports that Codex generates. Copy paste the table that it generated and include it here. I would address any HIGH severity reports, and the LOW severity ones are probably not necessary to address which you can state.

## Use Case 11 (TEMPLATE)
### Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A1 | Inconsistency | HIGH | spec.md:35 | Acceptance Scenario 7 allows update “per policy,” but FR‑008 + clarifications
require blocking duplicates. | Align scenario 7 (and edge case 10a1) to block‑only behavior. |
| A2 | Inconsistency | MEDIUM | spec.md:83 | Key Entities uses “Assigned paper” while plan/data model use
RefereeAssignment. | Rename to RefereeAssignment (assigned paper) for consistency. |
| B1 | Ambiguity | MEDIUM | spec.md:User Story 1 | Deadline enforcement is mentioned (“if enforced”) without specifying
the deadline source. | Define a deadline source (e.g., assignment.reviewDeadline) or explicitly state none. |
| C1 | Underspecification | LOW | spec.md:Edge Cases | “Clear messaging” is required, but unauthorized access message
content isn’t specified. | Add explicit message requirement for unauthorized/unassigned access. |

For this analysis, we did find a critical inconsistency issue between the spec and plan/tasks. In A1, the spec mentions allowing updates to submitted reviews, but then clarifications later specified that duplicate submissions are blocked. I prompted to update the spec to align this scenario. I also fixed the naming inconsistencies in A2. I also fixed the B1 issue, we do not need an explicit deadline for reviews for now.

## Use Case 1
### Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution Alignment | CRITICAL | constitution.md:57, plan.md:29, tasks.md:74 | The constitution requires backend authentication, protected routes, and basic RBAC for backend APIs, but the spec/plan/tasks add trigger
and query endpoints without any auth or authorization requirement or task coverage. | Add explicit protected-route/auth requirements to the spec, update the plan security section, and add implementation/test tasks for backend
auth on ingestion endpoints before implementation. |
| G1 | Coverage Gap | CRITICAL | spec.md:73, plan.md:16, tasks.md:39 | FR-001 requires a configured schedule to trigger ingestion, but tasks only cover API wiring and manual/test trigger surfaces. There is no task for scheduler
job registration, schedule configuration, or scheduled execution wiring. | Add foundational tasks for scheduler setup, configured job registration, and scheduler-driven invocation of the ingestion pipeline. |
| I1 | Inconsistency | HIGH | tasks.md:48, tasks.md:104, tasks.md:127, tasks.md:153 | The task file says user stories can be implemented independently after Foundational, but later says US2 and US3 depend on US1 pipeline/query
work. This conflicts with the story-independence goal used throughout the spec/tasks workflow. | Move shared ingestion/query primitives into Foundational or explicitly declare US2/US3 as dependent increments and adjust the
“independently testable” framing accordingly. |
| U1 | Underspecification | HIGH | plan.md:14, tasks.md:39 | The plan requires durable PostgreSQL persistence for runs, cursor state, dataset versions, current marker, and notifications, but tasks contain models and DB session
work only. There is no migration/schema-bootstrap task. | Add foundational tasks for migration tooling and initial schema creation for all persisted UC-01 entities. |
| A1 | Ambiguity | MEDIUM | plan.md:18 | The plan uses vague non-functional wording such as “immediately after run completion” and “enough durable evidence,” which is not measurable and has no task-level enforcement. | Quantify
or downgrade these statements to non-governing guidance, or add measurable targets and matching tasks if they are intended as real requirements. |
| I2 | Inconsistency | MEDIUM | spec.md:18, spec.md:33, spec.md:92 | The spec declares UC-01 backend-only and out of scope for forecasting/dashboard work, but user story value statements still say dashboards and forecasts “stay
current” or “never switch.” That is mild scope-language drift. | Normalize the story language to focus on the authoritative current dataset and downstream readiness, not dashboard/forecast behavior. |
| E1 | Coverage Gap | LOW | tasks.md:135 | T044 is documentation-only and does not map clearly to a specific requirement, story, or constitution mandate. | Either link it to operational onboarding/traceability or drop it from
the executable task path. |

For this analysis, there were inconsistencies present. For C1, I prompted Codex again to ensure authentication was added to the spec/plan/tasks. For G1, I prompted Codex to add tasks for scheduler scheduler setup, configured job registration, and scheduler-driven invocation of the ingestion pipeline. For I1, I prompted Codex to declare US2/US3 as dependent increments and adjust the “independently testable” framing accordingly. For U1, I prompted Codex to add foundational tasks for migration tooling and initial schema creation for all persisted UC-01 entities. For A1, it is fine as it is. For I2, I prompted Codex to update the story language to focus on the backend features. For E1, I prompted Codex to link it to operation onboarding/traceability.

## Use Case 2
### Specification Analysis Report

  | ID | Category | Severity | Location(s) | Summary | Recommendation |
  |----|----------|----------|-------------|---------|----------------|
  | C1 | Constitution Alignment | CRITICAL | constitution.md:19, tasks.md:1 | The constitution requires specs, plans, tasks, and implementation changes to reference governing UC-XX identifiers. tasks.md names the feature but does
  not explicitly reference UC-02. | Add explicit UC-02 references in the task title, phase headers, or task descriptions. |
  | G1 | Coverage Gap | HIGH | spec.md:118, tasks.md:57 | SC-003 sets a 15-minute completion target, but no task explicitly implements or validates timing/performance measurement for that outcome. | Add a task for timing
  instrumentation and/or an integration/assertion task covering the 15-minute requirement. |
  | G2 | Coverage Gap | HIGH | spec.md:119, tasks.md:125 | SC-004 sets a 2-minute operator visibility target, but tasks cover visibility functionally, not the measurable timing requirement. | Add a task to validate or instrument
  operator visibility timing against the success criterion. |
  | I1 | Inconsistency | HIGH | plan.md:53, tasks.md:38 | plan.md project structure does not include backend/app/models/, but tasks.md creates and uses backend/app/models/validation_models.py. | Either add models/ to the plan
  structure or move the task to a plan-defined location. |
  | I2 | Inconsistency | HIGH | tasks.md:68, tasks.md:89, tasks.md:114, tasks.md:216 | The implementation strategy says stories can be worked on in parallel, but US1, US2, and US3 all modify backend/app/pipelines/ingestion/
  validation_pipeline.py, and US1/US3 both modify backend/app/api/routes/validation_status.py. | Mark cross-story file contention explicitly and adjust the parallel strategy or break those tasks into non-conflicting components. |
  | I3 | Inconsistency | MEDIUM | spec.md:84, spec.md:92, plan.md:19 | The spec still uses “flagged for review” in requirements prose after standardizing the canonical outcome term as review-needed. Plan/tasks use review-needed
  consistently. | Normalize spec prose to the canonical status term, optionally mentioning “flagged for review” once as plain-language phrasing. |
  | U1 | Underspecification | MEDIUM | spec.md:104, plan.md:97, tasks.md:57 | The spec requires recording and exposing processing outcomes, but it does not name the processing-run entity that the plan/tasks center on
  (ValidationRun). | Add a concise spec-level key entity or definition for the processing run to improve traceability. |
  | A1 | Ambiguity | MEDIUM | spec.md:118 | SC-003 uses “normal operating conditions,” which is not objectively bounded in the spec. | Define the intended operating context or remove the phrase to keep the criterion objectively
  testable. |

  For this analysis, there were inconsistencies present. For C1, I prompted Codex to reference UC-02 in the tasks. For G1, I prompted Codex to add a task for 15-minute completion target. For G2, I prompted Codex similar to G1 to add task for timing requirement. For I1, I prompted codex that models should be in backend/app/repositories/models.py. For I2, I prompted to codex to break those tasks into non-conflicting components. For I3, I prompted codex to normalize spec prose to the canonical status term, optionally mentioning “flagged for review” once as plain-language phrasing. For U1, I prompted Codex to add a concise spec-level key entity. For A1, I prompted Codex to remove the phrase.

## Use Case 3
### Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution Alignment | CRITICAL | constitution.md:96, spec.md:74 | The spec does not explicitly identify the constitution-mandated required data sources, external integrations, or uncertainty outputs. plan.md adds
Edmonton 311 lineage, MSC GeoMet, Nager.Date, baseline, and P10/P50/P90, but spec.md does not. | Amend spec.md to name the governing UC-03 data sources/integrations and uncertainty outputs explicitly so the plan is not carrying
requirements the spec omits. |
| E1 | Coverage Gap | HIGH | spec.md:80, tasks.md:92 | FR-003 requires a forecast-run status surface, but there is no explicit task to implement GET /api/v1/forecast-runs/{forecastRunId} end-to-end. T030 only mentions response
shaping for reused-current outcomes. | Add a task for full run-status endpoint implementation, including status lookup, 404/422 handling, and normal success responses. |
| E2 | Coverage Gap | MEDIUM | spec.md:133, plan.md:18, tasks.md:128 | The measurable latency targets in SC-001 and SC-003 appear only as prose. No task explicitly adds timing assertions, instrumentation, or acceptance checks
for the 2-minute and 30-second thresholds. | Add explicit performance-verification tasks or acceptance assertions tied to the published thresholds. |
| I1 | Inconsistency | MEDIUM | plan.md:53, tasks.md:40 | plan.md’s source tree omits backend/app/models/, but T005 creates backend/app/models/forecast.py. | Either add models/ to the planned backend structure or move model
definitions to the planned location. |
| A1 | Ambiguity | MEDIUM | spec.md:89, spec.md:100, plan.md:143 | forecast-processing failure and cannot complete successfully are broad and underspecified in the spec, while the plan/tasks split failures into missing input,
enrichment, model, and storage categories. | Align spec.md with the failure taxonomy actually planned, or narrow plan/tasks to the spec’s published categories. |
| D1 | Duplication | LOW | spec.md:43, spec.md:66, spec.md:87 | Current-forecast reuse is stated in User Story 2, the edge cases, and FR-010 with near-identical behavior. | Keep one canonical wording for reuse behavior and let
the other sections reference it more tersely. |
| I2 | Inconsistency | LOW | spec.md:1, spec.md:16, plan.md:8 | Terminology drifts between “daily forecast”, “1-day demand forecast”, and “24-hour hourly operational forecast”. The intent is inferable, but the naming is not
perfectly consistent. | Standardize on one product name across all three artifacts, then use “24-hour hourly” as the clarifying subtitle. |
| U1 | Underspecification | LOW | tasks.md:134 | T042 records verification results back into tasks.md, which makes the task list double as an execution log. That behavior is not specified in spec.md or plan.md. | Record
verification results in a dedicated artifact or leave tasks.md as a plan-only checklist. |

For this analysis, there were inconsistencies present. For C1, I prompted Codex to amend spec.md to name the governing UC-03 data sources/integrations and uncertainty outputs explicitly so the plan is not carrying requirements the spec omits. For E1, I prompted Codex to add a task for full run-status endpoint implementation, including status lookup, 404/422 handling, and normal success responses. For E2, I prompted Codex to add explicit performance-verification tasks. For I1, I prompted Codex to move model definitions to the planned location repositories/models.py. For A1, I prompted Codex to align spec.md with the failure taxonomy actually planned. For D1, I prompted Codex to keep one canonical wording for reuse behavior and let the other sections reference it more tersely.For I2, it is fine as it is. FOr U1, I prompted codex to leave tasks.md as a plan-only checklist.

## Use Case 4
### Specification Analysis Report
| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution Alignment | CRITICAL | constitution.md:96-98, spec.md:67-110 | Spec does not explicitly
identify required external integrations/data sources (Socrata, GeoMet, Nager.Date), which is mandated by
constitution workflow gates. | Add explicit spec requirements/assumptions for canonical data source + required
external integrations. |
| C2 | Constitution Alignment | CRITICAL | constitution.md:34-37, plan.md:127-130, tasks.md:68-75 |
Constitution requires quantiles (P10/P50/P90) and baseline retention; UC-04 artifacts do not specify or task
these outputs. | Add requirements + plan/task coverage for quantile generation/persistence and baseline
comparator retention. |
| C3 | Constitution Alignment | CRITICAL | constitution.md:70-72, spec.md:72, plan.md:17-20 | Constitution
states forecast regeneration MUST occur daily; UC-04 specifies scheduled weekly generation as primary cadence.
| Reconcile by either adding daily regeneration requirement for this feature or explicitly amending
constitution in a separate process. |
| U1 | Underspecification | HIGH | spec.md:63, tasks.md:139-170 | Concurrency edge case is stated (“multiple
requests while run in progress”) but no explicit functional requirement or dedicated implementation task
exists for lock/idempotency behavior. | Add a concrete FR + task(s) for concurrency policy (dedupe, queue,
reject, or coalesce). |
| U2 | Underspecification | HIGH | spec.md:106, plan.md:107-110 | Spec only says “Operational Manager is
authorized”; role boundaries for read endpoints are not explicit in requirements, while plan/tasks assume
role-specific access. | Add explicit authz FRs for trigger and read operations to keep spec→plan→tasks
aligned. |

In this analysis, some critical issues were brought up. C1-C3 all address constitution violations related to forecast data sources, quantiles, and the regeneration schedule. The recommended actions make sense here so we prompted Codex to perform the stated fixes. U1 brings up a good point on the idempotency behavior being unspecified, so we prompted to make this explicit in the spec/plan. U2 also shows that we are not explicit in the role boundaries, so we also acted on this.

## Use Case 5
### Specification Analysis Report
| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution Alignment | CRITICAL | constitution.md:96, spec.md:77, plan.md:8 | The constitution requires every spec to identify required data sources, external integrations, forecast horizon, and uncertainty outputs. UC-05's spec names the uncertainty set but does not explicitly publish the upstream Edmonton 311 lineage, UC-02 cleaned dataset dependency, or the supported daily/weekly forecast products. | Add explicit spec requirements/assumptions for the approved cleaned dataset lineage, reused UC-03/UC-04 forecast products, and supported forecast products/horizons. |
| C2 | Constitution Alignment | CRITICAL | constitution.md:80, spec.md:81, plan.md:8, tasks.md:72 | The constitution requires forecast views to include category filtering, an alerts panel, last-updated visibility, and pipeline/data status visibility. The plan and tasks implement these, but the spec's functional requirements never require them. | Add explicit FRs and acceptance coverage for category filtering, alerts/status visibility, and last-updated metadata. |
| C3 | Constitution Alignment | CRITICAL | constitution.md:57, spec.md:23, plan.md:104, tasks.md:46 | Backend-enforced auth and RBAC are constitution MUSTs for this dashboard, but the spec does not state any authentication/authorization requirement or access-failure behavior. | Add spec-level auth/authz requirements and acceptance cases for protected read/write routes, including unauthorized and forbidden outcomes. |
| I1 | Inconsistency | HIGH | spec.md:25, plan.md:87, tasks.md:75 | The spec describes a singular "latest forecast" dashboard view, while the plan/tasks implement support for both daily and weekly products and a frontend product-selection flow. The user-facing selection/default behavior is not specified. | Decide whether managers can switch between products or only receive a system default, then publish that behavior in the spec. |
| G1 | Coverage Gap | HIGH | spec.md:131, tasks.md:135 | SC-007 requires usability validation that 90% of managers can identify the boundary and uncertainty on first review, but tasks cover component/integration testing only. | Add a task for usability validation or replace SC-007 with an objectively automatable criterion. |

In this analysis, some critical issues were brought up. For C1, we prompted Codex to add explicit FR and assumption coverage for UC-02 cleaned dataset lineage and UC-03/UC-04 forecast product scope. For C2, we added FRs and acceptance scenarios for category filtering, alerts/status visibility, pipeline/data status, and last-updated metadata. For C3, we added auth/authz FRs plus 401/403 acceptance and edge-case coverage. For I1, we made product selection explicit by specifying `daily_1_day` and `weekly_7_day` as the selectable forecast products in the spec. For G1, we replaced SC-007 with an automatable interpretability criterion based on explicit boundary markers, distinct series, and canonical quantile labels in the visualization payload.

## Use Case 6
### Specification Analysis Report
| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution Alignment | CRITICAL | spec.md:8 | The spec does not identify required data sources or
external lineage/integrations, even though the constitution says every spec must identify governing data
sources and integrations. | Add a brief governing dependencies section to the spec referencing UC-02 actuals
lineage and UC-03/UC-04 forecast lineage. |
| D1 | Duplication | HIGH | spec.md:84 | FR-006 appears twice with identical wording. | Remove the duplicate
and keep one FR-006. |
| I1 | Inconsistency | HIGH | spec.md:79, plan.md:30, tasks.md:45 | Auth/authorization is present in the plan
and tasks, but not stated in the spec requirements or scenarios. | Add explicit security/access requirements
to the spec, or remove unsupported auth work from plan/tasks. |
| E1 | Coverage Gap | MEDIUM | spec.md:129, tasks.md | SC-006 says planners should be able to determine
whether the engine outperformed baselines, but tasks only guarantee metric exposure, not an explicit
comparative summary or decision aid. | Either add a task/contract field for comparative summary, or relax SC-
006 to match the current design. |

In this analysis, some critical issues were brought up. C1 addresses a constitution violation related to forecast data sources. The recommended actions make sense here so we prompted Codex to perform the stated fixes. D1 notes a duplicate FR in our spec, so we got Codex to remove this as well. I1 and E1 also bring up valid inconsistencies and coverage gaps, so we performed the recommended fixes here as well. 

## Use Case 7
### Specification Analysis Report
| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution Alignment | CRITICAL | spec.md:8, plan.md:22, tasks.md:134 | UC-07 artifacts trace to
docs/UC-07.md, but not to the paired acceptance contract docs/UC-07-AT.md, which exists and is required by the
constitution. | Add explicit UC-07-AT.md references in the spec, plan, and acceptance-alignment task text. |
| I1 | Inconsistency | HIGH | spec.md:77, plan.md:103, tasks.md:45 | Authenticated access is part of the plan
and tasks, but the spec never states that historical-demand views or queries require authenticated or
authorized access. | Add an explicit access-control requirement and, if desired, an acceptance scenario or
edge case for unauthorized access. |
| A1 | Ambiguity | MEDIUM | spec.md:49, spec.md:88, tasks.md:88 | The warning flow says the planner may
“proceed or revise,” but the decline/revise path is not defined. Tasks only cover acknowledgement and
execution. | Define what happens when the planner declines the warning, then add matching frontend/backend
tasks if needed. |
| I2 | Inconsistency | MEDIUM | spec.md:11, plan.md:8, tasks.md:44 | The plan and tasks explicitly depend on
UC-02 approved cleaned-dataset lineage, but the spec only says “approved historical 311 demand data already
stored.” | Make the UC-02 lineage dependency explicit in the spec’s governing dependencies or assumptions. |

In this analysis, C1 presents a critical constitution violation that we fixed via prompting. There are also two inconsistencies I1 and I2 related to authentication and approved data storage between our use case and spec/plan. We prompted Codex to update the spec/plan to fix these inconsistencies. For A1, this is a valid abmiguity when the planner decides to ignore the warning. This should be explicitly defined, so we prompted to fix this as well.