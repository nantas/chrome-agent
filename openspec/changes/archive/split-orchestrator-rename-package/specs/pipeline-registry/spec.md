# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-registry`
- 来源: `proposal.md` New Capabilities
- 变更类型: `new`
- 用户确认摘要: 基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 3 设计确认

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: strategy-registry-module
系统 SHALL 将 `_STRATEGY_REGISTRY`、`DEFAULT_STRATEGIES`、`_PROFILE_KEY_MAP`、`PipelineStrategies` dataclass 从 `orchestrate.py` 提取到独立模块 `pipeline/registry.py`，作为策略注册表的唯一权威来源。

#### Scenario: registry-module-contents
- **WHEN** `pipeline/registry.py` 被创建
- **THEN** 文件包含 `PipelineStrategies` dataclass、`DEFAULT_STRATEGIES` dict、`_STRATEGY_REGISTRY` dict、`_PROFILE_KEY_MAP` dict、公共别名 `STRATEGY_REGISTRY` 和 `PROFILE_KEY_MAP`
- **AND** 文件行数 ≤ 160 行

### Requirement: build-pipeline-factory
系统 SHALL 将 `build_pipeline(strategy, domain)` 函数移至 `pipeline/registry.py`，行为与当前 `orchestrate.py` 中的实现完全一致。

#### Scenario: build-pipeline-delegation
- **WHEN** 调用 `registry.build_pipeline(strategy, domain)`
- **THEN** 返回 `PipelineStrategies` 实例，策略解析逻辑与重构前完全相同
- **AND** 无效策略 ID 仍触发 `ValueError`

### Requirement: derive-capabilities-function
系统 SHALL 将 `derive_capabilities(content_profile)` 函数移至 `pipeline/registry.py`，行为不变。

#### Scenario: derive-capabilities-move
- **WHEN** 调用 `registry.derive_capabilities(content_profile)`
- **THEN** 返回排序后的能力列表，逻辑与重构前相同

### Requirement: strategy-registry-public-api
系统 SHALL 通过 `pipeline/pipeline/__init__.py` 重新导出 `STRATEGY_REGISTRY`、`PROFILE_KEY_MAP`、`build_pipeline`、`derive_capabilities`、`PipelineStrategies`，确保外部消费者（`bootstrap-strategy`、`architecture_gate`）无需修改 import 路径中的符号名。

#### Scenario: public-re-exports
- **WHEN** 外部代码通过 `from scripts.pipeline.pipeline import STRATEGY_REGISTRY` 导入
- **THEN** 成功获取与重构前相同的注册表对象
