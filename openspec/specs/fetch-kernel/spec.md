# Specification

## Capability 对齐

- Capability: `fetch-kernel`
- 来源: `openspec/changes/unify-extract-fetch-kernels/proposal.md`
- 变更类型: modified
- 摘要: .mjs 与 pipeline 的 MediaWiki API fetch 重复实现 → 统一到 pipeline `ApiClient`

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件

## Requirements

### Requirement: fetch-via-pipeline-kernel

All MediaWiki API fetch operations SHALL route through `scripts/pipeline/pipeline/phases/fetch.py`'s `ApiClient` as the single kernel implementation. The `.mjs` Node.js layer SHALL delegate to this kernel via Python subprocess, not implement its own API client.

#### Scenario: mjs-fetch-delegates-to-pipeline
- **WHEN** `chrome-agent-cli.mjs` is invoked with a MediaWiki URL
- **THEN** the fetch SHALL delegate to `scripts.pipeline.client.ApiClient` via Python subprocess
- **AND** SHALL NOT implement its own MediaWiki API client (curl / standalone.py)

#### Scenario: pipeline-fetch-unchanged
- **WHEN** pipeline orchestrator runs Phase Fetch
- **THEN** the existing `run_fetch()` function SHALL be used unchanged
- **AND** batch fetch, cache, retry, and rate limiting SHALL work as before

#### Scenario: fetch-output-format-compatible
- **WHEN** `.mjs` receives raw HTML from the unified fetch kernel
- **THEN** the output format SHALL be compatible with the downstream `.mjs` conversion pipeline
- **AND** no change to the `.mjs` convert/discover/assemble code SHALL be required beyond the fetch invocation point
