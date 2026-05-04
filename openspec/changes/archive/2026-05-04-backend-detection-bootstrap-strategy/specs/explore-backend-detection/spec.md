# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore-backend-detection`
- 来源: `proposal.md` — New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户已通过对话确认，选择 A+C 组合方案：explore 在无匹配策略时自动检测后端类型并推荐可复用策略

## 规范真源声明

- 本文件是 `explore-backend-detection` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: 后端检测触发条件

The system SHALL trigger backend detection in `explore` only when no matching site strategy exists for the target URL.

#### Scenario: 已有策略时跳过检测

- **WHEN** the target domain matches an existing strategy in `sites/strategies/registry.json`
- **THEN** `explore` SHALL skip backend detection and use the existing strategy for its report
- **AND** the behavior SHALL remain identical to the pre-change `explore` implementation

#### Scenario: 无策略时触发检测

- **WHEN** no matching strategy exists for the target domain
- **THEN** `explore` SHALL attempt backend detection after Scrapling preflight
- **AND** it SHALL fetch a raw HTML sample from the target URL using `scrapling-get`

### Requirement: 后端指纹检测规则

The system SHALL detect backends by matching fetched HTML against structured signatures defined in `configs/backend-signatures.json`.

Each backend signature SHALL contain at least one of the following detection methods:
- `meta_generator`: a substring match against `<meta name="generator" content="...">`
- `dom_selector`: a CSS selector that MUST be present in the DOM
- `url_patterns`: an array of URL path substrings that MUST match the target URL pathname

#### Scenario: 单一检测方法命中

- **WHEN** a fetched HTML page contains the `meta_generator` substring declared in a backend signature
- **THEN** the backend SHALL be considered detected
- **AND** `explore` SHALL report the detected backend in its output

#### Scenario: 多检测方法联合命中

- **WHEN** a backend signature declares multiple detection methods
- **THEN** ALL declared methods MUST match for the backend to be considered detected
- **AND** partial matches SHALL NOT trigger a false positive

#### Scenario: 检测未命中

- **WHEN** no backend signature matches the fetched HTML
- **THEN** `explore` SHALL fall back to the existing "strategy gap" report behavior
- **AND** the output SHALL NOT claim any backend detection result

### Requirement: 可复用策略推荐

When a backend is detected, the system SHALL search `sites/strategies/registry.json` for existing strategies that share the same backend family and recommend them to the caller.

#### Scenario: 检测到已知后端并找到可复用策略

- **WHEN** a backend is detected and its signature includes `reusable_strategies` listing one or more domain names
- **THEN** `explore` SHALL list those domains as reusable strategy candidates
- **AND** the `next_action` field SHALL include a concrete `bootstrap-strategy` command using one of the reusable strategies as `--from`

#### Scenario: 检测到后端但无已注册可复用策略

- **WHEN** a backend is detected but no strategies in `registry.json` are registered for that backend family
- **THEN** `explore` SHALL report the detected backend without reusable strategy recommendations
- **AND** `next_action` SHALL direct the caller to manually create a strategy

### Requirement: 检测安全性与隔离

Backend detection SHALL be performed in a safe, isolated manner that does not interfere with existing workflows or produce false confidence.

#### Scenario: 检测不影响现有策略匹配

- **WHEN** a target URL has an exact domain match in `registry.json`
- **THEN** backend detection SHALL NOT run
- **AND** the matched strategy SHALL be used regardless of whether the page content actually matches the backend signature

#### Scenario: 检测失败不影响 explore 可用性

- **WHEN** the raw HTML fetch fails (network error, timeout, blocked) during backend detection
- **THEN** `explore` SHALL fall back to the existing strategy-gap behavior
- **AND** the failure SHALL be reported in the preflight status without marking the overall explore as failure
