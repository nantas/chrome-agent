# Design

## Context

Homepage discovery pipeline 的 `_build_homepage_manifest()` 在处理 `parse_homepage()` 返回的分类时，依赖策略配置的 `dir` 映射来决定分类页的输出目录。当首页 gallery 包含策略未配置的分类链接时（如 Isaac wiki 的 "Completion Marks" 和 "Attributes"），`cat_dir` 为空字符串，导致：(1) if 分支不更新 `target_directory`，保留 `assign_pages()` 的错误分配；(2) convert 阶段多个页面写入同一路径时静默覆盖。

相关 spec: `specs/homepage-discovery-category-extraction/spec.md`, `specs/convert-target-conflict-detection/spec.md`, `specs/isaac-strategy-dir-completeness/spec.md`

## Goals / Non-Goals

**Goals:**
- 分类页始终获得非空的 `target_directory`，即使策略未配置 `dir` 映射
- 自动回退到标准化分类名（`cat_name.lower().replace(" ", "-")`）
- convert 阶段 pre-scan 检测 target_path 冲突，防止静默覆盖
- Isaac wiki 策略补全 Completion Marks 和 Attributes 的 dir 映射
- 对已有 `dir` 映射的分类无影响（strategy mapping 优先）

**Non-Goals:**
- 不修改 `parse_homepage()` 的分类识别逻辑（识别正确）
- 不修改 `assign_pages()` 的优先级分配逻辑（按优先级分配是正确行为）

## Decisions

### D1: cat_dir 回退策略 — 自动标准化分类名

**决策**: 当 `strategy_cat_dir` 中无映射且 `cat.get("dir", "")` 也为空时，使用 `cat_name.lower().replace(" ", "-")` 作为回退目录名。

**理由**:
- 分类名本身是结构化的人类可读标识符（如 "Completion Marks"），标准化后可作为合法目录名
- 回退产生可预测的目录名，用户可从日志中看到并决定是否添加显式映射
- 对 Category: 前缀的分类（如 "Category:Modes"），`cat_name` 来自链接文本（"Modes"），不含前缀

**改动位置**: `discovery_homepage.py` `_build_homepage_manifest()` 第 261 行之后，在 `if/else` 分支之前统一解析

### D2: if 分支条件移除

**决策**: 删除 `if cat_dir:` 条件判断，改为无条件赋值 `target_directory = cat_dir`。

**理由**:
- 修复后 `cat_dir` 保证非空，条件判断已无必要
- 保留条件会增加认知负担（为什么有时更新有时不更新？）

### D3: convert 冲突检测 — pre-scan 模式

**决策**: 在 `run_convert()` 的 redirect pre-scan 之后增加 target_path 冲突 pre-scan，使用与 redirect 检测相同的模式（扫描 → 标记 → 主循环检查）。

**理由**:
- 与 redirect 检测模式一致，维护者熟悉
- pre-scan 一次性检测所有冲突，不影响主循环性能
- 冲突页面标记后跳过，避免静默覆盖

**改动位置**: `convert.py` `run_convert()` 第 ~320 行，redirect pre-scan 之后

### D4: 冲突页面结果状态

**决策**: 冲突页面结果使用 `status: "target_conflict"`，计入 `failed_count`。

**理由**: 文件未写入，等同失败。使用专用状态便于日志过滤和统计。

### D5: Isaac 策略补全

**决策**: 在 `strategy.md` 的 `api.homepage.categories` 中添加 Completion Marks 和 Attributes 的 dir 映射。

**理由**:
- 管线自动回退会产生 `completion-marks`（连字符），但 Isaac wiki 现有目录命名用下划线（如 `binding-of-isaac-wiki/items/`）
- 显式映射可控制目录名为 `completion_marks`，与项目风格一致
- 策略补全后，管线走 strategy mapping 分支，不会触发 auto-fallback warning

**改动位置**: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` 第 `api.homepage.categories` 列表

## Risks / Migration

### R1: 自动回退目录名可能与已有目录冲突

**风险**: 自动生成的目录名（如 `attributes`）可能与某个已存在的分类目录重名。
**缓解**: 分类名来自首页 gallery，每个分类名唯一，标准化后目录名也唯一。如果确实冲突，说明两个分类共享同一个标准化名称，这是更根本的命名问题。

### R2: 已有管线输出的兼容性

**风险**: 修复后重新运行管线，新增的 completion-marks/ 和 attributes/ 目录会导致增量输出变化。
**缓解**: 这是预期行为（修复 bug），不是 regression。下次完整运行会生成正确结构。

### R3: 冲突检测的性能影响

**风险**: pre-scan 需要遍历所有 manifest pages 构建 target_path 映射。
**缓解**: 这是 O(n) 操作，与 redirect pre-scan 相同量级。manifest 通常数千条，开销可忽略。
