---
Status: accepted
---

# 4-dimensional domain model for chrome-agent architecture

The chrome-agent business domain has four orthogonal axes: Capability (convert,
fetch, extract…), Execution Path (explore sampling vs pipeline production vs
site-samples testing), Strategy Variant (generic, fandom, wiki.gg…), and Input
Format (rendered HTML, wikitext, API JSON). Every module in the codebase
occupies a point in this 4-axis space.

Prior governance (SSOT maps, capability framework, C1-C10 constraints) only
modelled the Capability axis. This left Execution Path, Variant, and Format
unexpressed in any structural layer — directory layout, naming schema, spec
model, documentation, or governance. Modules that were behavioural mirrors
(e.g. explore vs pipeline HTML conversion) or site variants drifted apart
without detection, because their equivalence was never declared and nothing
enforced it.

We explicitly adopt these four dimensions as first-class architectural
concepts. Future structure must declare dimensional coordinates for modules,
name mirror/variant relationships, and provide executable equivalence proofs
for mirrors. This is the governance layer that closes the gap between domain
complexity (legitimately multi-dimensional) and structural expression
(previously flat, capability-only).

## Considered alternatives

- **Stay single-dimension, add more checks**: would compound the existing
  pattern — checks themselves drift because they bind to ambiguous targets.
- **Full physical refactor by all four axes**: premature without defining
  which dimensions need physical separation vs logical declaration.
