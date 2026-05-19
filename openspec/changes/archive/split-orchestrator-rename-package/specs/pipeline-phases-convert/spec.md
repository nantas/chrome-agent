# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-phases-convert`
- 来源: `proposal.md` New Capabilities
- 变更类型: `new`
- 用户确认摘要: 基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 3 设计确认

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: convert-phase-module
系统 SHALL 将 `run_phase_convert()` 函数从 `orchestrate.py` 提取到独立模块 `pipeline/phases/convert.py`。

#### Scenario: module-extraction
- **WHEN** `pipeline/phases/convert.py` 被创建
- **THEN** 文件包含 `run_phase_convert()` 函数
- **AND** 函数签名、缓存读取逻辑、转换调度、content_acquisition 不匹配警告与重构前完全一致

### Requirement: convert-phase-imports
模块 SHALL 从 `..phase_b` 导入 `convert_single_page`，从 `..registry` 导入 `build_pipeline`，从 `..` 导入 `cache as cache_mod`，不依赖 `orchestrator.py`。

#### Scenario: self-contained-imports
- **WHEN** `phases/convert.py` 的 import 被审查
- **THEN** 不存在对 `orchestrator.py` 或 `orchestrate.py` 的 import
- **AND** 策略构建通过 `registry.build_pipeline()` 完成，不再内联调用

### Requirement: convert-phase-no-behavior-change
`run_phase_convert()` 的行为 SHALL 与重构前完全一致，包括缓存加载、content_acquisition 不匹配警告、link_resolver 和 template_processor 构建、统计输出。

#### Scenario: convert-behavior-preservation
- **WHEN** 对同一站点执行完整 pipeline 的 convert phase
- **THEN** 产出（Markdown 文件、extraction_results.json、统计计数）与重构前完全相同
