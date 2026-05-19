# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-discovery-summary`
- 来源: `proposal.md` New Capabilities
- 变更类型: `new`
- 用户确认摘要: 基于 `docs/plans/2026-05-19-structure-refactor-and-docs.md` § Change 3 设计确认

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: discovery-summary-module
系统 SHALL 将 `build_discovery_summary()` 及其 5 个辅助函数（`_build_homepage_categories`、`_build_allpages_categories`、`_build_excluded_list`、`_build_unclassified`、`_estimate_time`）从 `orchestrate.py` 提取到独立模块 `pipeline/discovery_summary.py`。

#### Scenario: module-contents
- **WHEN** `pipeline/discovery_summary.py` 被创建
- **THEN** 文件包含 `build_discovery_summary()` 主函数和全部 5 个辅助函数
- **AND** 函数签名与行为与重构前完全一致

### Requirement: discovery-summary-imports
模块 SHALL 从 `...lib.config_resolver` 导入 `RateLimitConfig` 类型注解，不依赖 `orchestrator.py` 中的任何符号。

#### Scenario: no-orchestrator-dependency
- **WHEN** `discovery_summary.py` 的 import 被审查
- **THEN** 不存在对 `orchestrator.py` 或 `orchestrate.py` 的 import

### Requirement: unit-test-compatibility
系统 SHALL 确保 `scripts/pipeline/tests/test_discovery_summary.py`（Change 3 后路径）中的现有单元测试在模块移动后仍然通过。

#### Scenario: existing-tests-pass
- **WHEN** 执行 `python3 scripts/pipeline/tests/test_discovery_summary.py`
- **THEN** 所有 12 个测试用例通过
