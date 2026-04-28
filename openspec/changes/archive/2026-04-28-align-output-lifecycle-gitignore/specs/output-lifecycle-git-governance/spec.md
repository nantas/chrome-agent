# Specification Delta

## Capability 对齐（已确认）

- Capability: `output-lifecycle-git-governance`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认按当前清单执行，保留新增 capability 与既有 capability 修改。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Disposable outputs git ignore alignment
The repository MUST ignore disposable run outputs under `outputs/` in `.gitignore`.

#### Scenario: Disposable output generated
- **WHEN** a workflow emits transient run-scoped files beneath `outputs/`
- **THEN** those files SHALL remain untracked by default under Git status

### Requirement: Durable reports versioning visibility
The repository MUST keep durable report artifacts under `reports/` eligible for version control by default.

#### Scenario: Durable report created
- **WHEN** a workflow writes a reusable report or evidence file under `reports/`
- **THEN** the file SHALL be allowed to appear in Git status and be commit-eligible

## MODIFIED Requirements

## REMOVED Requirements

## RENAMED Requirements
