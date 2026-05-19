# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-phase-naming`
- 来源: `proposal.md` / 已确认 capabilities
- 变更类型: modified
- 用户确认摘要: 纯结构性重构，LSP 验证完成，无新增能力

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: phase-file-naming-alignment
Phase 文件 SHALL 按实际功能命名，文件名 SHALL 使用语义化名称而非序号标识。

#### Scenario: phase-file-discovery
- **WHEN** 开发者浏览 `pipeline/pipeline/phases/` 目录
- **THEN** 文件名直接反映功能：`discovery_homepage.py`、`discovery_allpages.py`、`fetch.py`、`convert.py`、`assemble.py`

### Requirement: phase-b-function-consolidation
`phase_b.py` 中的活跃函数 SHALL 被内化到对应的 phases 文件中，消除跨文件反向导入。

#### Scenario: fetch-single-page-colocation
- **WHEN** `phases/fetch.py` 需要调用 `fetch_single_page`
- **THEN** 函数定义在同一文件中，无需从 `phase_b.py` 导入

#### Scenario: convert-single-page-colocation
- **WHEN** `phases/convert.py` 需要调用 `convert_single_page` 和 `_process_html_page`
- **THEN** 函数定义在同一文件中，无需从 `phase_b.py` 导入

### Requirement: dead-code-removal
`phase_b.py` 中无外部调用方的函数 SHALL 被删除。

#### Scenario: run-phase-b-removal
- **WHEN** `run_phase_b` 和 `process_single_page` 仅形成闭环死链（无外部调用）
- **THEN** 两个函数 SHALL 被删除，orchestrate.py 中对应 import SHALL 被移除

#### Scenario: stale-top-level-files-removal
- **WHEN** `scripts/pipeline/phase_{a,b,c}.py` 顶层文件零外部引用
- **THEN** 这些文件 SHALL 被删除

## REMOVED Requirements

### Requirement: phase-b-monolith
**Reason**: `phase_b.py` 的职责已被 `phases/fetch.py` 和 `phases/convert.py` 在 Change 3 中拆分接管，剩余函数应内化到对应文件
**Migration**: 调用方（`phases/fetch.py`、`phases/convert.py`）的 import 路径从 `..phase_b` 改为本地定义

## RENAMED Requirements

- FROM: `### Requirement: phase_0-file`
- TO: `### Requirement: discovery-homepage-file`

- FROM: `### Requirement: phase_a-file`
- TO: `### Requirement: discovery-allpages-file`

- FROM: `### Requirement: phase_c-file`
- TO: `### Requirement: assemble-file`
