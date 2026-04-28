# Specification Delta

## Capability 对齐（已确认）

- Capability: `output-lifecycle`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认按当前清单执行，保留新增 capability 与既有 capability 修改。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

## MODIFIED Requirements

### Requirement: Artifact classes
The system SHALL classify CLI artifacts into durable and disposable classes, and repository defaults MUST align git tracking behavior with those classes.

The minimum classes SHALL be:
- durable reports under `reports/`
- disposable run outputs under `outputs/`

Repository default tracking alignment SHALL be:
- `outputs/` ignored in `.gitignore`
- `reports/` not globally ignored by `.gitignore`

#### Scenario: Lifecycle-to-git consistency
- **WHEN** maintainers validate repository lifecycle policy
- **THEN** `outputs/` SHALL be configured as ignored disposable artifacts
- **AND** `reports/` SHALL be retained as durable artifacts eligible for version control

## REMOVED Requirements

## RENAMED Requirements
