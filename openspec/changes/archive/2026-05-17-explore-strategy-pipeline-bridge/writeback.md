# Writeback Plan — explore-strategy-pipeline-bridge

## Overview

- **Change**: explore-strategy-pipeline-bridge
- **Date**: 2026-05-17
- **Prerequisite**: verification.md — all 14 spec requirements and 18 tasks verified
- **Status**: Ready for writeback execution

---

## Writeback Targets

| Target | Action | Field Mapping | Evidence |
|--------|--------|--------------|----------|
| `scripts/chrome-agent-cli.mjs` | Modify | Added `api.platform` check in `selectFetcher()`; new `runMediawikiApiFetch()`; modified `runEngineFetch()` dispatch; added `conversion_engine`/`converter_path` to `runExplore()` return | Lines examined in code review |
| `scripts/explore/sample_converter.py` | Modify | Added `main()` with `apply` and `fetch-and-apply` subcommands; added `_load_extraction_rules()` helper | CLI help output verified |
| `scripts/explore/main.py` | Modify | Engine selection checks `api_config` before probe chain | Code diff reviewed |
| `configs/engine-registry.json` | Modify | Added `mediawiki-api` entry with `type: "api"`, `status: "frozen"`, `default_rank: 0` | Registry JSON parsed |
| `sites/anti-crawl/rate-limit-api.md` | Modify | Added `mediawiki-api` at `rank: 0`; demoted `scrapling-fetch` to `rank: 1` | Frontmatter updated |
| `~/.agents/skills/chrome-agent/SKILL.md` | Modify | Added "Route to Sample Conversion" section documenting API and non-API paths | Section added |
| `AGENTS.md` | Modify | Added documentation for `sample_converter.py` CLI subcommands | Entry added under "API 路径" |

---

## Field Mapping Details

### `chrome-agent-cli.mjs`

| Before | After | Reason |
|--------|-------|--------|
| `selectFetcher()` starts with `engine_preference` checks | Starts with `strategy?.document?.api?.platform` check | API platform must win before any scrapling logic |
| No `runMediawikiApiFetch()` | New function: reads strategy, extracts page title, calls action=parse, writes HTML | API engine handler per spec |
| `runEngineFetch()` handles `cloakbrowser` and scrapling | Also handles `"mediawiki-api"` via `runMediawikiApiFetch()` | API fetcher dispatch |
| `runExplore()` strategy-matched return has no conversion fields | Returns `conversion_engine` and `converter_path` | Agent needs this to find the conversion tool |

### `sample_converter.py`

| Before | After | Reason |
|--------|-------|--------|
| No `main()` entry | `main()` with `apply` and `fetch-and-apply` subcommands + `argparse` | Standalone CLI discovery by agent |

### `main.py`

| Before | After | Reason |
|--------|-------|--------|
| `engine = protection.get("engine_override") or probe_result.get("success_engine") or "scrapling-get"` | Checks `api_config` first; if `type == "mediawiki"`, sets `engine = "mediawiki-api"` | API-discovered platforms should not go through scrapling |

### `engine-registry.json`

| Before | After | Reason |
|--------|-------|--------|
| No `mediawiki-api` entry | New entry: `id: "mediawiki-api"`, `type: "api"`, `status: "frozen"`, `default_rank: 0`, `applicable_platforms: ["mediawiki", "mediawiki-fandom", "mediawiki-wiki-gg"]` | New engine type per engine-contracts spec |

### `rate-limit-api.md`

| Before | After | Reason |
|--------|-------|--------|
| `engine_priority`: `scrapling-fetch` (rank 1), `chrome-devtools-mcp` (rank 2) | Added `mediawiki-api` (rank 0), `scrapling-fetch` demoted to rank 1 | MediaWiki API avoids rate limiting |

---

## Prerequisites

- [x] verification.md confirms all 14 spec requirements implemented
- [x] All 18 tasks completed (verified via task checkboxes and code review)
- [x] No pending review items

## Writeback Execution

Writeback is complete — all targets have been modified during implementation. No additional write passes needed.

### Audit Trail

```
Writeback authority: chrome-agent repo maintainer
Writeback timing: 2026-05-17 (implementation day)
Writeback scope: conclusions only (field mappings, status), no spec/design/tasks duplication
Status: All targets written during implementation cycle
```
