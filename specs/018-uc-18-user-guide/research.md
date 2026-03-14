# Research: Access User Guide

## Decision: Limit user-guide access to signed-in users

**Rationale**: The accepted clarification in the spec states that any signed-in user can access the guide. Keeping the guide behind existing authenticated sessions aligns with the constitution’s backend-enforced access model and avoids introducing a second public documentation surface.

**Alternatives considered**:
- Make the guide publicly accessible: rejected because UC-18 is defined as an in-product help feature and does not require anonymous access.
- Restrict the guide to specific roles: rejected because the feature goal is broad product usability for all authenticated users.

## Decision: Retrieve only the current published guide at request time

**Rationale**: UC-18 requires the current published guide and does not mention version browsing or historical content. Loading the current published guide on demand keeps the behavior simple and ensures users always see the active instructional content.

**Alternatives considered**:
- Offer guide version history or version switching: rejected because it adds scope not present in the use case or acceptance tests.
- Cache per-user guide copies as the primary source: rejected because the source of truth should remain the published guide content, not a user-scoped duplicate.

## Decision: Normalize guide content and navigation metadata into one stable backend response

**Rationale**: The guide may be stored in a documentation service or storage system, but the frontend must not depend on raw source formats. A normalized response lets the client render readable content and move between sections or pages without coupling to the underlying document structure.

**Alternatives considered**:
- Return raw documentation source content directly to the frontend: rejected because it leaks source-format assumptions into the client and weakens typed contract stability.
- Split guide metadata and content across multiple frontend-managed requests: rejected because UC-18’s primary flow is a single open-and-read action, and unnecessary request choreography increases failure modes.

## Decision: Treat retrieval failure and render failure as separate observable outcomes

**Rationale**: The spec and acceptance tests distinguish between content that cannot be retrieved and content that was retrieved but could not be displayed. Separate outcomes keep diagnostics accurate and prevent operational teams from treating backend success as equivalent to a successful user experience.

**Alternatives considered**:
- Merge all failures into one generic guide-load error: rejected because it loses the distinction required by UC-18 extensions and acceptance tests.
- Log only backend retrieval outcomes: rejected because client-side render failures would remain invisible.

## Decision: Record one guide-access event per open attempt and a separate render outcome when needed

**Rationale**: A dedicated access event preserves the core audit trail for successful access and retrieval failures, while a separate render-outcome report captures the final user-visible result for cases where the guide could not be displayed after retrieval.

**Alternatives considered**:
- Persist only unstructured logs: rejected because acceptance alignment requires queryable success and failure outcomes.
- Persist full guide-content snapshots per access: rejected because UC-18 needs observability, not per-request content duplication.

## Decision: Keep navigation within one loaded guide session using ordered sections or pages

**Rationale**: The user must move between available sections or pages without reopening the guide. Exposing ordered navigation metadata in the guide payload allows the frontend to preserve readability and availability during normal in-session navigation.

**Alternatives considered**:
- Force a full guide reload for every section change: rejected because it works against the navigation requirement and increases avoidable failure risk.
- Leave navigation structure undefined and let the frontend infer it: rejected because it creates contract ambiguity and weaker testability.
