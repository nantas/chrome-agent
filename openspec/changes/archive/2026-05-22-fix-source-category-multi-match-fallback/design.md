# Design

## Context

`page_assigner.assign_pages()` 当前有 4 个步骤：

1. Manual overrides
2. Source category match（exact-1-match — 仅单匹配）
3. MW category tag matching（带 alias 和 page_categories fallback）
4. Default → `misc`

Step 2 的 exact-1-match 逻辑是 `fix-boi-config-issues` 引入的，用于将多 source_categories 匹配的页面（如同时出现在 Bosses 和 Chapters 列表页的楼层）延迟到 Step 3，由 MW 分类标签（"Stages" → Chapters）做终裁。

但此逻辑无法处理有 2+ source_categories 匹配但 **没有 MW 标签** 的页面。这些页面在 Step 2→3→4 链中无任何步骤匹配，最终落入 `misc`。对 BOI 站点，这类页面有 71 个。

## Goals / Non-Goals

**Goals:**

1. 新增 Step 3.5：source_categories first-match-wins 回退，处理 Step 3 后仍未分配的页面
2. 新 `assignment_method` 值 `"source_category_fallback"` 用于可观测性
3. 不对 Step 2 或 Step 3 的现有行为产生回归

**Non-Goals:**

1. 不修改 Step 2 的 exact-1-match 逻辑
2. 不修改 Step 3 的 MW 匹配逻辑
3. 不引入新的优先级或评分系统
4. 不修改策略文件或 BOI 站点配置

## Decisions

### D1: Step 3.5 作为独立步骤，不在 Step 2 中处理

**选项 A**：将 Step 2 改为"先 exact-1-match，失败再 first-match-wins"

**选项 B**：在 Step 3 和 Step 4 之间插入独立步骤 Step 3.5

**决策：选项 B。**

理由：
- Step 2 的"延迟双匹配"设计目的是让 MW 类别有机会打破歧义。在 Step 2 中做 fallback 会绕过 MW 类别的权威性（例如 Basement 会被 Step 2 分配为 Bosses 而非让 MW "Stages" 纠正为 Chapters）
- Step 3.5 作为独立步骤，保证 MW 匹配始终优先于 source_categories 回退
- Step 2、3、3.5、4 的线性顺序易于理解和测试

### D2: first-match-wins 而非 score-based

**决策：first-match-wins 与 `assignment_priority` 顺序一致。**

理由：
- 复用已有的 `assignment_priority` 排序，无新配置
- Step 2（单匹配时）已采用相同语义，一致性更好
- 回退场景中 source_categories 的 priority 顺序足够——第一优先级类别（通常是"Items"）是合理的默认选择

### D3: 新 assignment_method 值

**决策：`"source_category_fallback"`。**

理由：
- 可观测性：从 manifest 可区分"直接单匹配"与"回退多匹配"
- 不影响现有 `"source_category_match"` 或 `"mw_category_match"` 值的语义

## Risks / Migration

| 风险 | 影响 | 缓解 |
|------|------|------|
| 回退将页面分配给错误目录 | BOI 站点上 71 页中的部分页面偏好不同的类别 | 回退分配基于 source_categories（页面在 wiki 列表页上的存在位置）——这是比 misc 更好的信号。用户可通过 MW 分类别名进一步优化策略 |
| 破坏现有确切单匹配行为 | 提前停止的 Step 3.5 迭代影响已分配的页面 | 第 3.5 步仅处理 `assignment_method=None` 的页面；已分配的页面不受影响 |
| Step 2 未来变更与 Step 3.5 冲突 | Step 2 中的逻辑变更可能需要调整第 3.5 步 | 当前语义明确：Step 2 处理单匹配；Step 3 使用 MW；Step 3.5 对剩余页面使用 source_categories 回退。未来变更应保留此顺序 |
