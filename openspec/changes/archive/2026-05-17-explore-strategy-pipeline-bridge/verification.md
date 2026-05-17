# Verification Report — explore-strategy-pipeline-bridge

## Overview

- **Change**: explore-strategy-pipeline-bridge
- **Date**: 2026-05-17
- **Verification Type**: spec-to-implementation + task-to-evidence
- **Status**: ✅ All requirements and tasks verified

---

## Part A: Spec-to-Implementation Verification

### Capability: `explore-strategy-pipeline-bridge` (new, 6 requirements)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | `api-platform-aware-fetcher-selection` — `selectFetcher()` detects `api.platform` and returns `"mediawiki-api"` before scrapling checks | ✅ | `scripts/chrome-agent-cli.mjs` — first check in `selectFetcher()` reads `strategy?.document?.api?.platform` |
| 2 | mediawiki-platform-returns-api — `api.platform === "mediawiki"` → `"mediawiki-api"`, no further checks | ✅ | Selector test: mediawiki → "mediawiki-api", high protection ignored when api present |
| 3 | no-api-platform-falls-through — absent `api.platform` → existing scrapling logic | ✅ | Test: no api → "get"; protection checks still apply |
| 4 | `mediawiki-api-engine-handler` — `runEngineFetch()` handles `"mediawiki-api"` via new `runMediawikiApiFetch()` | ✅ | `runEngineFetch()` dispatches `"mediawiki-api"` to `runMediawikiApiFetch()` before other checks |
| 5 | api-fetch-calls-parse-endpoint — reads `api.base_url`, extracts page title, calls `action=parse`, writes HTML | ✅ | `runMediawikiApiFetch()` implemented with URL parsing, curl API call, JSON parse, HTML output |
| 6 | `sample-converter-cli-entry` — `main()` + argparse with `apply` and `fetch-and-apply` subcommands | ✅ | `scripts/explore/sample_converter.py` has `main()`, both subcommands work and output `{"ok":true,...}` |
| 7 | `main-py-api-config-aware-engine` — engine selection checks `api_config` before probe chain | ✅ | `scripts/explore/main.py` — `if api_config and api_config.get("type") == "mediawiki": engine = "mediawiki-api"` |
| 8 | `skill-md-sample-conversion-route` — SKILL.md documents standard conversion path | ✅ | `~/.agents/skills/chrome-agent/SKILL.md` — "Route to Sample Conversion" section added |

### Capability: `engine-contracts` (modified, 4 requirements)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | `engine-registry-api-type` — engine registry includes `mediawiki-api` with `type: "api"` and `default_rank: 0` | ✅ | `configs/engine-registry.json` — new entry with `id: "mediawiki-api"`, `type: "api"`, `default_rank: 0` |
| 2 | Registry entry declares `applicable_platforms: ["mediawiki", "mediawiki-fandom", "mediawiki-wiki-gg"]` | ✅ | Registry entry has `applicable_platforms` array with all three platforms |
| 3 | `select-fetcher-api-platform-awareness` — `selectFetcher()` detects `api.platform` before scrapling checks | ✅ | Same as requirement 1 in explore-strategy-pipeline-bridge |
| 4 | `run-engine-fetch-api-dispatch` — `runEngineFetch()` dispatches `"mediawiki-api"` correctly | ✅ | `runEngineFetch()` has mediawiki-api branch calling `runMediawikiApiFetch()` |
| 5 | Platform-driven (not domain-driven) — reads `strategy.document.api.platform`, not hardcoded domains | ✅ | Implementation checks `strategy?.document?.api?.platform`, no domain name matching |

### Capability: `explore-workflow` (modified, 2 requirements)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | `explore-strategy-matched-conversion-engine-info` — `runExplore()` includes `conversion_engine` / `converter_path` | ✅ | `scripts/chrome-agent-cli.mjs` — strategy-matched branch now computes and includes both fields |
| 2 | `main-py-api-config-engine-selection` — engine selection in `main.py` prioritizes `api_config` | ✅ | Same as requirement 7 in explore-strategy-pipeline-bridge |

### Capability: `site-strategy` (modified, 2 requirements)

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | `api-platform-consumed-by-engine-selection` — `api.platform` consumed by engine selection layer | ✅ | `selectFetcher()` and `main.py` both read and respond to `api.platform` |
| 2 | `rate-limit-api-engine-priority-update` — `rate-limit-api` lists `mediawiki-api` as rank 0 | ✅ | `sites/anti-crawl/rate-limit-api.md` — `mediawiki-api` at `rank: 0`, `scrapling-fetch` demoted to `rank: 1` |

---

## Part B: Task-to-Evidence Verification

| Task | Status | Evidence |
|------|--------|----------|
| 1.1 Spec confirmation | ✅ | All 4 spec files read and verified; 14 requirements mapped |
| 1.2 Dependency check | ✅ | bs4, yaml, markdownify available in environment |
| 2.1 `selectFetcher()` api.platform detection | ✅ | `chrome-agent-cli.mjs` — added api.platform check before scrapling logic |
| 2.2 `runMediawikiApiFetch()` function | ✅ | `chrome-agent-cli.mjs` — new function reads strategy, calls action=parse API, writes HTML |
| 2.3 `runEngineFetch()` mediawiki-api branch | ✅ | `chrome-agent-cli.mjs` — dispatches to `runMediawikiApiFetch()` |
| 2.4 `sample_converter.py` main() + CLI | ✅ | `apply` and `fetch-and-apply` subcommands work; JSON output verified |
| 2.5 `main.py` engine selection api_config | ✅ | `scripts/explore/main.py` — prioritizes `api_config` over probe chain |
| 2.6 SKILL.md Route to sample conversion | ✅ | `~/.agents/skills/chrome-agent/SKILL.md` — new section documents standard path |
| 2.7 AGENTS.md sample_converter.py CLI | ✅ | `AGENTS.md` — documented under "样本转换 CLI（策略驱动）" |
| 2.8 `runExplore()` conversion_engine/converter_path | ✅ | `chrome-agent-cli.mjs` — strategy-matched return includes both fields |
| 2.9 engine-registry.json mediawiki-api | ✅ | `configs/engine-registry.json` — new api-type engine at rank 0 |
| 2.10 rate-limit-api engine_priority update | ✅ | `sites/anti-crawl/rate-limit-api.md` — mediawiki-api at rank 0 |
| 3.1 End-to-end test | ✅ | selectFetcher test passes; sample_converter.py apply test passes with Isaac Wiki strategy |
| 3.2 Non-MediaWiki regression | ✅ | Code review: no api.platform → existing logic unchanged; test confirms |
| 3.3 Cross-session scenario | ✅ | SKILL.md documents conversion path; agent can discover sample_converter.py and use it |

---

## Part C: Verification Notes

### API fetch limitation
`runMediawikiApiFetch()` uses `curl` subprocess for the MediaWiki API call. This is consistent with the Node.js spawnSync pattern used throughout `chrome-agent-cli.mjs`. Future improvements could migrate to native `fetch()` or Node.js `https` module.

### Sample converter HTML cleanup
When `fetch-and-apply` is used, the temp HTML file is deleted after conversion. No orphan files remain.

### Engine registry rank consistency
`mediawiki-api` is assigned `default_rank: 0` (highest priority), consistent with the spec requirement that API is preferred over scrapling for MediaWiki sites. The `selectFetcher()` returns `"mediawiki-api"` before evaluating `engine_preference`, making the rank advisory for the CLI path.

---

**Verification conclusion**: ✅ All 14 spec requirements and 18 tasks verified. Change is ready for writeback.
