# Explore Domain: Deep Discovery — Merged Spec

> **Merged from**: `explore-workflow`, `explore-backend-detection`, `explore`
> **Purpose**: Defines the full deep discovery pipeline triggered when `explore` encounters a URL with no matching strategy. Covers engine chain probing, API discovery, structure mapping, protection identification, interactive user confirmation, and the transition from strategy-gap to strategy-creation workflow.

---

## Part 1 — Source: `explore-workflow`

### Requirement: deep-discovery

The system SHALL, when `explore` is executed against a URL not covered by an existing strategy, automatically execute a deep discovery pipeline before reporting a strategy gap.

#### Scenario: chain-engine-probe
- **WHEN** `explore` starts with no matching strategy
- **THEN** the system SHALL attempt engine chain: `scrapling-get` → `obscura-fetch` → `cloakbrowser-fetch` → `chrome-devtools-mcp`
- **THEN** the system SHALL record for each engine: `status` (success/failure/partial), `http_status` or `error_type`, `page_title`, `content_length`

#### Scenario: api-discovery
- **WHEN** any engine in the chain succeeds
- **THEN** the system SHALL probe for known API endpoints: `/api.php` (MediaWiki), `/wp-json` (WordPress), `/graphql` (GraphQL), `/sitemap.xml`, `/robots.txt`
- **THEN** the system SHALL record for each detected API: `type`, `base_url`, `version`, `capabilities`

#### Scenario: structure-mapping
- **WHEN** page content is successfully retrieved
- **THEN** the system SHALL extract the page type (home/list/article/gallery) based on DOM features
- **THEN** the system SHALL identify nav structure and extract top-level section labels (≤10 items)
- **THEN** the system SHALL NOT extract the complete internal link topology
- **THEN** the system SHALL detect content structure: presence of tables, infoboxes, list/card patterns

#### Scenario: protection-identification
- **WHEN** the engine chain produces failures or partial results
- **THEN** the system SHALL identify the protection mechanism (cloudflare-turnstile / cloudflare-managed / login-wall / rate-limit / none)
- **THEN** the system SHALL record the detection basis (HTTP status, DOM markers, error message)

### Requirement: user-interactive-confirmation

The system SHALL, after deep discovery, interact with the user via ask_user to confirm crawl scope before generating samples.

#### Scenario: scope-selection
- **WHEN** deep discovery has identified the site's content sections
- **THEN** the system SHALL present the detected sections and ask the user to select: "all" / "specific sections" / "to be specified"
- **THEN** the system SHALL ask the user to select page granularity: "summary + individual" / "individual only" / "summary only"
- **THEN** the system SHALL note if certain sections have only summary pages (no individual entity pages)

#### Scenario: sample-selection
- **WHEN** the scope is confirmed
- **THEN** the system SHALL recommend 4-8 sample pages covering each content type selected
- **THEN** the system SHALL prioritize: most content-rich pages, edge cases (with/without infobox)
- **THEN** the system SHALL present the sample list to the user for confirmation before proceeding

### Requirement: pipeline-dependency-preflight

The deep discovery pipeline (`scripts/explore/main.py`) SHALL verify all required Python dependencies at startup and exit with a clear error message if any are missing.

#### Scenario: main-py-dependency-self-check
- **WHEN** `python3 scripts/explore/main.py` is invoked
- **THEN** the script SHALL attempt to import `bs4`, `yaml`, and `selectolax` before executing any pipeline phase
- **THEN** if any import fails, the script SHALL print to stderr: `FATAL: Missing dependencies: <package-list>`
- **THEN** the script SHALL print to stderr: `Install with: pip3 install -r scripts/explore/requirements.txt`
- **THEN** the script SHALL exit with code 1

### Requirement: explore-strategy-matched-conversion-engine-info

When `runExplore()` in `chrome-agent-cli.mjs` matches an existing strategy, the result SHALL include `conversion_engine` and `converter_path` fields to guide the agent toward the correct sample conversion path.

#### Scenario: strategy-matched-output-extended
- **WHEN** `runExplore()` finds a matching strategy
- **AND** the strategy has `api.platform: "mediawiki"`
- **THEN** the result SHALL include `conversion_engine: "mediawiki-api"`
- **THEN** the result SHALL include `converter_path: "scripts/explore/sample_converter.py fetch-and-apply"`

#### Scenario: non-api-strategy-no-change
- **WHEN** `runExplore()` finds a matching strategy without an API platform
- **THEN** the result SHALL include `conversion_engine: "<recommendedFetcher>"`
- **THEN** `converter_path` SHALL be absent or indicate scrapling-based conversion

### Requirement: main-py-api-config-engine-selection

The engine selection in `scripts/explore/main.py` SHALL prioritize the API discovery result (`api_config`) over the probe chain's first successful engine.

#### Scenario: api-discovered-prioritized
- **WHEN** `main.py` Phase 6 selects the sample conversion engine
- **AND** `api_config` is not None and `api_config.get("type") == "mediawiki"`
- **THEN** the engine SHALL be `"mediawiki-api"`
- **THEN** the probe chain engine SHALL NOT be used

