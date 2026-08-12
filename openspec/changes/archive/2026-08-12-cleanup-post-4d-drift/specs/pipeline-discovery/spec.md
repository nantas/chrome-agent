# Delta: pipeline-discovery

## REMOVED Requirements

### Requirement: discovery-summary-module

**Rationale**: 模块已无人调用——`discovery_summary.json` 实际由 `chrome-agent-cli.mjs` 内联 JS 构建，`pipeline/discovery_summary.py` 全仓零 import。模块组织类 requirement 随模块删除失效。

### Requirement: discovery-summary-imports

**Rationale**: 随 `discovery-summary-module` 一并失效（约束对象不存在）。

### Requirement: unit-test-compatibility

**Rationale**: 被引用的 `test_discovery_summary.py` 测的是手动复制的副本而非真实模块，已随模块一并删除。
