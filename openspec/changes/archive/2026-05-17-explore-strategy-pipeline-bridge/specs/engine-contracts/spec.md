# Specification Delta

## Capability 对齐（已确认）

- Capability: `engine-contracts`
- 来源: `proposal.md`
- 变更类型: `modified`
- 用户确认摘要: 引擎注册表新增 `mediawiki-api` 引擎类型；`selectFetcher()` 新增 API 平台感知分支

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: engine-registry-api-type

The engine registry (`configs/engine-registry.json`) SHALL include a `mediawiki-api` engine entry with type `"api"` and default rank `0` (highest priority, below only explicit overrides).

#### Scenario: registry-contains-api-engine
- **WHEN** the engine registry is loaded
- **THEN** an entry with `id: "mediawiki-api"` SHALL exist
- **THEN** the entry SHALL have `type: "api"` and `status: "frozen"`
- **THEN** the entry SHALL declare `applicable_platforms: ["mediawiki", "mediawiki-fandom", "mediawiki-wiki-gg"]`

### Requirement: select-fetcher-api-platform-awareness

`selectFetcher()` in `chrome-agent-cli.mjs` SHALL detect the strategy's `api.platform` and return `"mediawiki-api"` for MediaWiki platforms before evaluating scrapling-based engine selection.

#### Scenario: mediawiki-platform-detected
- **WHEN** `selectFetcher(strategy, page)` is called
- **AND** `strategy?.document?.api?.platform` matches `"mediawiki"` or `"mediawiki-fandom"`
- **THEN** the function SHALL return `"mediawiki-api"` immediately
- **THEN** no further engine preference, protection, or anti-crawl check SHALL be evaluated

#### Scenario: non-mediawiki-platform-unchanged
- **WHEN** `strategy?.document?.api` is absent or its platform is not a recognized API type
- **THEN** the existing engine selection logic SHALL apply unchanged

### Requirement: run-engine-fetch-api-dispatch

`runEngineFetch()` in `chrome-agent-cli.mjs` SHALL dispatch `"mediawiki-api"` fetcher requests to a new `runMediawikiApiFetch()` function.

#### Scenario: api-fetcher-is-handled
- **WHEN** `runEngineFetch(repoRoot, "mediawiki-api", targetUrl, outputPath, extraArgs)` is called
- **THEN** `runMediawikiApiFetch(repoRoot, targetUrl, outputPath, extraArgs)` SHALL be invoked
- **THEN** no scrapling preflight or CloakBrowser check SHALL execute

### Requirement: engine-registry-selectFetcher-integration

The `selectFetcher()` function SHALL derive its API platform detection from the strategy document's `api.platform` field, NOT from a hardcoded list of domain names or URL patterns.

#### Scenario: platform-driven-not-domain-driven
- **WHEN** `selectFetcher()` evaluates a strategy
- **THEN** it SHALL read `strategy.document.api.platform`
- **THEN** it SHALL NOT hardcode domain names like `"bindingofisaacrebirth.wiki.gg"`
- **THEN** it SHALL NOT use URL pattern matching to determine API capability