#### Scenario: no-api-preserves-existing-logic
- **WHEN** `api_config` is None or not a known API type
- **THEN** the existing logic: `protection.get("engine_override") or probe_result.get("success_engine") or "scrapling-get"` SHALL apply

---

## Part 2 — Source: `explore-backend-detection`

### Requirement: 后端检测触发条件

The system SHALL trigger backend detection in `explore` only when no matching site strategy exists for the target URL.

#### Scenario: 已有策略时跳过检测
- **WHEN** the target domain matches an existing strategy in `sites/strategies/registry.json`
- **THEN** `explore` SHALL skip backend detection and use the existing strategy for its report

#### Scenario: 无策略时触发检测
- **WHEN** no matching strategy exists for the target domain
- **THEN** `explore` SHALL attempt backend detection after Scrapling preflight
- **AND** it SHALL fetch a raw HTML sample from the target URL using `scrapling-get`

### Requirement: 后端指纹检测规则

The system SHALL detect backends by matching fetched HTML against structured signatures defined in `configs/backend-signatures.json`.

Each backend signature SHALL contain at least one of: `meta_generator`, `dom_selector`, `url_patterns`.

#### Scenario: 单一检测方法命中
- **WHEN** a fetched HTML page contains the `meta_generator` substring declared in a backend signature
- **THEN** the backend SHALL be considered detected

#### Scenario: 多检测方法联合命中
- **WHEN** a backend signature declares multiple detection methods
- **THEN** ALL declared methods MUST match for the backend to be considered detected

#### Scenario: 检测未命中
- **WHEN** no backend signature matches the fetched HTML
- **THEN** `explore` SHALL fall back to the existing "strategy gap" report behavior

### Requirement: 可复用策略推荐

When a backend is detected, the system SHALL search `sites/strategies/registry.json` for existing strategies that share the same backend family and recommend them to the caller.

#### Scenario: 检测到已知后端并找到可复用策略
- **WHEN** a backend is detected and its signature includes `reusable_strategies` listing one or more domain names
- **THEN** `explore` SHALL list those domains as reusable strategy candidates

#### Scenario: 检测到后端但无已注册可复用策略
- **WHEN** a backend is detected but no strategies in `registry.json` are registered for that backend family
- **THEN** `explore` SHALL report the detected backend without reusable strategy recommendations

### Requirement: 检测安全性与隔离

Backend detection SHALL be performed in a safe, isolated manner that does not interfere with existing workflows.

#### Scenario: 检测不影响现有策略匹配
- **WHEN** a target URL has an exact domain match in `registry.json`
- **THEN** backend detection SHALL NOT run

#### Scenario: 检测失败不影响 explore 可用性
- **WHEN** the raw HTML fetch fails during backend detection
- **THEN** `explore` SHALL fall back to the existing strategy-gap behavior

---

## Part 3 — Source: `explore`

### Requirement: explore-command-backend

The system SHALL route `explore` into the full deep-discovery workflow when no strategy exists, while retaining the existing behavior when a strategy IS matched.

Deep discovery SHALL be the only path for strategy-gap scenarios. The legacy backend-detection fallback (HTML fetch → DOM fingerprint → bootstrap recommendation) SHALL NOT be invoked.

#### Scenario: strategy-matched
- **WHEN** `explore <url>` is called and a strategy exists in the registry for the domain
- **THEN** the system SHALL continue with the existing behavior (load strategy, return structured report)

#### Scenario: strategy-gap
- **WHEN** `explore <url>` is called and no strategy exists for the domain
- **THEN** the system SHALL NOT simply return "strategy gap"
- **THEN** the system SHALL enter the deep discovery pipeline
- **THEN** the system SHALL proceed through: preflight → probe chain → API discovery → structure mapping → protection identification
- **THEN** the system SHALL engage interactive scope confirmation with the user
- **THEN** the system SHALL generate strategy scaffold
- **THEN** the system SHALL produce and self-check samples
- **THEN** on approval, the system SHALL freeze the strategy

### Requirement: explore-output-format

#### Scenario: output-format-extended
- **WHEN** deep discovery is complete
- **THEN** the output SHALL include standard fields plus:
  - `discovery.engine_chain[]`
  - `discovery.api`
  - `discovery.content_profile`
  - `discovery.protection`
  - `discovery.scale`
  - `scaffold.path`
  - `samples[]`
  - `self_check.summary`

### Requirement: explore-preflight-failure

#### Scenario: python-deps-missing
- **WHEN** `runExplore()` checks Python dependencies and one or more are not importable
- **THEN** the system SHALL return `result: "failure"` with `summary` containing the missing package names

#### Scenario: deep-discovery-execution-failure
- **WHEN** `scripts/explore/main.py` returns non-zero exit code
- **THEN** the system SHALL return `result: "failure"` with `summary` containing the first 500 characters of stderr

### Requirement: explore-legacy-fallback-removal

#### Scenario: no-legacy-fallback
- **WHEN** deep discovery is unavailable or fails
- **THEN** `runExplore()` SHALL NOT attempt to fetch HTML via `runEngineFetch` or invoke `detectBackend`
- **THEN** all code related to legacy fallback SHALL be removed from `runExplore()`
