# Design

## Context

MediaWiki API extraction pipeline (`scripts/mediawiki-api-extract/`) currently hard-codes all rate-limiting parameters:

- `concurrency=5` in `__main__.py` argparse
- `time.sleep(0.8)` (previously `0.04`) in `phase_b.py`
- `max_retries=5` (previously `3`) in `client.py`
- `delay *= 2.5` (previously `2`) in `client.py` 429 handling
- `jitter` is completely unimplemented

These values were patched at runtime for `slaythespire.wiki.gg` to avoid HTTP 429 failures. The `sites/anti-crawl/rate-limit-api.md` strategy exists but is never read by the pipeline. The `openspec/specs/site-strategy-schema/spec.md` `api` block has no `rate_limit` field.

The chosen architecture model (Model C) places parameter templates in Anti-Crawl strategies (`rate_limit_tiers`) and allows Site Strategies to reference a tier and locally override specific values. This unifies the existing strategy infrastructure with the request-control layer that was previously bypassed.

## Goals / Non-Goals

**Goals:**
- Eliminate all hard-coded rate limit constants from the MediaWiki API pipeline.
- Enable per-site rate limit configuration through `api.rate_limit` in site strategy files.
- Enable cross-site reusable rate limit templates through `rate_limit_tiers` in anti-crawl strategies.
- Maintain CLI override capability for runtime debugging.
- Implement jitter in exponential backoff to prevent thundering-herd retries.
- Provide safe code defaults (`concurrency=1`, `batch_delay_ms=1000`) so unconfigured runs do not trigger rate limits.
- Update `slaythespire.wiki.gg` strategy to use the new configuration schema with its empirically validated parameters.

**Non-Goals:**
- Generalizing this rate limit framework to Scrapling fetch paths (`scrapling-get`, `obscura-fetch`, etc.). This change is scoped to the MediaWiki API pipeline only.
- Adding a GUI or interactive configuration wizard for rate limit tuning.
- Back-filling rate limit configurations for all existing site strategies (only `slaythespire.wiki.gg` is updated as the reference implementation).
- Changing the anti-crawl detection/signal schema beyond adding `rate_limit_tiers`.

## Decisions

### 1. Four-layer override priority

**Decision**: CLI → Site Strategy local overrides → Anti-Crawl tier template → Code safe defaults.

**Rationale**:
- CLI at the top allows rapid iteration when tuning a new site without editing files.
- Site Strategy overrides give operators fine-grained control for sites with known empirical values.
- Anti-Crawl tiers provide class-level defaults (e.g., all `rate_limit` protections start conservative).
- Code defaults act as a safety net and ensure the pipeline never runs with undefined parameters.

### 2. `rate_limit_tiers` inside anti-crawl frontmatter

**Decision**: Add `rate_limit_tiers` as an optional object in the anti-crawl strategy YAML frontmatter, keyed by tier identifier.

**Rationale**:
- Keeps anti-crawl strategies self-contained: protection mechanism + recommended mitigation parameters in one file.
- Tier naming (`default`, `strict`, `very-strict`) is intuitive and allows future expansion without schema changes.
- The existing `anti_crawl_refs` field in site strategies already points to these files; no new reference mechanism is needed.

### 3. Partial override semantics

**Decision**: Site Strategy `api.rate_limit` fields override only the fields explicitly provided; all absent fields inherit from the resolved tier or code defaults.

**Rationale**:
- Operators should not have to copy an entire tier just to tweak one value (e.g., only `batch_delay_ms`).
- This minimizes configuration drift between site strategies and their referenced anti-crawl templates.

### 4. Safe code defaults are conservative

**Decision**: Code defaults are `concurrency=1`, `batch_delay_ms=1000`, `retry.max_retries=5`, `retry.jitter=true`.

**Rationale**:
- The previous defaults (`concurrency=5`, `batch_delay_ms=200`) caused mass 429 failures on `slaythespire.wiki.gg`.
- Conservative defaults penalize unconfigured runs with slower execution but prevent accidental rate limit violations.
- A well-configured site strategy or CLI override can easily restore higher throughput.

### 5. Jitter implementation

**Decision**: Apply ±20% uniform random jitter to each backoff delay calculation.

**Rationale**:
- Prevents synchronized retries from multiple concurrent workers after a shared rate limit event.
- 20% is a commonly accepted jitter range (see AWS Exponential Backoff and Jitter patterns).
- Implemented as a multiplier: `delay * (1 + random(-0.2, +0.2))`.

### 6. No `api.rate_limit` required for strategy validity

**Decision**: The `api.rate_limit` field is optional; its absence does not invalidate a site strategy file.

**Rationale**:
- Most existing site strategies do not need rate limit tuning (e.g., `balatrowiki.org` ran fine with defaults).
- Mandatory fields increase maintenance burden for low-traffic sites.

## Risks / Migration

| Risk | Impact | Mitigation |
|------|--------|------------|
| Pipeline refactoring introduces regressions in Phase B / client retry logic | High | Change is additive; existing behavior paths are replaced by resolved-config paths with identical semantics. The `slaythespire.wiki.gg` strategy will be the first validation target. |
| `rate_limit_tiers` schema is too rigid for future needs | Low | Tier structure is a flat map; new fields can be added to `rate_limit_config` via subsequent spec changes without breaking existing tiers. |
| Anti-crawl `registry.json` indexing does not surface `rate_limit_tiers` | Low | `registry.json` is an index for machine querying; `rate_limit_tiers` is runtime-resolved from the full anti-crawl file, not the index. If needed, a future change can add a summary field to `registry.json`. |
| Existing `client.py` 429 handling (`delay *= 2.5`) conflicts with tier-configured backoff | Medium | The 429 hard-coded multiplier will be removed. 429 responses will use the same retry path as other transient failures, with parameters from the resolved configuration. |
| Site operators confuse `anti_crawl_refs` tier reference with direct parameter placement | Low | Documented through spec scenarios and ADR. The `tier` field is explicitly inside `api.rate_limit`, separating "which protection mechanism" (`anti_crawl_refs`) from "which parameter template" (`tier`). |

**Migration notes**:
- Existing pipeline invocations without `--concurrency` will now default to `concurrency=1` (instead of `5`). Operators relying on the old default for low-protection sites must either pass `--concurrency 5` on the CLI or add `api.rate_limit.concurrency: 5` to the site strategy.
- The `time.sleep(0.8)` hard-coded patch in `phase_b.py` will be removed. `slaythespire.wiki.gg` strategy must include `api.rate_limit.batch_delay_ms: 800` before the next crawl.
