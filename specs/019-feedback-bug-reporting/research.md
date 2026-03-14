# Research: Submit Feedback or Bug Report

## Decision: Require explicit report type selection at intake

**Rationale**: Mandatory `Feedback` vs `Bug Report` classification reduces reviewer triage ambiguity and supports cleaner operational reporting aligned with clarified UC-19 scope.

**Alternatives considered**:
- Optional report type with reviewer-side classification: rejected because it shifts avoidable ambiguity to reviewers.
- Auto-classification only from description text: rejected because false classification risk is high for short or ambiguous submissions.

## Decision: Allow anonymous and authenticated submissions with optional contact details

**Rationale**: This model maximizes report capture and still allows follow-up when users voluntarily provide contact information.

**Alternatives considered**:
- Authenticated submissions only: rejected because it increases friction and can suppress important bug reports.
- Anonymous-only submission: rejected because it removes identity context when authenticated users can provide valuable reproducibility details.

## Decision: Make local persistence the source of truth for accepted submissions

**Rationale**: Accepted reports must remain reviewable even when external issue-tracking integrations are unavailable; local persistence guarantees resilience and traceability.

**Alternatives considered**:
- External issue tracker as sole system of record: rejected because external outages would cause report loss or user-visible inconsistency.
- Log-only fallback during outages: rejected because structured reviewer retrieval and acceptance-test verification require queryable records.

## Decision: Use explicit processing lifecycle states with status-event history

**Rationale**: Lifecycle states and immutable status events make operations diagnosable and support measurable outcomes in the specification.

**Alternatives considered**:
- Single mutable status field only: rejected because historical transitions become opaque.
- Free-form textual status entries: rejected because they reduce contract stability and testability.

## Decision: Keep duplicate submissions as separate records in UC-19

**Rationale**: Potential duplicates may represent distinct user impact contexts; capturing each submission avoids accidental data loss and keeps deduplication policy out of this feature scope.

**Alternatives considered**:
- Hard blocking near-duplicate submissions: rejected because it can prevent valid reports from being captured.
- Silent merge into existing reports: rejected because it hides user intent and reduces auditability.
