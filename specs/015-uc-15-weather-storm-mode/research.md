# Research: Storm Mode Forecast Adjustments

## Decision: Reuse UC-09 weather-provider and geography-alignment rules

**Rationale**: UC-15 depends on trustworthy weather context. UC-09 already established approved provider and alignment conventions, so storm mode should inherit those rules instead of introducing a second source-selection policy.

**Alternatives considered**:
- Create a storm-mode-specific provider mapping: rejected because it would duplicate weather-source governance and risk inconsistent scope matching.
- Allow ad hoc fallback station or geography substitution: rejected because UC-15 requires reliable, validated triggers before storm mode can affect forecasts or alerts.

## Decision: Persist one evaluation run per storm-mode decision pass

**Rationale**: UC-15 requires traceable monitoring, detection, validation, activation, forecast adjustment, alert evaluation, and notification outcomes for the same operational flow. A run-scoped anchor makes those outcomes reviewable under one correlation context.

**Alternatives considered**:
- Rely only on free-form logs: rejected because acceptance review needs structured, queryable records.
- Persist only activation rows with no run-level anchor: rejected because cross-scope and failure-path traceability would be fragmented.

## Decision: Keep storm mode scope-limited rather than global

**Rationale**: The spec repeatedly constrains storm mode to the affected category, geography, and time scope. A scope-limited activation model prevents unrelated forecast and alert paths from inheriting unsupported storm behavior.

**Alternatives considered**:
- Introduce one global storm-mode switch: rejected because it would over-apply uncertainty widening and alert sensitivity.
- Activate by geography only: rejected because category-specific sensitivity rules are part of the business requirement.

## Decision: Reuse existing notification-event persistence instead of creating a new storm notification table

**Rationale**: UC-15 changes sensitivity and decision context, not the platform’s notification-delivery mechanics. Existing shared notification records already capture delivery attempts, retry state, and manual follow-up, so UC-15 should link to them rather than duplicate them.

**Alternatives considered**:
- Add a standalone storm notification event table: rejected because it would duplicate shared delivery-tracking semantics from UC-10 and UC-11.
- Track only a boolean alert-sent flag in UC-15: rejected because it would lose retry and delivery-status detail required by the spec.

## Decision: Treat forecast-adjustment failure as forced baseline reversion for both forecast uncertainty and alert sensitivity

**Rationale**: FR-012 and FR-013 require that when storm-mode uncertainty adjustment fails, the system reverts both forecast uncertainty and alert sensitivity to baseline for the affected scope. Persisting this as an explicit reversion rule makes the safety requirement testable.

**Alternatives considered**:
- Keep storm-adjusted alert sensitivity even when uncertainty widening fails: rejected because it conflicts with the spec’s safe-fallback rule.
- Abort the entire run on adjustment failure: rejected because UC-15 requires continued operation on baseline behavior.

## Decision: Expose storm-mode state through authenticated diagnostics

**Rationale**: The spec allows effective parameters to be inspected through logs, records, or supported diagnostic outputs. Authenticated read APIs provide a stable, typed inspection path without requiring operators to reconstruct behavior from raw logs alone.

**Alternatives considered**:
- Keep parameter visibility only in logs: rejected because it is harder to validate and review consistently.
- Add a public storm-status endpoint: rejected because storm-mode diagnostics should remain authenticated and role-aware.
