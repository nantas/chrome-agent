# Specification Delta

## Capability 对齐（已确认）

- Capability: `fetch-kernel`
- 来源: `proposal.md` — Modified Capability
- 变更类型: `modified`
- 用户确认摘要: Stage 3 drift 4：.mjs 与 pipeline 的 MediaWiki API fetch 重复实现 → 统一到 pipeline fetch.py

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件

## REMOVED Requirements

### Requirement: mjs-mediawiki-api-fetch

**Reason**: `chrome-agent-cli.mjs` `runMediawikiApiFetch()` spawns `scripts/pipeline/standalone.py` to call MediaWiki API for a single page. Pipeline `fetch.py` already provides batch fetch with caching, retry, and rate limiting. Two code paths for the same operation violates B-axis mirror principle.

**Migration**: `.mjs` paths that need MediaWiki API page content SHALL spawn `python3 -m scripts.pipeline fetch` (or import shared fetch module) instead of `runMediawikiApiFetch()`. The `standalone.py` module SHALL remain as-is (it serves other non-fetch purposes like reconvert).

## MODIFIED Requirements

### Requirement: fetch-via-pipeline-kernel

All MediaWiki API fetch operations SHALL route through `scripts/pipeline/pipeline/phases/fetch.py` as the single kernel implementation. The `.mjs` Node.js layer SHALL delegate to this kernel via `python3 -m scripts.pipeline` subprocess, not implement its own API client.

#### Scenario: mjs-fetch-delegates-to-pipeline
- **WHEN** `chrome-agent-cli.mjs` is invoked with a MediaWiki URL
- **THEN** the fetch SHALL use `python3 -m scripts.pipeline fetch` (or equivalent shared import)
- **AND** SHALL NOT call `standalone.py` directly for page fetching

#### Scenario: pipeline-fetch-unchanged
- **WHEN** pipeline orchestrator runs Phase Fetch
- **THEN** the existing `run_fetch()` function SHALL be used unchanged
- **AND** batch fetch, cache, retry, and rate limiting SHALL work as before

#### Scenario: fetch-output-format-compatible
- **WHEN** `.mjs` receives raw HTML from the unified fetch kernel
- **THEN** the output format SHALL be compatible with the downstream `.mjs` conversion pipeline
- **AND** no change to the `.mjs` convert/discover/assemble code SHALL be required beyond the fetch invocation point
