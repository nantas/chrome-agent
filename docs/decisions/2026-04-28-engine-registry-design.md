# Engine Registry Design Decision

## Context

Phase 2 froze the engine contracts, but the engine inventory, routing hints, error matrix, and smoke-check summary remained partially duplicated inside `openspec/specs/engine-contracts/spec.md`. Phase 3 standardized strategy files, yet anti-crawl ordering still relied on `engine_sequence.purpose`, which could not express a precise priority chain or integrate with site-level overrides.

Phase 4 needed a decoupled registry, a consistent scoring model, and a governed extension path for new engines without changing the runtime orchestration layer.

## Decision

1. Introduce `configs/engine-registry.json` as the machine-readable engine inventory and keep contract specs as the behavioral source of truth.
2. Score engines on `efficiency`, `stability`, and `adaptability`, with mandatory rationale notes for each score.
3. Derive `composite_score` with the weighted formula `round((adaptability * 0.50 + stability * 0.30 + efficiency * 0.20) * 100)`.
4. Derive `default_rank` from family-aware routing rules that enforce Scrapling-first ordering instead of raw score order.
5. Replace anti-crawl `engine_sequence` with `engine_priority`, using contiguous integer `rank` values and canonical-chain ordering.
6. Add optional site-strategy `engine_preference` at both file and per-page scope.
7. Define `extension-api` as the mandatory artifact checklist, naming convention, validation gate, and template source for engine additions.
8. Use `scrapling-bulk-fetch` as the example extension to validate the workflow end to end.

## Consequences

- The engine inventory is now queryable without parsing multiple spec tables.
- Strategy files can express precise priority ordering and targeted overrides without embedding runtime orchestration logic.
- New engine additions must update three governance layers together: contract spec, registry entry, and engine-contracts aggregation.
- Existing docs and strategy files must stay aligned with registry identifiers to avoid drift.
- Composite score values must follow the documented formula even when earlier planning notes contained conflicting literals.
