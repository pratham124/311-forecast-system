# Research: Configure Alert Thresholds and Notification Channels

## Decision: Use one shared active configuration for the whole alerting system

**Rationale**: The accepted clarification chose one shared active configuration rather than per-manager preferences. A single active configuration keeps downstream alert behavior deterministic and aligns with the requirement that future alerts follow one saved set of thresholds, channels, and scoped frequency or deduplication rules.

**Alternatives considered**:
- Store one configuration per operational manager: rejected because it conflicts with the clarified shared-configuration requirement and would make alert behavior ambiguous.
- Store one configuration per channel: rejected because thresholds and suppression rules must be evaluated as one coherent policy set.

## Decision: Persist immutable configuration snapshots and switch the active pointer atomically

**Rationale**: UC-13 requires the previous configuration to remain active whenever validation or storage fails. Immutable version snapshots plus a single active marker make rollback-free continuity straightforward and preserve a stable audit trail of what configuration future alerts were using at any moment.

**Alternatives considered**:
- Update the current configuration in place: rejected because partial writes or failed saves would risk corrupting the active policy set.
- Persist only the latest serialized blob with no versioning: rejected because it weakens traceability and makes save outcomes harder to audit.

## Decision: Record save attempts separately from saved configuration versions

**Rationale**: Validation rejection and storage failure are user-visible outcomes in UC-13, but neither should create a new active configuration. A dedicated update-attempt record preserves those outcomes for observability without promoting invalid or failed drafts into the canonical saved configuration lineage.

**Alternatives considered**:
- Log failures only in unstructured application logs: rejected because acceptance tests require traceable save outcomes.
- Create draft configuration versions for failed attempts: rejected because failed drafts are not part of the active saved configuration lineage.

## Decision: Validate channels against the platform-supported capability set at save time

**Rationale**: The spec states that supported channels are provisioned elsewhere and that unsupported or unavailable selections must be rejected. Resolving channel support during both load and save keeps the UI honest while ensuring the final persisted configuration reflects channels that are truly valid at the moment of activation.

**Alternatives considered**:
- Hard-code channel options in UC-13: rejected because support is supplied elsewhere in the platform and can vary by environment.
- Validate channels only on the frontend: rejected because unsupported channels must be rejected before persistence even if the client is stale or bypassed.

## Decision: Keep frequency and deduplication controls in one scoped delivery-preference record

**Rationale**: UC-13 applies frequency and deduplication rules per service category with optional geography scope. A single scoped preference record keeps that policy surface coherent and avoids splitting closely related suppression behavior across multiple loosely coupled tables.

**Alternatives considered**:
- Store one table for frequency and a separate table for deduplication: rejected because both features share the same scope and save lifecycle in this use case.
- Use one global deduplication rule for all alerts: rejected because the spec explicitly requires scoped behavior rather than one global rule.

## Decision: Keep downstream alerting workflows as consumers of the active configuration

**Rationale**: UC-13 governs authoring and activation of alert settings, not alert generation itself. Reusing UC-10 and UC-11 downstream workflows preserves feature boundaries and avoids redefining shared alerting entities in the configuration use case.

**Alternatives considered**:
- Move threshold evaluation logic into UC-13 persistence: rejected because it mixes authoring concerns with runtime alert generation.
- Duplicate threshold and channel semantics inside new UC-13-only alert tables: rejected because it would fracture shared alert behavior across multiple sources of truth.
