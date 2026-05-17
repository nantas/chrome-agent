# Specification Delta

## Capability 对齐（已确认）

- Capability: `engine-contracts`
- 来源: `phase-2-contract-freeze` + `phase-4-engine-extension-governance`
- 变更类型: modified
- 用户确认摘要: `engine-contracts` 继续作为聚合索引 spec，具体引擎清单迁移到 `configs/engine-registry.json`，本 spec 保留 cross-engine concerns

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 注意：各引擎的行为规范真源是各自的 `<engine-id>-contract/spec.md`；本文件是聚合索引，不做行为定义的替代

## Requirements

### Requirement: Engine contract registry

The system SHALL maintain a registry of all engine contracts, their types, usage scenarios, and status.

The registry SHALL be stored at `configs/engine-registry.json` as defined by the `engine-registry` capability spec.

This spec SHALL reference the external registry rather than inlining individual engine entries.

#### Scenario: Engine contract inventory

- **WHEN** the engine contracts registry is consulted
- **THEN** it SHALL defer to `configs/engine-registry.json` for the list of engines, their types, and usage scenarios
- **AND** the registry SHALL be maintained according to the `engine-registry` spec

#### Scenario: Engine contract status

- **WHEN** the registry is checked
- **THEN** engine contract statuses SHALL be stored in `configs/engine-registry.json` as defined by `engine-registry`
- **AND** status values SHALL be: `draft`, `frozen`, `superseded`

### Requirement: Engine selection mapping

The system SHALL define the routing logic for engine selection based on page type, protection level, and evidence need.

Engine selection SHALL use the following priority sources in order:

1. Site strategy `engine_preference` (if present)
2. Anti-crawl strategy `engine_priority` (if matching protection detected)
3. Engine `default_rank` from `configs/engine-registry.json`

#### Scenario: Scrapling-first rule with cdp_lightweight

- **WHEN** a webpage grabbing task is initiated
- **THEN** the engine selection SHALL start with the Scrapling engine family (engines with type `http`, `cdp_lightweight`, `playwright*` in the registry) by default
- **AND** `cdp_lightweight` engines SHALL be considered part of the first-escalation tier between HTTP and full Playwright engines
- **AND** the selection SHALL escalate to full CDP engines (`cdp_managed`, `cdp_live`) only when lighter options are exhausted or defined fallback triggers are present

#### Scenario: Page type to engine mapping

- **WHEN** routing an engine for a given page type in the absence of strategy overrides
- **THEN** the engine with the lowest `default_rank` that `best_for` includes that page type SHALL be selected
- **AND** if no engine explicitly `best_for` covers the page type, `default_rank` order SHALL be used as the fallback escalation chain
- **AND** for `dynamic_content` and `dynamic_list` page types, `obscura-fetch` (cdp_lightweight) SHALL be tried before `scrapling-fetch` (playwright) when both are available

#### Scenario: Fallback boundaries

- **WHEN** an engine fails to produce acceptable content
- **THEN** the fallback SHALL advance to the next engine in `default_rank` order
- **AND** escalation SHALL respect the Scrapling-first principle (all Scrapling engines before CDP engines)
- **AND** fallback switching SHALL NOT happen solely because multiple tools are technically capable

### Requirement: Cross-engine error contract consistency

The system SHALL ensure consistent error categories and recommendations across all engine contracts.

#### Scenario: Shared error categories

- **WHEN** error contracts are compared across engines
- **THEN** the following error categories SHALL be used consistently (each engine adds engine-specific categories as needed):

