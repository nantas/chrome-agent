# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认每个 capability spec 的实现范围与边界
  - `page-assignment` (modified): 纯 BOI 策略配置变更——`assignment_priority` 补全 + `page_categories` 新增映射
- [x] 1.2 确认依赖前置条件
  - `page_assigner.py` 已支持 `page_categories` fallback 机制（前 change 2026-05-20 已实现）
  - BOI 策略文件已有 `api.homepage.assignment_priority` 和 `api.taxonomy.page_categories` 字段

## 2. 核心实现任务

### 2.1 assignment_priority 补全

- [x] 2.1.1 在 `assignment_priority` 列表末尾追加 `"Attributes"`
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 位置: Objects 之后，保持与 categories 定义顺序一致
  - 验证: `grep "Attributes" strategy.md` 确认存在

- [x] 2.1.2 在 `assignment_priority` 列表末尾追加 `"Completion Marks"`
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 位置: Attributes 之后
  - 验证: `grep "Completion Marks" strategy.md` 确认存在

### 2.2 page_categories 映射追加

- [x] 2.2.1 追加 `Runes: "Cards"` 到 `taxonomy.page_categories`
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 影响: 17 个符文页（Soul of X）从 misc 分配到 cards/
  - 验证: discover 后 cards/ 增加约 17 页

- [x] 2.2.2 追加 `Special cards: "Cards"` 到 `taxonomy.page_categories`
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 影响: 8 个特殊卡页从 misc 分配到 cards/
  - 验证: discover 后 cards/ 增加约 8 页

- [x] 2.2.3 追加 `Mini-bosses: "Bosses"` 到 `taxonomy.page_categories`
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 影响: 3 个小 Boss 页从 misc 分配到 bosses/
  - 验证: discover 后 bosses/ 增加约 3 页

- [x] 2.2.4 追加 `Item pools: "Items"` 到 `taxonomy.page_categories`
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 影响: 3 个物品池页从 misc 分配到 items/
  - 验证: discover 后 items/ 增加约 3 页

## 3. 收敛与验证准备

- [x] 3.1 准备 C-1 验证证据（assignment_priority 补全）
  - 检查点: `discovery_summary.json` 中 `attributes/` 的 `page_count` > 1（不再只有 index）
  - 检查点: `discovery_summary.json` 中 `completion_marks/` 的 `page_count` > 1

- [x] 3.2 准备 C-2～C-5 验证证据（page_categories 映射）
  - 检查点: `discovery_summary.json` 中 `misc` 的 `count` 减少至少 31（从 164 降至 ~133）
  - 检查点: `cards/` 的 `page_count` 增加约 25（17 Runes + 8 Special cards）
  - 检查点: `bosses/` 的 `page_count` 增加约 3
  - 检查点: 抽查 misc 的 `sample_pages` 不含 Runes/Special cards/Mini-bosses/Item pools 页面

- [x] 3.3 标记需要进入 writeback 的摘要与状态变更
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — `assignment_priority` + `page_categories` 变更

## 4. 验证与回写收敛

- [x] 4.1 基于验证结果生成 verification.md
- [x] 4.2 基于 verification.md 结论生成 writeback.md
- [x] 4.3 执行回写:
  - 更新 BOI 策略文件的 `assignment_priority` 和 `taxonomy.page_categories`
