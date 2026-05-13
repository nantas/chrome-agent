# Specification Delta

## Capability 对齐（已确认）

- Capability: `explore`
- 来源: `proposal.md`
- 变更类型: `modified`
- 用户确认摘要: 从"仅返回 strategy gap"升级为"执行完整探索工作流"，向后兼容已有策略命中场景

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: explore-command-backend

The system SHALL route `explore` into the full deep-discovery wofkflow when no strategy exists, while retaining the existing behavior when a strategy IS matched.

#### Scenario: strategy-matched
- **WHEN** `explore <url>` is called and a strategy exists in the registry for the domain
- **THEN** the system SHALL continue with the existing behavior (load strategy, return structured report)
- **THEN** no change in this scenario

#### Scenario: strategy-gap
- **WHEN** `explore <url>` is called and no strategy exists for the domain
- **THEN** the system SHALL NOT simply return "strategy gap"
- **THEN** the system SHALL enter the deep discovery pipeline (see `explore-workflow` spec)
- **THEN** the system SHALL proceed through: probe chain → API discovery → structure mapping → protection identification
- **THEN** the system SHALL engage interactive scope confirmation with the user
- **THEN** the system SHALL generate strategy scaffold
- **THEN** the system SHALL produce and self-check samples
- **THEN** the system SHALL present results for user review
- **THEN** on approval, the system SHALL freeze the strategy

### Requirement: explore-output-format

The system SHALL produce consistent structured output with additional fields for the new deep-discovery workflow.

#### Scenario: output-format-extended
- **WHEN** deep discovery is complete
- **THEN** the output SHALL include the standard fields (`result`, `command`, `target`, `summary`, `artifacts`, `next_action`, `workflow`, `engine_path`)
- **THEN** the output SHALL additionally include:
  - `discovery.engine_chain[]` — results from each engine probe
  - `discovery.api` — detected API configuration
  - `discovery.content_profile` — page type classification, nav sections, template patterns
  - `discovery.protection` — identified protection mechanism
  - `discovery.scale` — estimated site scale (if API available)
  - `scaffold.path` — path to generated strategy scaffold (if applicable)
  - `samples[]` — list of sample page titles selected for conversion
  - `self_check.summary` — per-sample and overall pass/fail summary
