# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-workflow`
- 来源: `proposal.md` → Modified Capabilities
- 变更类型: modified
- 用户确认摘要: 2026-10-02 用户回复“能力确认”，确认 Explore 入口修复和交接命名修复。

## 规范真源声明

- 本文件为本次 change 的行为规范真源；design / tasks / verification 必须引用本文件。
- 项目页面回写不得替代本文件。

## MODIFIED Requirements

### Requirement: deep-discovery

The system SHALL, when `explore` is executed against a URL not covered by an existing strategy, automatically execute a deep discovery pipeline before reporting a strategy gap.

Deep discovery startup SHALL make repository-local packages and sibling Explore modules importable before importing pipeline modules, without requiring caller-provided PYTHONPATH or a particular working directory. The existing application-layer interpreter resolution and discovery/confirmation gates SHALL remain in effect.

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

#### Scenario: direct-entry-without-pythonpath
- **WHEN** application dependencies are available and the real `scripts/explore/main.py --help` entry is launched as a child process with PYTHONPATH removed
- **AND** its cwd is either the repository root or an unrelated temporary directory
- **THEN** it SHALL exit 0 and display the Deep discovery CLI help
- **AND** it SHALL NOT emit `ModuleNotFoundError: No module named 'scripts'`
- **AND** it SHALL NOT fetch pages, create a scaffold, or start extraction.

#### Scenario: strategy-gap-cli-startup
- **WHEN** the real CLI routes a strategy-gap Explore request to the real main.py entry with application dependencies available and PYTHONPATH absent
- **THEN** repository-local imports SHALL succeed before probe-chain execution
- **AND** subsequent probe success or failure SHALL be reported through the existing Explore result/handoff contract.

## 冻结规范合并定位

现有完整 requirement 位于 `openspec/specs/explore/explore-deep-discovery.md` Part 1；归档时在该位置替换完整块，不在其它文件复制同名要求。`openspec/specs/explore-workflow/spec.md` 保留其 capability gate 要求。
