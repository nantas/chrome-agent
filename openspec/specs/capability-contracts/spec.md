# Specification Delta

## Capability 对齐（已确认）

- Capability: `capability-contracts`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 对话中确认——Phase 1 只建立契约元模型（通用 schema 框架），不填充具体引擎契约值。采用混合命名方式：capability-contracts 定义通用框架，具体引擎契约在 `openspec/specs/<engine-id>-contract/` 下独立定义

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: 契约元模型结构

The system SHALL define a universal contract metamodel that all engine-specific contracts MUST follow.

Each engine contract SHALL define three dimensions:

1. **Input Contract**: 引擎接受的输入参数——URL 格式要求、session 模式、超时配置、可选的 CSS selector/headers/cookies/proxy 等
2. **Output Contract**: 引擎在成功时产出的输出——extraction format (markdown/text/html)、content structure、metadata fields (title, final URL, timestamp)
3. **Error Contract**: 引擎在异常时的错误模型——error categories (network, timeout, block, auth, parse)、error response structure、recommended next action per error type

#### Scenario: Contract dimension completeness

- **WHEN** an engine contract is defined under openspec/specs/<engine-id>-contract/spec.md
- **THEN** it SHALL contain all three dimensions (input, output, error) with non-empty requirement blocks
- **AND** missing any dimension SHALL be treated as an incomplete contract

#### Scenario: Contract validation

- **WHEN** a contract is validated against this metamodel
- **THEN** each dimension SHALL use `### Requirement:` blocks with SHALL/MUST language
- **AND** each requirement SHALL have at least one `#### Scenario:` block

### Requirement: 契约命名与存放规则

The system SHALL define the naming and storage conventions for capability contracts.

#### Scenario: Contract file location

- **WHEN** an engine contract is created
- **THEN** it SHALL be stored at `openspec/specs/<engine-id>-contract/spec.md`
- **AND** <engine-id> SHALL use kebab-case matching the engine's identifier (e.g., `scrapling-get-contract`, `scrapling-fetch-contract`, `scrapling-stealthy-fetch-contract`, `chrome-devtools-mcp-contract`, `chrome-cdp-contract`)

#### Scenario: Contract metamodel location

- **WHEN** the contract metamodel itself is referenced
- **THEN** it SHALL be located at `openspec/specs/capability-contracts/spec.md`
- **AND** this file SHALL serve as the normative reference for all engine contracts

#### Scenario: Contract identifier format

- **WHEN** a contract capability ID is used in proposals
- **THEN** it SHALL follow the pattern `<engine-id>-contract` (e.g., `scrapling-get-contract`)
- **AND** it SHALL clearly distinguish from the engine capability ID itself

### Requirement: 输入契约规范

The system SHALL define the required fields for the input dimension of an engine contract.

#### Scenario: Input contract required fields

- **WHEN** an engine's input contract is defined
- **THEN** it SHALL specify:
  - URL format constraints and supported schemes
  - Required vs optional parameters with their types and defaults
  - Session mode support (single-shot, persistent, bulk)
  - Timeout behavior and default values
  - Header, cookie, and proxy parameter specifications
  - Authentication boundary rules (read-only by default)

#### Scenario: Input contract format

- **WHEN** input parameters are documented
- **THEN** each parameter SHALL include: name, type, required/optional, default value (if any), and a one-sentence description

### Requirement: 输出契约规范

The system SHALL define the required fields for the output dimension of an engine contract.

#### Scenario: Output contract required fields

- **WHEN** an engine's output contract is defined
- **THEN** it SHALL specify:
  - Supported extraction formats (markdown, text, html) with the default
  - Content structure fields (title, body/content, final URL, metadata)
  - Image handling rules (preserve inline image URLs vs strip)
  - Main content extraction behavior (whether default is body-only or full page)
  - Response metadata that MUST be present in every successful output

#### Scenario: Output contract schema

- **WHEN** output fields are documented
- **THEN** each field SHALL include: field name, type, presence (always/maybe), and a one-sentence description

### Requirement: 错误契约规范

The system SHALL define the required fields for the error dimension of an engine contract.

#### Scenario: Error contract required fields

- **WHEN** an engine's error contract is defined
- **THEN** it SHALL specify:
  - Error categories (at minimum: network, timeout, block/challenge, auth, parse/extraction)
  - Error response structure (error code, human-readable message, diagnostic context)
  - Recommended next action per error category (retry, escalate, stop, switch engine)

#### Scenario: Error contract completeness

- **WHEN** an engine encounters a failure mode not listed in its error contract
- **THEN** the error SHALL be reported as an "unclassified" error with full context preserved
- **AND** the engine's contract SHALL be updated to cover the newly discovered failure mode

### Requirement: 契约版本管理

The system SHALL define version management conventions for capability contracts.

#### Scenario: Contract version identifier

- **WHEN** a contract is created or modified
- **THEN** the contract SHALL include a version identifier at the top of the spec (e.g., `version: 1.0.0`)
- **AND** a change history section SHALL record each version with date and summary of changes

#### Scenario: Contract modification via change workflow

- **WHEN** an existing contract needs modification
- **THEN** the modification SHALL go through a new openspec change with a Modified Capabilities entry
- **AND** the change SHALL use MODIFIED Requirements blocks in its delta spec

### Requirement: 契约与 Phase 2 的关系

The system SHALL define how this metamodel feeds into Phase 2 engine contract creation.

#### Scenario: Phase 2 preconditions

- **WHEN** Phase 2 engine contract creation begins
- **THEN** the developer SHALL reference this metamodel as the normative contract structure
- **AND** each engine contract SHALL validate against the metamodel's input/output/error structure before being considered complete

#### Scenario: Metamodel evolution

- **WHEN** the contract metamodel itself needs modification (e.g., adding a new dimension)
- **THEN** the modification SHALL go through a new openspec change
- **AND** all existing engine contracts SHALL be reviewed for compliance with the updated metamodel
