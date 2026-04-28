# Specification Delta

## Capability 对齐（已确认）

- Capability: `engine-contracts`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 对话中确认——engine-contracts 作为聚合索引 spec，引用所有 5 个独立引擎契约，提供引擎类型与使用场景的映射表，不做重复定义

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件
- 注意：各引擎的行为规范真源是各自的 `<engine-id>-contract/spec.md`；本文件是聚合索引，不做行为定义的替代

## ADDED Requirements

### Requirement: Engine contract registry

The system SHALL maintain a registry of all engine contracts, their types, usage scenarios, and status.

#### Scenario: Engine contract inventory

- **WHEN** the engine contracts registry is consulted
- **THEN** it SHALL list the following 5 engine contracts with their corresponding spec references:

| Engine | Contract Spec | Type | Primary Scenario |
|--------|-------------|------|-----------------|
| Scrapling get | `scrapling-get-contract` | HTTP (impersonate) | 静态页面、低保护、文章提取 |
| Scrapling fetch | `scrapling-fetch-contract` | Playwright | SPA、动态页面、JS 渲染 |
| Scrapling stealthy-fetch | `scrapling-stealthy-fetch-contract` | Playwright + stealth | Cloudflare、WAF、高保护 |
| chrome-devtools-mcp | `chrome-devtools-mcp-contract` | CDP (managed) | 诊断证据（DOM/网络/性能/截图） |
| chrome-cdp | `chrome-cdp-contract` | CDP (live-session) | 实时会话延续、认证页面 |

#### Scenario: Engine contract status

- **WHEN** the registry is checked
- **THEN** all engine contracts SHALL be marked with status `frozen` after Phase 2 completion
- **AND** status values SHALL be: `draft`, `frozen`, `superseded`

### Requirement: Engine selection mapping

The system SHALL define the routing logic for engine selection based on page type, protection level, and evidence need.

#### Scenario: Scrapling-first rule

- **WHEN** a webpage grabbing task is initiated
- **THEN** the engine selection SHALL start with Scrapling (get/fetch/stealthy-fetch) by default
- **AND** the selection SHALL escalate to chrome-devtools-mcp or chrome-cdp only when defined fallback triggers are present

#### Scenario: Page type to engine mapping

- **WHEN** routing an engine for a given page type
- **THEN** the following mapping SHALL be used:

| Page Type | Primary Engine | Fallback Engine |
|-----------|---------------|-----------------|
| Static / low protection | scrapling-get | scrapling-fetch (if JS needed) |
| SPA / dynamic | scrapling-fetch | scrapling-stealthy-fetch (if blocked) |
| Protected / WAF | scrapling-stealthy-fetch | chrome-devtools-mcp (diagnosis) |
| Auth-only (approved) | scrapling-fetch (session reuse) | chrome-cdp (live tab) |
| Diagnostic needed | chrome-devtools-mcp | chrome-cdp (if live session needed) |

#### Scenario: Fallback boundaries

- **WHEN** a Scrapling engine fails
- **THEN** the fallback SHALL be selected by diagnostic-evidence needs (→ chrome-devtools-mcp) versus live-tab continuity needs (→ chrome-cdp)
- **AND** fallback switching SHALL NOT happen solely because both tools are technically capable

### Requirement: Cross-engine error contract consistency

The system SHALL ensure consistent error categories and recommendations across all engine contracts.

#### Scenario: Shared error categories

- **WHEN** error contracts are compared across engines
- **THEN** the following error categories SHALL be used consistently (each engine adds engine-specific categories as needed):

| Category | get | fetch | stealthy-fetch | chrome-devtools-mcp | chrome-cdp |
|----------|-----|-------|----------------|---------------------|------------|
| network | ✓ | ✓ | ✓ | — | — |
| timeout | ✓ | ✓ | ✓ | — | — |
| block | ✓ | ✓ | ✓ | — | — |
| parse | ✓ | ✓ | ✓ | — | — |
| browser | — | ✓ | ✓ | — | — |
| challenge | — | — | ✓ | — | — |
| connection | — | — | — | ✓ | ✓ |
| navigation | — | — | — | ✓ | — |
| selector | — | — | — | ✓ | — |
| evaluation | — | — | — | ✓ | — |
| auth_redirect | — | — | — | — | ✓ |
| session_loss | — | — | — | — | ✓ |
| rate_limit | — | — | — | — | ✓ |
| permissions | — | — | — | — | ✓ |

#### Scenario: Escalation chain

- **WHEN** an engine fails and escalation is recommended
- **THEN** the escalation SHALL follow the chain: `get → fetch → stealthy-fetch → chrome-devtools-mcp` for protection-level escalation
- **AND** the live-session path SHALL follow: `get/fetch/stealthy-fetch (session reuse fail) → chrome-cdp`

### Requirement: Contract compliance

The system SHALL define the compliance criteria that each engine contract must meet.

#### Scenario: Compliance criteria

- **WHEN** an engine contract is validated
- **THEN** it SHALL contain all three dimensions (input, output, error) as defined in `capability-contracts` metamodel
- **AND** each dimension SHALL use `### Requirement:` blocks with SHALL/MUST language
- **AND** each requirement SHALL have at least one `#### Scenario:` block
- **AND** the contract SHALL include a smoke-check scenario with a known target URL
- **AND** the contract SHALL include a version identifier (e.g., `version: 1.0.0`)

#### Scenario: Compliance status

- **WHEN** Phase 2 is complete
- **THEN** all 5 engine contracts SHALL meet the compliance criteria
- **AND** the compliance status SHALL be recorded in this registry spec

### Requirement: Smoke-check aggregate

The system SHALL provide a consolidated view of smoke-check scenarios across all engine contracts.

#### Scenario: Smoke-check inventory

- **WHEN** the smoke-check inventory is consulted
- **THEN** it SHALL list each engine's smoke-check target and expected outcome:

| Engine | Smoke-check Target | Expected Outcome |
|--------|-------------------|-----------------|
| get | mp.weixin.qq.com/s/... | 文章标题 + DOM 顺序正文 + 内联图片 URL 保留 |
| fetch | x.com/<user>/status/<id> | SPA 渲染推文内容 + 作者 + 媒体链接 |
| stealthy-fetch | wiki.supercombo.gg/w/... | CF 挑战突破 + 文章内容（非挑战壳） |
| chrome-devtools-mcp | x.com/hashtag/... | 诊断证据：title/URL + snapshot + network（登录门检测） |
| chrome-cdp | fanbox.cc/@.../posts | 认证页面 visit + 帖子列表内容 + 无 auth redirect |

#### Scenario: Phase 3 dependency

- **WHEN** Phase 3 (策略库标准化) begins
- **THEN** it SHALL reference this engine contract registry for field types and error codes
- **AND** the per-engine contracts SHALL serve as the normative reference for engine behavior in strategy schema design
