# Specification Delta

## Capability 对齐（已确认）

- Capability: `report-emission-gating`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 用户要求仅在 CLI explore 工作流或显式指定 report 参数时产出 `reports/`，避免常规简单抓取持续产出报告。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Durable report emission gate
The CLI MUST gate durable report creation under `reports/` by workflow intent or explicit operator request.

Default gate policy SHALL be:
- `explore` workflow: durable report emission enabled by default
- non-`explore` workflows (including fetch and crawl): durable report emission disabled by default
- explicit report flag/parameter: enables durable report emission regardless of workflow

#### Scenario: Default simple fetch execution
- **WHEN** the operator runs a simple fetch-style command without an explicit report parameter
- **THEN** the CLI SHALL return extracted content/artifact metadata without creating a durable file under `reports/`

#### Scenario: Explore workflow execution
- **WHEN** the operator runs the `explore` workflow without overriding report behavior
- **THEN** the CLI SHALL create a durable report artifact under `reports/`

#### Scenario: Explicit report request on non-explore workflow
- **WHEN** the operator runs `fetch` or `crawl` and explicitly requests report output via CLI parameter
- **THEN** the CLI SHALL create a durable report artifact under `reports/`

## MODIFIED Requirements

## REMOVED Requirements

## RENAMED Requirements
