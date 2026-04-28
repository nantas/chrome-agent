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
