# Proposal

## 问题定义

对 `bindingofisaacrebirth.wiki.gg` 的 homepage-driven crawl 完成后的目录清单暴露了两个分配缺陷：

### Q1: 列表页交叉链接导致分类错误

`page_assigner` 的 Step 2（`_apply_source_category_assignments`）按 `assignment_priority` 顺序匹配页面的 `source_categories`。但 MediaWiki 列表页之间存在大量交叉链接（导航模板、侧边栏、归类表格等），导致同一页面出现在多个列表页的 `prop=links` 结果中。

具体案例：

| 页面 | source_categories (来自列表页链接) | 应属目录 |
|------|-----------------------------------|---------|
| Basement | `["Bosses", "Chapters"]` | chapters/ |
| Caves | `["Bosses", "Chapters"]` | chapters/ |
| Cellar | `["Bosses", "Chapters"]` | chapters/ |

所有楼层页面同时出现在 Bosses 列表页和 Chapters 列表页的链接中。由于 "Bosses" 在 `assignment_priority` 排第 2 位、"Chapters" 排第 8 位，Step 2 将它们分配到了 `bosses/`。

这是 S-1 修复的前次 change（`fix-pipeline-assignment-and-output`）引入的副作用——扩展 `list_page` 匹配后，交叉链接导致的噪声源也进入了匹配范围。

### Q2: `assignment_priority` 缺失条目

策略中定义了 22 个 `homepage.categories` 条目，但 `assignment_priority` 只包含 20 个。缺失的：

- `Attributes` (dir: `attributes`)
- `Completion Marks` (dir: `completion_marks`)

由于 Step 2 和 Step 3 都仅遍历 `assignment_priority`，这两个类别的页面无法通过任何分配步骤匹配。只有它们自己的 `index.md`（由 `_build_homepage_manifest` 硬编码创建）出现在对应目录，所有成员页面流向了更高优先级的类别或 `misc`。

## 范围边界

### 范围内

- **Q1 修复**: 修改 `page_assigner._apply_source_category_assignments()` 逻辑——当页面匹配到多个 `source_categories` 时，延后到 Step 3（MW category 匹配）进行终裁，而非直接按优先级顺序分配。
- **Q2 修复**: 在 BOI 策略的 `assignment_priority` 中添加 `Attributes` 和 `Completion Marks`。

### 范围外

- 不修改 `_apply_mw_category_matching()` 的匹配逻辑
- 不新增策略字段（`exclude_links`、`link_noise_threshold` 等）
- 不修改 `discovery_homepage.py` 的 `source_categories` 生成逻辑
- 不修改 CLI、Convert、Resume 等 phase
- 不涉及其他站点策略的修改

## Capabilities

### New Capabilities

_无_

### Modified Capabilities

- `page-assignment`: Step 2 在页面匹配到**唯一** `source_categories` 时才立即分配；匹配到**多个**时延后到 Step 3（MW category 匹配）进行终裁。此修改使 MW categories（如 `Category:Stages`）成为分类冲突时的可信终裁信号。

## Capabilities 待确认项

- [x] 能力清单已确认——只修改 `page-assignment`，不涉及其他 capability

## Impact

| 影响维度 | 详情 |
|---------|------|
| page_assigner 行为 | Step 2 从"第一匹配即分配"改为"唯一匹配才分配，多匹配延后到 Step 3" |
| 策略配置 | BOI 策略 `assignment_priority` 新增 `Attributes` 和 `Completion Marks` |
| 向后兼容 | 其他站点策略不受影响：对于 `source_categories` 唯一匹配的页面，行为不变；多匹配页面原本的分配行为也属于噪声（交叉链接导致），改为 MW 终裁是更合理的行为 |
| 性能 | 多匹配页面会触发 Step 3 的 MW category 查询（原本这类页面已被分配，绕过 MW 查询）。但实际上多匹配页面在 Step 2 已通过 `prop=categories` 查询了 MW 标签——`assign_pages()` 中 MW 查询在所有 Step 之前批量执行。因此无性能退化。 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `openspec/specs/page-assignment/` — 页面分配行为真源
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — BOI 策略配置回写目标
  - `scripts/pipeline/pipeline/page_assigner.py` — 实现文件
