# Design

## Context

前次 change（`fix-pipeline-assignment-and-output`）的 S-1 修复将 `_apply_source_category_assignments` 从仅匹配 `category_page` 类型扩展为匹配所有类型（`list_page` + `category_page`）。这修复了大多数页面分配问题，但引入了一个副作用：

MediaWiki 列表页之间存在广泛的交叉链接（导航模板、侧边栏、章节表格等），导致同一页面出现在多个列表页的 `prop=links` 结果中。例如：

- Bosses 列表页的导航模板链接到所有楼层页面（Basement, Caves, Womb 等）
- Chapters 列表页的内容表格链接到所有楼层页面

两个列表页的链接集通过 `prop=links` 被完整捕获，使楼层页面的 `source_categories` 同时包含 `"Bosses"` 和 `"Chapters"`。由于 `assignment_priority` 中 "Bosses" 排在 "Chapters" 之前，Step 2 将楼层分配到了 `bosses/`。

当前分配链：

```
Step 2: source_categories 匹配 → 第一匹配即分配
  Basement: source_categories=["Bosses", "Chapters"]
  → "Bosses"(priority 2) 先匹配 → 分配到 bosses/  (❌ 错误)

Step 3: MW category 匹配 (对已分配页面不执行)
  → 无法到达
```

设计方案的核心思路：**当 `source_categories` 存在冲突（匹配到多个类别）时，不进行猜测，而是延后到 MW category 匹配（Step 3）做终裁。** MW category 是由 MediaWiki 系统直接赋值的页面属性，比从列表页链接推断出的 `source_categories` 更可信。

另一个独立问题：`assignment_priority` 缺失 `Attributes` 和 `Completion Marks` 两个类别，导致这两个目录只有 index.md，所有成员页面无法被分配。

## Goals / Non-Goals

**Goals:**

1. 修改 `_apply_source_category_assignments()`：当页面匹配到**唯一** `source_categories` 时立即分配；匹配到**多个**时延后到 Step 3
2. 修改 BOI 策略 `assignment_priority`：补全 `Attributes` 和 `Completion Marks`
3. 验证分配结果：楼层页面进入 `chapters/`，属性进入 `attributes/`，完成标记进入 `completion_marks/`
4. 确保 non-BOI 站点不受影响（单一匹配行为不变）

**Non-Goals:**

1. 不修改 `_apply_mw_category_matching()` 逻辑
2. 不新增 API 调用——MW categories 已在 `assign_pages()` 开始时批量查询，Step 3 的 MW 数据对 deferred pages 立即可用
3. 不修改 `discovery_homepage.py` 的 `source_categories` 生成
4. 不修改其他站点策略

## Decisions

### D1: 唯一匹配 + 延后策略

选择"唯一匹配才分配，多匹配延后"而非"从多匹配中选优先级最高"：

- **理由 1**: 多匹配本质上是噪声（交叉链接导致），非分类信号。使用 MW category 做终裁更符合 MediaWiki 的语义体系——MW 分类是页面作者明确赋予的标签。
- **理由 2**: MW category 已经在 `assign_pages()` 开头批量查询，被 deferred 的页面只是多了一步检查，无额外 API 开销。
- **理由 3**: 此选择影响所有站点，但语义上更正确——当多个分类来源冲突时，使用最权威的信号（MW tags）裁决。

**不选择**排除列表页特定链接（如 `exclude_links` 策略字段），因为：
- 增加策略配置负担，每站点需手动配置
- 交叉链接是普遍现象，不应期望站点策略作者逐一排除
- 无法覆盖未知的交叉链接模式

### D2: 补全 `assignment_priority` 为配置修复

`Attributes` 和 `Completion Marks` 的缺失不是代码 bug，而是 BOI 策略配置不完整。补全到 `assignment_priority` 的末尾位置（不会影响已有类别的优先级顺序）。

### D3: deferred pages 无优先级惩罚

从 Step 2 延后的页面在 Step 3 中与零匹配页面同等对待——按 `assignment_priority` 顺序、alias 匹配、`page_categories` 兜底。不设额外权重或惩罚。

### 分配链对比

**修复前：**
```
Step 2: 第一匹配即分配
  Basement → source_categories=["Bosses", "Chapters"]
  → "Bosses"(p2) 匹配 → 即时分配 → bosses/ ❌

Step 2: 唯一匹配
  The Sad Onion → source_categories=["Items"]
  → "Items"(p1) 唯一匹配 → 即时分配 → items/ ✅
```

**修复后：**
```
Step 2: 唯一匹配才分配
  Basement → source_categories=["Bosses", "Chapters"]
  → 多匹配 → 不分配 → 延后到 Step 3

Step 3: MW category 终裁
  Basement → mw_categories=["Stages"]
  → "Chapters" alias "Stages"(p8) 匹配 → 分配到 chapters/ ✅

Step 2: 唯一匹配
  The Sad Onion → source_categories=["Items"]
  → "Items"(p1) 唯一匹配 → 即时分配 → items/ ✅
```

## Risks / Migration

| 风险 | 影响 | 缓解策略 |
|------|------|---------|
| **单一匹配页面被错误阻止**：原本的单一匹配逻辑被错误地改成要求严格唯一 | 所有页面无法分配，全部进入 misc | 单元测试覆盖 3 种场景：单一匹配/多匹配/零匹配 |
| **第三方站点退化**：如果一个站点依赖多匹配时的"第一匹配即分配"行为 | 该站点的页面分类发生变化 | 当前行为本质上是噪声（交叉链接），没有任何站点应该依赖此行为。如果出现退化，revert 并评估该站点的替换方案 |
| **MW 查询失败导致 deferred pages 全部进入 misc** | 多匹配页面在 Step 3 也没有匹配，落入 misc | 与现有零匹配页面的 fallback 行为一致——MW 查询失败已有重试和 misc fallback。无新增风险 |
| **assignment_priority 补全遗漏**：BOI 策略还有其他的缺失条目 | 其他类别页面分配错误 | 通过 code review 确认 priority 与 categories 完整性；建立 lint 规则 |
