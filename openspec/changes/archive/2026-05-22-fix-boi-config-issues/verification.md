# Verification

## Change: fix-boi-config-issues
## Schema: orbitos-change-v1
## Date: 2026-05-22

## Verification Method

配置变更验证：检查 BOI 策略文件 `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` 的 YAML frontmatter 是否按 spec 要求正确修改。

## C-1: assignment_priority 补全

### 检查项: Attributes 和 Completion Marks 存在于 assignment_priority

**结果: ✓ PASS**

```
assignment_priority 列表末尾包含:
  - "Attributes"
  - "Completion Marks"
```

- `"Attributes"` 位于列表第 21 位（Objects 之后）
- `"Completion Marks"` 位于列表第 22 位（末尾）
- 两个条目与 `homepage.categories` 定义中的对应条目匹配

### 检查项: category_page_types 不影响新条目

**结果: ✓ PASS**

`category_page_types` 仅定义了 `Modes` 和 `Objects`，`Attributes` 和 `Completion Marks` 不受其影响，将使用默认的 list_page 行为。

## C-2: Runes → Cards 映射

### 检查项: page_categories 包含 Runes: "Cards"

**结果: ✓ PASS**

```yaml
page_categories:
  ...
  Runes: "Cards"
```

**解析验证:**
- `top_segment = "Cards".split("/")[0] = "Cards"`
- `cat_name_to_dir` 包含 `"Cards" → "cards"`（来自 `homepage.categories` 中 `{name: "Cards", dir: "cards"}`）
- `page_cat_dir_map["Runes"] = "cards"` ✓

**预期影响:** 17 个符文页（Soul of Isaac 等）从 misc 分配到 cards/

## C-3: Special cards → Cards 映射

### 检查项: page_categories 包含 Special cards: "Cards"

**结果: ✓ PASS**

```yaml
page_categories:
  ...
  Special cards: "Cards"
```

**解析验证:**
- `top_segment = "Cards"` → `cat_name_to_dir["Cards"] = "cards"` ✓

**预期影响:** 8 个特殊卡页从 misc 分配到 cards/

## C-4: Mini-bosses → Bosses 映射

### 检查项: page_categories 包含 Mini-bosses: "Bosses"

**结果: ✓ PASS**

```yaml
page_categories:
  ...
  Mini-bosses: "Bosses"
```

**解析验证:**
- `top_segment = "Bosses"` → `cat_name_to_dir["Bosses"] = "bosses"` ✓

**预期影响:** 3 个小 Boss 页从 misc 分配到 bosses/

## C-5: Item pools → Items 映射

### 检查项: page_categories 包含 Item pools: "Items"

**结果: ✓ PASS**

```yaml
page_categories:
  ...
  Item pools: "Items"
```

**解析验证:**
- `top_segment = "Items"` → `cat_name_to_dir["Items"] = "items"` ✓

**预期影响:** 3 个物品池页从 misc 分配到 items/

## Backward Compatibility

**结果: ✓ PASS**

- `assignment_priority` 仅在末尾追加，不改变已有条目顺序
- `page_categories` 新增 2 个映射（Special cards、Mini-bosses），修正 2 个映射（Runes、Item pools）
- 所有新增/修正映射的 MW 分类在原配置中要么映射到无效目标（Runes→Runes、Item pools→Item_pools），要么不存在（Special cards、Mini-bosses），因此不会影响已有正确分配的页面

## Regression Risk

**风险: 低**

- `Runes: "Runes"` 原映射到 `"Runes"` top segment，但 `cat_name_to_dir` 中不存在 `"Runes"` key（homepage.categories 无此条目），因此原映射实际上无效 → 修改为 `"Cards"` 是修复而非行为变更
- `Item pools: "Item_pools"` 原映射到 `"Item_pools"` top segment，同样在 `cat_name_to_dir` 中无对应 key → 修改为 `"Items"` 同样是修复

## Summary

| Check | Status |
|-------|--------|
| C-1: assignment_priority 补全 | ✓ PASS |
| C-2: Runes → Cards | ✓ PASS |
| C-3: Special cards → Cards | ✓ PASS |
| C-4: Mini-bosses → Bosses | ✓ PASS |
| C-5: Item pools → Items | ✓ PASS |
| Backward compatibility | ✓ PASS |
| Regression risk | LOW |

**Overall: ALL CHECKS PASSED**

配置变更已完成，需要运行 discover 命令进行实际端到端验证以确认 31 个页面从 misc 重新分配到正确目录。
