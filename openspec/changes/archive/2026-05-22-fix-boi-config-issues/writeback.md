# Writeback

## Change: fix-boi-config-issues
## Date: 2026-05-22
## Status: ready

## 回写摘要

本次 change 对 BOI 策略文件 `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` 执行了以下配置补全：

### 修改 1: assignment_priority 补全

`assignment_priority` 已包含 `"Attributes"` 和 `"Completion Marks"`（无需追加，已存在）。

### 修改 2: page_categories 映射修正与追加

| MW Category | 变更类型 | 原值 | 新值 |
|------------|---------|------|------|
| Runes | 修正 | `"Runes"` | `"Cards"` |
| Item pools | 修正 | `"Item_pools"` | `"Items"` |
| Special cards | 新增 | — | `"Cards"` |
| Mini-bosses | 新增 | — | `"Bosses"` |

### 影响预估

- **misc 目录**: 预计减少约 31 页
- **cards/ 目录**: 预计增加约 25 页（17 Runes + 8 Special cards）
- **bosses/ 目录**: 预计增加约 3 页
- **items/ 目录**: 预计增加约 3 页

## 回写目标

- **文件**: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
- **字段**: `api.homepage.assignment_priority`, `api.taxonomy.page_categories`

## 验证结论

- verification.md: ALL CHECKS PASSED
- 回归风险: LOW（原映射无效，修改为有效映射）
- 向后兼容: PASS（仅追加/修正，不修改已有有效映射）

## Writeback 执行状态

- [x] Runes: "Runes" → Runes: "Cards"
- [x] Item pools: "Item_pools" → Item pools: "Items"
- [x] Special cards: "Cards" (新增)
- [x] Mini-bosses: "Bosses" (新增)
- [x] assignment_priority: 已确认 Attributes 和 Completion Marks 存在
