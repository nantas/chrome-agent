# Specification Delta

## Capability 对齐（已确认）

- Capability: `extension-api`
- 来源: `phase-4-engine-extension-governance` proposal
- 变更类型: new

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: 新引擎接入 artifact checklist

The system SHALL define a mandatory artifact checklist for any new engine addition.

When adding a new engine to the system, the following artifacts SHALL be created or updated:

1. **Contract Spec**: `openspec/specs/<engine-id>-contract/spec.md`
2. **Registry Entry**: an entry in `configs/engine-registry.json`
3. **Engine-Contracts Integration**: update `openspec/specs/engine-contracts/spec.md`
4. **Strategy Integration** (if applicable): update relevant `engine_priority` or `engine_preference` references
5. **Decision Record**: `docs/decisions/YYYY-MM-DD-<engine-id>-addition.md`
6. **Smoke-Check Evidence**: evidence recorded in `reports/` or referenced in the decision record

#### Scenario: 最小可行接入

- **WHEN** a new engine is added that does not affect existing anti-crawl or site strategies
- **THEN** artifact 4 MAY be omitted
- **AND** artifacts 1, 2, 3, 5, and 6 SHALL still be completed

#### Scenario: 接入完整性验证

- **WHEN** an engine addition change is verified
- **THEN** all applicable artifacts from the checklist SHALL be present and complete
- **AND** missing any mandatory artifact SHALL block the change from being archived

### Requirement: 引擎 contract spec 模板

The system SHALL provide a contract spec template for new engines.

The template SHALL contain the following sections with placeholder markers wrapped in `{{ }}`:

```md
# Specification Delta

## Capability 对齐（已确认）

- Capability: `{{ engine-id }}-contract`
- 来源: `{{ change-name }}` proposal
- 变更类型: new

## 规范真源声明

- 本文件是该 capability 的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Input contract

The system SHALL define the input parameters for {{ engine-name }}.

[Describe URL format, required/optional parameters, session support, timeout behavior,
authentication boundaries]

#### Scenario: {{ input scenario }}

- **WHEN** {{ condition }}
- **THEN** {{ expected behavior }}

### Requirement: Output contract

The system SHALL define the output structure for {{ engine-name }}.

[Describe supported extraction formats, content structure fields, image handling,
metadata requirements]

#### Scenario: {{ output scenario }}

- **WHEN** {{ condition }}
- **THEN** {{ expected behavior }}

### Requirement: Error contract

The system SHALL define error handling for {{ engine-name }}.

[Describe error categories, error response structure, recommended next actions per category]

#### Scenario: {{ error scenario }}

- **WHEN** {{ condition }}
- **THEN** {{ expected behavior }}

### Requirement: Smoke-check

The system SHALL provide a smoke-check scenario to validate {{ engine-name }}.

#### Scenario: Smoke-check

- **WHEN** {{ engine-name }} is used against {{ target URL }}
- **THEN** the output SHALL contain {{ expected outcome }}
- **AND** no errors SHALL be returned
```

#### Scenario: 模板填充

- **WHEN** a developer creates a new engine contract spec using the template
- **THEN** they SHALL replace all `{{ }}` placeholders with concrete values
- **AND** they SHALL NOT leave any placeholder unresolved in the final spec

#### Scenario: 模板位置

- **WHEN** the contract spec template is needed
- **THEN** it SHALL be accessible at `openspec/specs/extension-api/contract-template.md`
- **AND** its content SHALL match the structure defined in this requirement

### Requirement: 引擎命名规范

The system SHALL define naming conventions for new engine identifiers.

New engine identifiers SHALL:
- Use kebab-case, all lowercase
- Follow the pattern `<tool-prefix>-<capability>`
- Match the directory stem `openspec/specs/<engine-id>-contract/`
- Be unique across all entries in `configs/engine-registry.json`
- NOT reuse a previously superseded identifier

#### Scenario: 命名规范验证

- **WHEN** a new engine identifier is proposed
- **THEN** it SHALL be validated against existing identifiers in the registry
- **AND** it SHALL conform to kebab-case format and `<tool-prefix>-<capability>` pattern

### Requirement: 接入验证要求

The system SHALL define validation requirements before an engine transitions from `draft` to `frozen`.

The following conditions SHALL be met:

1. Smoke-check scenario has been executed and passed
2. Evidence of smoke-check execution is recorded in `reports/` or the decision record
3. Contract spec has been reviewed for compliance with `capability-contracts`
4. Registry entry has been reviewed for consistency with contract spec
5. New error categories, if any, have been added to the `engine-contracts` error matrix
6. Relevant strategy files have been updated when the engine is usable in existing strategies

#### Scenario: Draft to frozen transition

- **WHEN** all validation conditions are met
- **THEN** the engine's status in `configs/engine-registry.json` SHALL change from `draft` to `frozen`
- **AND** the transition SHALL be documented in the relevant change's verification artifact

#### Scenario: Validation failure

- **WHEN** any validation condition is not met
- **THEN** the engine SHALL remain in `draft` status
- **AND** the failing condition SHALL be documented in the change's verification artifact with remediation steps

### Requirement: 接入治理规则

The system SHALL enforce governance rules for engine additions through AGENTS.md.

AGENTS.md SHALL include an `引擎扩展治理` section that:

1. States that new engines MUST go through the openspec change workflow
2. References `extension-api` spec for the artifact checklist
3. References `engine-registry` spec for the registration format
4. States that `configs/engine-registry.json` MUST be updated when engines are added, modified, or superseded
5. States that engine identifier naming follows the conventions in this spec

#### Scenario: 治理规则可发现

- **WHEN** an agent or operator needs to add a new engine
- **THEN** they SHALL find the governance rules in AGENTS.md under `引擎扩展治理`
- **AND** the section SHALL point to `extension-api` and `engine-registry` specs for detailed requirements

#### Scenario: 无 openspec change 禁止接入

- **WHEN** an engine is added without an openspec change
- **THEN** the addition SHALL be considered non-compliant
- **AND** the engine SHALL NOT be referenced by any strategy until properly registered

### Requirement: 决策记录要求

The system SHALL require a decision record for every new engine addition.

The decision record `docs/decisions/YYYY-MM-DD-<engine-id>-addition.md` SHALL contain:
- **Context**
- **Decision**
- **Consequences**

#### Scenario: 决策记录完整性

- **WHEN** a new engine addition change completes verification
- **THEN** the decision record SHALL be present in `docs/decisions/`
- **AND** it SHALL be indexed in `docs/decisions/README.md`
