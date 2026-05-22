# Proposal

## 问题定义

对 `bindingofisaacrebirth.wiki.gg` 的 homepage-driven discovery（1757 页）暴露了 `page_assigner` exact-1-match 逻辑的过度防御问题。

`_apply_source_category_assignments` (Step 2) 当前仅在页面恰好匹配 **1 个** `assignment_priority` 类别时分配。匹配 2+ 个类别的页面被延迟到 Step 3（MW category matching），旨在通过官方 MW 分类标签打破 source_categories 的歧义（例如 "Basement" 同时出现在 Bosses 和 Chapters 列表页 → MW "Stages" → Chapters）。

但 71 个页面匹配 2+ 个 source_categories 且 **MW 分类标签为空**。延迟后 Step 3 无匹配项，Step 4 将它们分配到 `misc`，尽管其 source_categories 明确包含 "Items"（priority 1）：

| 页面 | source_categories | MW | 当前去向 | 预期去向 |
|------|------------------|-----|---------|---------|
| Activated item | Items, Trinkets | [] | misc | items |
| Passive item | Items, Characters | [] | misc | items |
| Card | Items, Trinkets, Characters, Rooms | [] | misc | items |
| Bomb | Items, Characters | [] | misc | items |
| Floor | Items, Rooms | [] | misc | items |
| Shot speed | Items, Trinkets, Characters, Attributes | [] | misc | items |
| …（共 71 页） | | | misc | items |

**根因**：Step 2 对多匹配页面不做任何分配（未设置 `assignment_method`），Step 3 只在 MW 类别匹配时分配，Step 4 将所有剩余页面发往 `misc`。无 MW 类别的多匹配页面在 Step 2→3→4 链中无任何步骤处理。

## 范围边界

**范围内：**
- 在 `assign_pages()` 中新增 Step 3.5：对 Step 3 后仍 `assignment_method=None` 的页面，用 source_categories 的 first-match-wins 做回退分配
- 新 `assignment_method`：`"source_category_fallback"` 用于区分与直接的 `"source_category_match"`
- 单元测试覆盖：单匹配、多匹配无 MW、多匹配有 MW（确保不会覆盖正确的 MW 匹配）

**范围外：**
- 不修改 Step 2（exact-1-match 逻辑保留）
- 不修改 Step 3（MW 匹配逻辑保留）
- 不修改策略文件
- 不修改 BOI 站点配置（由 `fix-boi-config-issues` 覆盖）

## Capabilities

### Modified Capabilities

- `page-assignment`: 在 MW 匹配后（Step 3）与默认分配（Step 4）之间新增 source_categories first-match-wins 回退步骤。Step 2 匹配 2+ source_categories 但无 MW 类别的页面不再落入 `misc`，而是回退到 source_categories 优先级链。

## Capabilities 待确认项

- [x] 能力清单已基于复现数据确认：71 页证据，根因明确
- [x] 修改范围已确认：仅 page_assigner.py，约 10 行新增

## Impact

| 维度 | 详情 |
|------|------|
| page_assigner 行为 | 新增 Step 3.5：first-match-wins 回退，assigned_category 取自 source_categories |
| assignment_method 枚举 | 新增 `"source_category_fallback"` 值 |
| 对当前行为的影响 | 已在 exact-1-match 中正确分配的页面无变化；已在 Step 3 中匹配的页面无变化；仅当前发往 misc 的 71 页会重新分配到正确类别 |
| 向后兼容 | 仅新增步骤；现有 Step 1–4 逻辑不变 |
| BOI 具体影响 | misc 从 164 → ~93（减少 71 页） |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页：`openspec/specs/page-assignment/`
- 已确认项目页：`scripts/pipeline/pipeline/page_assigner.py`、`sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
- 回写目标：`openspec/specs/page-assignment/spec.md`
