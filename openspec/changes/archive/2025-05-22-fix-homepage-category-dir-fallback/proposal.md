# Proposal

## 问题定义

Homepage gallery 包含的策略未配置 `dir` 映射的分类链接（如 "Completion Marks"、"Attributes"），在 discovery pipeline 中被正确识别为分类，但 `_build_homepage_manifest()` 因 `cat_dir` 为空而不更新 `target_directory`，导致这些分类页保留了 `assign_pages()` 按优先级分配的错误目录（如 `items/`）。多个分类页被分配到同一 `target_path`（如 `items/index.md`），convert 阶段 incremental write 静默覆盖，最终索引页内容错误。

### 根因链

1. `parse_homepage()` 正确返回 22 个分类链接（含 Completion Marks、Attributes）
2. 策略 `api.homepage.categories` 只配置了 20 个 dir 映射，漏掉 Completion Marks 和 Attributes
3. 这两个页面同时作为导航链接出现在几乎所有列表页的 `prop=links` 中 → `source_categories` 包含 17 个分类
4. `assign_pages()` 按 `assignment_priority` 把它们分配到 `items/`（Items 排第一）
5. `_build_homepage_manifest()` Step 1：`cat_dir=""` 是 falsy → 不覆盖 `target_directory` → 保留错误的 `items/`
6. `run_convert()` incremental write 不检测 target_path 冲突 → 后处理的 Completion Marks 覆盖 Items 的 `items/index.md`

## 范围边界

### In Scope
- `_build_homepage_manifest()` 中 `cat_dir` 为空时的自动回退逻辑
- `run_convert()` 中 target_path 冲突的 pre-scan 检测与防御
- Isaac wiki 策略文件补全（`strategy.md` 的 `api.homepage.categories` 添加 Completion Marks 和 Attributes 的 dir 映射）
- 新增测试覆盖上述修复点

### Out of Scope
- `parse_homepage()` 逻辑修改 — 分类识别正确，不需要修改
- `assign_pages()` 逻辑修改 — 按优先级分配是正确行为，问题在于后续覆盖
- `assemble.py` 的 index 生成逻辑 — 修复 manifest 后 assemble 自然正确

## Capabilities

### New Capabilities
- `convert-target-conflict-detection`: convert 阶段 pre-scan 检测 target_path 冲突，冲突页面标记跳过并 log error

### Modified Capabilities
- `homepage-discovery-category-extraction`: `_build_homepage_manifest()` Step 1 增加 cat_dir 自动回退逻辑，当策略未配置 dir 映射时标准化分类名为目录路径
- `isaac-strategy-dir-completeness`: Isaac wiki 策略文件补全 `api.homepage.categories` 中缺失的 Completion Marks 和 Attributes dir 映射

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

### 对 Isaac wiki 的影响
- Completion Marks: `items/index.md` → `completion_marks/index.md`（策略显式映射，独立目录）
- Attributes: `items/index.md` → `attributes/index.md`（策略显式映射，独立目录）
- Items 索引页内容恢复正确

### 对其他 wiki 的通用影响
- 任何使用 homepage discovery 且策略 `api.homepage.categories` 不完全覆盖首页 gallery 链接的站点，都会受益于自动回退
- 已有 `dir` 映射的分类不受影响（strategy mapping 优先）
- convert 冲突检测作为防御层，对所有站点生效

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：`specs/homepage-discovery-category-extraction/spec.md`, `docs/architecture/01-overview.md`
