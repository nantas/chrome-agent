# Writeback Targets

## Targets

### 1. `openspec/specs/site-strategy-schema/spec.md` — MODIFIED

- **Change**: Merge `api` field delta from `openspec/changes/mediawiki-api-extraction/specs/site-strategy-schema/spec.md` into frozen spec
- **Precondition**: verification.md confirms api field works with real strategies
- **Status**: Ready

### 2. `openspec/specs/mediawiki-api-extraction/spec.md` — NEW (freeze)

- **Change**: Promote `openspec/changes/mediawiki-api-extraction/specs/mediawiki-api-extraction/spec.md` to frozen spec
- **Precondition**: verification.md confirms all spec requirements implemented
- **Status**: Ready

### 3. `scripts/mediawiki-api-extract` — NEW

- **Change**: CLI tool already created during implementation
- **Precondition**: Phase A/B/C validated on balatrowiki.org
- **Status**: Done ✓

### 4. `sites/strategies/balatrowiki.org/strategy.md` — MODIFIED

- **Change**: `api` field added during implementation
- **Precondition**: api.platform validated, YAML parses correctly
- **Status**: Done ✓

### 5. `sites/strategies/vampire.survivors.wiki/strategy.md` — MODIFIED

- **Change**: `api` field added during implementation
- **Precondition**: api.platform validated, YAML parses correctly
- **Status**: Done ✓

### 6. `sites/strategies/registry.json` — MODIFIED

- **Change**: balatrowiki.org entry added, backend fields added
- **Precondition**: registry.json validates, both entries have matching backend
- **Status**: Done ✓

### 7. `AGENTS.md` — MODIFIED

- **Change**: Add MediaWiki API route to crawl path documentation
- **Precondition**: crawl command integration complete
- **Status**: Pending

## Field Mapping

| Writeback Target | Source | Field/Section | Action |
|-----------------|--------|--------------|--------|
| site-strategy-schema spec | change spec delta | `api` object definition | Merge |
| mediawiki-api-extraction spec | change spec | Full spec | Freeze |
| balatrowiki.org strategy | design + proposal | `api` frontmatter field | Written |
| vampire.survivors.wiki strategy | design + proposal | `api` frontmatter field | Written |
| registry.json | design | balatrowiki.org entry + backend fields | Written |
| AGENTS.md | design Decision 1 | Crawl route API branch | Pending |

## Non-writeback (preserved as-is)

- `scripts/clean-mediawiki.sh` — Continues serving Scrapling fallback path
- `openspec/specs/mediawiki-extraction-patterns/spec.md` — No changes needed
- `openspec/specs/strategy-guided-crawl/spec.md` — No changes needed (API is internal routing)
- `configs/engine-registry.json` — No new engine type added

## Writeback Execution Evidence

| Target | Action | Date | Executor | Result |
|--------|--------|------|----------|--------|
| `AGENTS.md` | Added MediaWiki API route to engine selection strategy + directory governance + reference index | 2026-05-04 | pi agent | ✓ Written |
| `openspec/specs/mediawiki-api-extraction/spec.md` | Promoted from change spec to frozen spec | 2026-05-04 | pi agent | ✓ Copied |
| `openspec/specs/site-strategy-schema/spec.md` | Merged api field delta into frozen spec | 2026-05-04 | pi agent | ✓ Appended |
| `sites/strategies/balatrowiki.org/strategy.md` | api field added (done during implementation) | 2026-05-04 | pi agent | ✓ Already done |
| `sites/strategies/vampire.survivors.wiki/strategy.md` | api field added (done during implementation) | 2026-05-04 | pi agent | ✓ Already done |
| `sites/strategies/registry.json` | balatrowiki.org entry + backend fields (done during implementation) | 2026-05-04 | pi agent | ✓ Already done |
| `scripts/mediawiki-api-extract` | CLI tool created (done during implementation) | 2026-05-04 | pi agent | ✓ Already done |
| `scripts/mediawiki-api-extract` (round 2) | DPL table restoration, HTML comment removal, H1 titles, filename space→underscore, image URL encoding | 2026-05-04 | pi agent | ✓ Updated |
| `openspec/specs/mediawiki-api-extraction/spec.md` (round 2) | Added DPL 表格还原 + HTML comment removal requirements | 2026-05-04 | pi agent | ✓ Updated |
| `openspec/specs/site-strategy-schema/spec.md` (round 2) | No additional changes needed | 2026-05-04 | pi agent | ✓ N/A |
