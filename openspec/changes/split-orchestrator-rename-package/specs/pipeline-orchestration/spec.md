# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-orchestration`
- 来源: `proposal.md` Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 3 设计确认

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## MODIFIED Requirements

### Requirement: orchestrator-responsibility
`pipeline/orchestrator.py` SHALL 仅包含：exit code 常量、`validate_api_config()` 函数、`run_pipeline()` 主编排函数。所有从 `registry.py`、`discovery_summary.py`、`phases/fetch.py`、`phases/convert.py` 导入的符号通过明确的 import 声明依赖。

#### Scenario: orchestrator-size-limit
- **WHEN** `orchestrator.py` 完成重构
- **THEN** 文件行数 ≤ 350 行
- **AND** 不包含 `_STRATEGY_REGISTRY`、`build_pipeline`、`build_discovery_summary`、`run_phase_fetch`、`run_phase_convert` 的定义

#### Scenario: orchestrator-delegates
- **WHEN** `run_pipeline()` 需要构建管线策略
- **THEN** 调用 `registry.build_pipeline()` 而非内联函数
- **WHEN** `run_pipeline()` 需要构建发现摘要
- **THEN** 调用 `discovery_summary.build_discovery_summary()`
- **WHEN** `run_pipeline()` 执行 fetch phase
- **THEN** 调用 `phases.fetch.run_phase_fetch()`
- **WHEN** `run_pipeline()` 执行 convert phase
- **THEN** 调用 `phases.convert.run_phase_convert()`

### Requirement: run-pipeline-no-behavior-change
`run_pipeline()` 的端到端行为 SHALL 与重构前完全一致，包括策略解析、API 探测、discovery 调度、exclude 过滤、resume 状态管理、link fix 和 L6 validation。

#### Scenario: end-to-end-preservation
- **WHEN** 执行 `python3 -m scripts.pipeline pipeline <url> --strategy <path> --output <dir>`
- **THEN** 产出（manifest、discovery_summary、Markdown 文件、extraction_results.json）与重构前完全相同
- **AND** 退出码语义不变（0=success, 1=partial, 10+=failure）

### Requirement: public-api-compatibility
`pipeline/pipeline/__init__.py` SHALL 重新导出所有 `orchestrator.py` 中的公共 API（`run_pipeline`、`build_pipeline`、`validate_api_config`、exit codes 等），确保 `cli.py` 和其他消费者的 import 路径不需要更改符号名。

#### Scenario: init-re-exports
- **WHEN** `from scripts.pipeline.pipeline import run_pipeline, EXIT_SUCCESS` 被执行
- **THEN** 成功获取对应符号
