# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-phases-fetch`
- 来源: `proposal.md` New Capabilities
- 变更类型: `new`
- 用户确认摘要: 基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 3 设计确认

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: fetch-phase-module
系统 SHALL 将 `run_phase_fetch()` 函数从 `orchestrate.py` 提取到独立模块 `pipeline/phases/fetch.py`。

#### Scenario: module-extraction
- **WHEN** `pipeline/phases/fetch.py` 被创建
- **THEN** 文件包含 `run_phase_fetch()` 函数及其内部 `_fetch_one()` 辅助函数
- **AND** 函数签名、并发逻辑、缓存跳过逻辑、统计计数与重构前完全一致

### Requirement: fetch-phase-imports
模块 SHALL 从 `..phase_b` 导入 `fetch_single_page`，从 `..client` 导入 `ApiClient` 和 `PageNotFoundError`，从 `..` 导入 `cache as cache_mod`，不依赖 `orchestrator.py`。

#### Scenario: self-contained-imports
- **WHEN** `phases/fetch.py` 的 import 被审查
- **THEN** 不存在对 `orchestrator.py` 或 `orchestrate.py` 的 import
- **AND** 所有必要的运行时依赖通过相对 import 获取

### Requirement: fetch-phase-no-behavior-change
`run_phase_fetch()` 的行为 SHALL 与重构前完全一致，包括并发控制、缓存判断、错误处理和统计输出。

#### Scenario: fetch-behavior-preservation
- **WHEN** 对同一站点执行完整 pipeline 的 fetch phase
- **THEN** 产出（缓存文件、统计计数、日志输出）与重构前完全相同
