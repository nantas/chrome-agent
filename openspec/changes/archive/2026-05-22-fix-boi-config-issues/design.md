# Design

## Context

本次 change 是纯策略配置变更，涉及 `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` 的 YAML frontmatter 修改。

当前配置缺口：

```
assignment_priority:  [Items, Bosses, ..., Objects]     ← 缺 Attributes, Completion Marks
page_categories:      {..., Stages: Chapters, ...}       ← 缺 Runes, Special cards, Mini-bosses, Item pools
```

两个缺口的后果不同：
- `assignment_priority` 缺失 → 该类别无法被 Step 2（source_categories）和 Step 3（MW 标签匹配）的 priority 遍历命中 → 只有 index 页
- `page_categories` 缺失 → 有 MW 标签的页面在 Step 3 的 fallback 阶段找不到映射 → 流入 `misc`

根据 specs，`page_assigner` 的 `_apply_mw_category_matching` 函数在 Step 3 末尾通过 `page_cat_dir_map` 处理 `page_categories` 映射。映射逻辑是：

```python
top_segment = cat_path.split("/")[0]
if top_segment in cat_name_to_dir:
    page_cat_dir_map[mw_cat_name] = cat_name_to_dir[top_segment]
```

所以 `Runes → Cards` 的 `top_segment` 是 `"Cards"`，而 `"Cards"` 确实在 `cat_name_to_dir` 中（因为 `homepage.categories` 有 `{name: "Cards", dir: "cards"}`），因此可以正确解析。

## Goals / Non-Goals

**Goals:**

1. `assignment_priority` 追加 `Attributes` 和 `Completion Marks`，使其成员页面可被正确分配
2. `taxonomy.page_categories` 追加四个 MW 分类映射，使 31 个 misc 页面进入正确目录
3. 重新 discover 验证配置生效

**Non-Goals:**

1. 不修改 `page_assigner.py` 或其他 pipeline 代码
2. 不修复 Step 2 多 source_categories 匹配 bug（71 页概念页面问题）
3. 不修改除 BOI 外的其他站点策略

## Decisions

### D1: page_categories 映射目标为分类名而非目录名

映射值使用 `homepage.categories[].name` （如 `"Cards"`）而非目录名（如 `"cards"`），因为 `page_cat_dir_map` 的解析逻辑是通过 top_segment 匹配 `cat_name_to_dir` 的 key（即 category name），然后取其 dir。

示例：`Runes → Cards` 比 `Runes → cards` 更正确，因为 `page_categories` 映射的语义是"MW 分类名 → 策略分类名"，目录名由 `cat_name_to_dir` 自动解析。

### D2: 追加位置在 priority 末尾

`Attributes` 和 `Completion Marks` 追加到 `assignment_priority` 末尾（Objects 之后），与它们在 `homepage.categories` 中的位置一致。

## Risks / Migration

| 风险 | 影响 | 缓解策略 |
|------|------|---------|
| page_categories 新增映射误写（如 `Mini-bosses → Boss`） | 解析失败，页面仍留 misc | 验证时检查 `page_cat_dir_map` 构建是否正确 |
| 新 priority 条目与已有 MW 标签冲突 | 某些页面可能从当前目录切换到新目录 | 验证时抽查原目录正常页面的分配是否变化 |
| 配置变更测试不充分 | 合并后影响生产 crawl | 需在 staging 环境运行 discover 验证 |
