# Delta: pipeline-orchestration

## MODIFIED Requirements

### Requirement: orchestrator-responsibility

`pipeline/orchestrator.py` SHALL 仅包含：exit code 常量、`validate_api_config()` 函数、`run_pipeline()` 主编排函数。所有从 `registry.py`、`phases/fetch.py`、`phases/convert.py` 导入的符号通过明确的 import 声明依赖。发现摘要（discovery_summary.json）的构建不属于 orchestrator 职责，由 CLI 层承担。

#### Scenario: orchestrator-delegates
- **WHEN** `run_pipeline()` 需要构建管线策略 → 调用 `registry.build_pipeline()`
- **WHEN** `run_pipeline()` 执行 fetch phase → 调用 `phases.fetch.run_phase_fetch()`
- **WHEN** `run_pipeline()` 执行 convert phase → 调用 `phases.convert.run_phase_convert()`

#### Scenario: orchestrator-size-limit
- **WHEN** `orchestrator.py` 完成重构
- **THEN** 文件行数 ≤ 350 行
- **AND** 不包含 `_STRATEGY_REGISTRY`、`build_pipeline`、`run_phase_fetch`、`run_phase_convert` 的定义
