# Proposal

## 问题定义

对 `bindingofisaacrebirth.wiki.gg` 的 homepage discovery 产出的 manifest 分析表明，BOI 策略配置有 5 个缺口，导致部分页面被错误归入 `misc` 或其他目录：

| # | 问题 | 影响 | 严重度 |
|---|------|------|--------|
| C-1 | `Attributes`、`Completion Marks` 未加入 `assignment_priority` | 两个类别只有 index 页（各 1 页），其真实成员页面（Damage、Health 等）被 MW 分类分发到其他目录 | P1 |
| C-2 | `page_categories` 缺 `Runes` → `Cards` 映射 | 17 个符文页（Soul of Isaac、Soul of Magdalene 等）流入 `misc` | P1 |
| C-3 | `page_categories` 缺 `Special cards` → `Cards` 映射 | 8 个特殊卡页（Chaos Card、Credit Card、Holy Card 等）流入 `misc` | P2 |
| C-4 | `page_categories` 缺 `Mini-bosses` → `Bosses` 映射 | 3 个小 Boss 页（Krampus、Ultra Pride、Angel）流入 `misc` | P2 |
| C-5 | `page_categories` 缺 `Item pools` → `Items` 映射 | 3 个物品池页（Angel Room、Boss、Shop）流入 `misc` | P3 |

总计：**31 个页面** 因为配置缺失而被误归到 `misc`。

## 范围边界

**范围内：**
- BOI 策略 `assignment_priority` 追加 `Attributes`、`Completion Marks`
- BOI 策略 `taxonomy.page_categories` 追加四个 MW 分类 → 目录映射（Runes、Special cards、Mini-bosses、Item pools）
- 验证：重新 discover 后确认上述页面分配到正确目录

**范围外：**
- 不修改 `page_assigner.py` 或其他 pipeline 代码（纯配置变更）
- 不修复 Step 2 的 71 页未匹配 bug（需要 pipeline 代码调试，属于独立 change）
- 不修改其他站点策略

## Capabilities

### New Capabilities

_无（纯配置变更，不新增 capability）_

### Modified Capabilities

- `page-assignment`: BOI 策略配置补全——`assignment_priority` 补全缺失条目；`taxonomy.page_categories` 新增四个 MW 分类 → 目录映射

## Capabilities 待确认项

- [x] 能力清单已与用户确认 — 配置变更，仅涉及 `page-assignment` capability 的 BOI 策略实例

## Impact

| 影响维度 | 详情 |
|---------|------|
| BOI 策略配置 | `assignment_priority` 增加 2 条；`page_categories` 增加 4 条 |
| 输出目录变化 | `attributes/`、`completion_marks/` 将获得其真实成员页面；`misc/` 减少 31 页 |
| 向后兼容 | 无冲突——仅增加新的映射条目，不修改已有映射 |
| 文件变更 | 仅修改 `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `openspec/specs/page-assignment/` — 页面分配行为规范真源
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — 唯一配置修改目标
