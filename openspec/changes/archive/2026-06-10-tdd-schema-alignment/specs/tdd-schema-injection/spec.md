# Specification Delta

## Capability 对齐（已确认）

- Capability: `tdd-schema-injection`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: grill session 确认——schema 注入 TDD + J3，条件排除纯文档任务

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: TDD vertical slice in tasks instruction
The `tasks` artifact instruction SHALL require that code-modifying tasks be decomposed as vertical slices, each containing a test sub-task and an implementation sub-task. Pure documentation tasks are exempt.

#### Scenario: Code task with vertical slice
- **WHEN** a task involves modifying `scripts/`, `sites/strategies/`, or `.agents/skills/` code
- **THEN** the tasks.md SHALL contain a test sub-task (RED) before the implementation sub-task (GREEN) for that task

#### Scenario: Pure documentation task
- **WHEN** a task only modifies `.md` files or `docs/` content
- **THEN** no test sub-task is required; the task may stand alone

### Requirement: TDD enforcement in apply instruction
The `apply` phase instruction SHALL instruct the agent to follow TDD vertical slice flow for code tasks: write test first (RED), then implement (GREEN), then refactor if needed. The instruction SHALL conditionally exclude pure documentation tasks.

#### Scenario: Agent implements a code task
- **WHEN** the agent encounters a task that modifies Python or JavaScript source files
- **THEN** the agent SHALL write or update the corresponding test first, verify it fails (RED), then implement the change (GREEN)

#### Scenario: Agent implements a documentation task
- **WHEN** the agent encounters a task that only modifies markdown or documentation files
- **THEN** the agent SHALL proceed directly without requiring a RED→GREEN cycle

### Requirement: J3 test completeness in verification instruction
The `verification` artifact instruction SHALL include J3 severity rules for test completeness: new modules without tests = CRITICAL; modified modules without updated tests = WARNING.

#### Scenario: New module without tests
- **WHEN** a new `.py` or `.mjs` module is created in `scripts/` and no corresponding test file exists in `tests/`
- **THEN** the verification report SHALL flag this as a CRITICAL issue

#### Scenario: Modified module without updated tests
- **WHEN** an existing module in `scripts/lib/` or `scripts/pipeline/` is modified and its corresponding test file is unchanged
- **THEN** the verification report SHALL flag this as a WARNING

#### Scenario: Documentation-only change
- **WHEN** only `.md` files are modified
- **THEN** no test completeness check is required; the verification SHALL proceed without test checks
