# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 capability spec 的实现范围与边界
  - `page-assignment` (modified): `unique-source-category-assignment` + `mw-category-tiebreaker-preserved` + `assignment-priority-gap-fill`
- [x] 1.2 确认依赖前置条件
  - `fix-pipeline-assignment-and-output` 已归档（S-1/S-2 修复已合并）
  - `page_assigner.py` 当前代码中 `_apply_source_category_assignments` 和 `_apply_mw_category_matching` 函数已就位
  - MW categories 批量查询在 `_apply_mw_category_matching` 入口执行，deferred pages 的 MW 数据将自动被查询

## 2. 核心实现任务

### 2.1 page_assigner Step 2 多匹配延后 (spec: page-assignment → unique-source-category-assignment)

- [x] 2.1.1 修改 `_apply_source_category_assignments()` 匹配逻辑
  - 文件: `scripts/pipeline/pipeline/page_assigner.py`
  - 当前行为: 遍历 `assignment_priority`，首个匹配即分配
  - 修改为: 先收集所有匹配的 `assignment_priority` 条目，仅当 `len(matching) == 1` 时分配；`len(matching) > 1` 时不分配（延后到 Step 3）
  - 零匹配页面不分配（与当前行为一致，延后到 Step 3）
  - 验证: 单元测试确认三种场景
    - 单一 source_categories 匹配 → 立即分配 `"source_category_match"`
    - 多个 source_categories 匹配 → 不分配，`assignment_method` 保持 `None`
    - 零 source_categories 匹配 → 不分配，延后到 Step 3

- [x] 2.1.2 确认 deferred pages 在 Step 3 的正确处理
  - 验证: 被延后的页面（多匹配）在 `_apply_mw_category_matching` 中被正确处理
  - 检查点: MW 批量查询覆盖这些页面（它们现在在 `unassigned` 列表中）
  - 检查点: 不修改 `_apply_mw_category_matching` 逻辑（deferred pages 与零匹配页面同等对待）

### 2.2 BOI 策略 assignment_priority 补全 (spec: page-assignment → assignment-priority-gap-fill)

- [x] 2.2.1 添加 `Attributes` 和 `Completion Marks` 到 `assignment_priority`
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 在 `assignment_priority` 列表末尾追加：
    ```yaml
    - "Attributes"
    - "Completion Marks"
    ```
  - 验证: YAML 语法正确，`assignment_priority` 包含 22 个条目（与 `homepage.categories` 数量一致）

## 3. 收敛与验证准备

- [x] 3.1 准备 Q1 验证证据
  - 检查点: 对 BOI 站点运行 homepage discovery → manifest 中楼层页面（Basement, Cellar, Caves 等）分配到 `chapters/` 目录
  - 检查点: `assignment_method` 为 `"mw_category_match"`（而非 `"source_category_match"`）
  - 检查点: `chapters/` 目录包含至少 25 个楼层页面（而非 ~2 个）
  - 检查点: 实际 Boss 页面（Monstro, Chub 等）仍正确分配到 `bosses/`

- [x] 3.2 准备 Q2 验证证据
  - 检查点: `assignment_priority` 包含 `Attributes` 和 `Completion Marks`
  - 检查点: 属性页面分配到 `attributes/` 目录
  - 检查点: 完成标记页面分配到 `completion_marks/` 目录

- [x] 3.3 回归检查
  - 检查点: non-BOI 站点测试（如 Balatro 或 Vampire Crawlers）— 确认单一匹配行为不变
  - 检查点: misc 目录页面数不异常增多

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成 writeback.md
- [x] 4.3 执行 writeback.md 中定义的回写目标:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — `assignment_priority` 补全