| Category | scrapling-get | obscura-fetch | scrapling-fetch | cloakbrowser-fetch | scrapling-bulk-fetch | chrome-devtools-mcp | chrome-cdp |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| network | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| timeout | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| block | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| parse | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| browser | — | ✓ | ✓ | ✓ | ✓ | — | — |
| challenge | — | — | — | ✓ | — | — | — |
| binary | — | — | — | ✓ | — | — | — |
| license | — | — | — | ✓ | — | — | — |
| connection | — | — | — | — | — | ✓ | ✓ |
| navigation | — | — | — | — | — | ✓ | — |
| selector | — | — | — | — | — | ✓ | — |
| evaluation | — | — | — | — | — | ✓ | — |
| auth_redirect | — | — | — | — | — | — | ✓ |
| session_loss | — | — | — | — | — | — | ✓ |
| rate_limit | — | — | — | — | — | — | ✓ |
| permissions | — | — | — | — | — | — | ✓ |

Note: `scrapling-stealthy-fetch` (superseded) retains its error categories for historical reference but is removed from the primary comparison table.

#### Scenario: Escalation chain

- **WHEN** an engine fails and escalation is recommended
- **THEN** the standard escalation chain SHALL follow: `scrapling-get → obscura-fetch → scrapling-fetch → cloakbrowser-fetch → chrome-devtools-mcp` for protection-level escalation
- **AND** `cloakbrowser-fetch` SHALL be tried after `scrapling-fetch` and before `chrome-devtools-mcp` for high-protection pages requiring stealth (TLS fingerprint evasion, Turnstile, reCAPTCHA)
- **AND** `obscura-fetch` SHALL be tried after `scrapling-get` fails (e.g., JS rendering required) and before `scrapling-fetch` (e.g., full browser needed)
- **AND** the bulk escalation chain SHALL follow: `scrapling-bulk-fetch → scrapling-bulk-stealthy-fetch` for batch operations
- **AND** the live-session path SHALL follow: `scrapling-fetch/cloakbrowser-fetch (session reuse fail) → chrome-cdp`

### Requirement: Contract compliance

The system SHALL define the compliance criteria that each engine contract must meet.

#### Scenario: Compliance criteria

- **WHEN** an engine contract is validated
- **THEN** it SHALL contain all three dimensions (input, output, error) as defined in `capability-contracts` metamodel
- **AND** each dimension SHALL use `### Requirement:` blocks with SHALL/MUST language
- **AND** each requirement SHALL have at least one `#### Scenario:` block
- **AND** the contract SHALL include a smoke-check scenario with a known target URL
- **AND** the contract SHALL include a version identifier (e.g., `version: 1.0.0`)

### Requirement: Smoke-check aggregate

The system SHALL provide a consolidated view of smoke-check scenarios across all engine contracts.

#### Scenario: Smoke-check inventory

- **WHEN** the smoke-check inventory is consulted
- **THEN** it SHALL reference each engine's smoke-check scenario from its individual contract spec
- **AND** the inventory SHALL list each engine's smoke-check target and expected outcome:

| Engine | Smoke-check Target | Expected Outcome |
|--------|-------------------|-----------------|
| scrapling-get | mp.weixin.qq.com/s/... | 文章标题 + DOM 顺序正文 + 内联图片 URL 保留 |
| obscura-fetch | news.ycombinator.com | 页面标题 "Hacker News" + ≥20 story entries + HTTP 200 + timing ≤ 5000ms |
| scrapling-fetch | x.com/<user>/status/<id> | SPA 渲染推文内容 + 作者 + 媒体链接 |
| cloakbrowser-fetch | wiki.supercombo.gg/w/... | CF Turnstile 自动解析 + 文章内容（20,000+ chars），非挑战壳 |
| | scrapingbee.com/blog/ | TLS 指纹绕过 + 全量内容（140+ links），非空 body |
| scrapling-bulk-fetch | [example.com, httpbin.org/get] | 双 URL 成功，status 200 × 2，正确内容 |
| chrome-devtools-mcp | x.com/hashtag/... | 诊断证据：title/URL + snapshot + network（登录门检测） |
| chrome-cdp | fanbox.cc/@.../posts | 认证页面 visit + 帖子列表内容 + 无 auth redirect |

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
