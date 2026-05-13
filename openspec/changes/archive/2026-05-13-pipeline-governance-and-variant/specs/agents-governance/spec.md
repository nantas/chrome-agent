# Specification Delta

## Capability 对齐（已确认）

- Capability: `agents-governance`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户同意在 AGENTS.md 中新增 Pipeline Strategy Schema 治理章节

## 规范真源声明

- 本文件是 `agents-governance` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Pipeline Strategy Schema 治理章节

The system SHALL 在 AGENTS.md 中新增 Pipeline Strategy Schema 治理章节，作为 Section 7（策略库治理）的子章节或独立章节。

该章节 SHALL 包含以下内容：

1. **权威来源声明**：声明 `_STRATEGY_REGISTRY` 为策略 ID 的唯一权威来源
2. **策略文件约束**：`content_profile` 字段只能引用已注册 ID
3. **扩展协议**：实现 → 注册 → 引用的严格顺序
4. **Registry 变更约束**：删除/重命名 ID 前必须反向检查
5. **当前注册 ID 清单**：各维度的合法 ID 列表（快速参考，不替代代码权威）

#### Scenario: 章节结构

- **WHEN** 用户或 agent 阅读 AGENTS.md 的 Pipeline Strategy Schema 治理章节
- **THEN** 该章节 SHALL 位于策略库治理（当前 Section 7）之后或作为其子章节
- **AND** SHALL 包含完整的扩展协议和注册 ID 参考表
- **AND** SHALL 明确引用 `scripts/mediawiki-api-extract/pipeline/orchestrate.py` 作为 `_STRATEGY_REGISTRY` 的权威位置
