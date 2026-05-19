# Writeback Report

**Change**: `split-fetch-convert-phases`
**Date**: 2026-05-19
**Status**: Implementation complete, verification documented

## Summary of Changes

### New Capabilities
1. **page-content-cache**: Persistent cache layer at `.cache/<platform>/<domain>/<safe_title>.json`
2. **pipeline-fetch-phase**: Independent `--phase fetch` (API → cache)
3. **pipeline-convert-phase**: Independent `--phase convert` (cache → Markdown → assembly)

### Modified Capabilities
4. **mediawiki-api-extraction-pipeline**: Phase B split into `fetch_single_page` / `convert_single_page`; `--phase` choices updated
5. **pipeline-cli-entry**: `--phase` choices = `all/discover/fetch/convert/assemble`; `--re-fetch` flag added
6. **strategy-guided-crawl**: Scrapling path supports `--phase fetch` / `--phase convert`

### Removed
- `--phase extract`, `A`, `B`, `C`, `homepage` — all removed from argparse choices
- `cmd_pipeline()` deprecated value mapping — removed

### Deprecated
- `--keep-html` — warns and guides to `--phase fetch`
- `--no-markdown` — tips to `--phase fetch`

### Fixed
- `extraction_results.json` now saves `content` and `rendered_html` (was only `status` + `error`)

## Writeback Targets

### 1. AGENTS.md

Requires updates to:
- §6 (Pipeline Strategy Schema) — no change needed (schema unchanged)
- §9 (Development) — no change needed (no new dev patterns)
- §2 (Capability Framework) — should mention fetch/convert phases

### 2. README.md

Requires updates if it describes `--phase` arguments. Check current README.

### 3. Project page (Obsidian)

Not yet discovered; writeback deferred.

## Artifacts

| File | Purpose |
|------|---------|
| `scripts/mediawiki-api-extract/pipeline/cache.py` | Cache layer module |
| `scripts/mediawiki-api-extract/pipeline/phase_b.py` | Refactored with fetch/convert split |
| `scripts/mediawiki-api-extract/pipeline/orchestrate.py` | Added run_phase_fetch/run_phase_convert, modified run_pipeline |
| `scripts/mediawiki-api-extract/cli.py` | Updated --phase choices, removed deprecated mapping |
| `scripts/chrome-agent-cli.mjs` | Updated runCrawl, added deprecation warnings, scrapling cache helpers |
| `.gitignore` | Added `.cache/` |
| `openspec/changes/split-fetch-convert-phases/verification.md` | Verification report |

## Pending Actions

1. If `README.md` describes `--phase` values, update to reflect new choices
2. AGENTS.md capability framework may need mention of fetch/convert phases
3. Obsidian project page writeback (when discovered)
