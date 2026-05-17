# Tasks

## 1. Spec 覆盖与实现准备

- [ ] 1.1 确认 `explore-ki-lifecycle` spec 覆盖全部 6 个 requirement（classification-by-owner, priority-assignment, fix-priority-order, status-tracking, ki-table-in-strategy, separation-from-architecture-gate）
- [ ] 1.2 确认依赖：KI 分类依赖 self-check 输出（S1-S12 检查结果中的失败项）
- [ ] 1.3 确认 strategy.md KI 表 schema 扩展向后兼容（新增 Status/Priority/Owner 列不影响现有解析）

## 2. 核心实现任务

### 2.1 KI 分类引擎

- [ ] 2.1.1 创建 `scripts/explore/ki_lifecycle.py`，提供 `classify_ki(failure: dict) -> dict` 函数
- [ ] 2.1.2 实现分类决策树：根据 self-check failure 的 `check` ID 和 `detail` 内容推断 owner domain
- [ ] 2.1.3 预定义映射表：S1→self_check, S2→pipeline, S3→pipeline, S5→self_check, S6→self_check, S8→pipeline, S9→pipeline, S11→pipeline, S12→pipeline
- [ ] 2.1.4 支持 `fixed_via` 覆盖：当 agent 判定修复归属与默认映射不同时，允许显式指定 owner
- [ ] 2.1.5 验证：对本 session 的 6 个 KI 运行分类，确认 KI-1→self_check, KI-2→self_check, KI-5→pipeline, KI-6→pipeline

### 2.2 优先级分配

- [ ] 2.2.1 实现 `assign_priority(ki: dict) -> str` 函数，返回 P0-P3
- [ ] 2.2.2 P0 判定规则：ID 字段含链接文本/导航文本 → P0；infobox field 值完全错误 → P0
- [ ] 2.2.3 P1 判定规则：可读性降低但不影响数据正确性；self_check 误报
- [ ] 2.2.4 P2 判定规则：检查范围/精度问题，不影响实际输出
- [ ] 2.2.5 P3 判定规则：已在 skip 状态；装饰性问题
- [ ] 2.2.6 验证：本 session 的 KI-1(P2), KI-2(P1), KI-3(P3), KI-4(P3), KI-5(P1), KI-6(P0) 分类正确

### 2.3 KI 状态机

- [ ] 2.3.1 定义状态枚举：`open`, `in_progress`, `resolved`, `wontfix`, `open_systemic`
- [ ] 2.3.2 实现 `transition_status(ki: dict, new_status: str) -> dict`
- [ ] 2.3.3 验证状态转换：open→in_progress→resolved 合法；open→open_systemic 合法；resolved→open 非法

### 2.4 KI 表更新

- [ ] 2.4.1 实现 `generate_ki_table(kis: list[dict]) -> str`，生成 Markdown 表格
- [ ] 2.4.2 表头：`| ID | Issue | Status | Priority | Owner | Impact | Resolution |`
- [ ] 2.4.3 实现 `update_strategy_ki_table(strategy_path: str, kis: list[dict])`，替换策略文件中的 `## Known Issues` 节
- [ ] 2.4.4 验证：对 Isaac Wiki strategy.md 运行，确认产出 7 列表格

### 2.5 迭代控制

- [ ] 2.5.1 在 `ki_lifecycle.py` 中实现 `plan_fix_batches(kis: list[dict]) -> list[list[dict]]`，按优先级分组
- [ ] 2.5.2 返回 `[[P0_ki, ...], [P1_ki, ...], [P2_ki, ...]]` 格式
- [ ] 2.5.3 每个批次标记为一次迭代；最多 3 批次
- [ ] 2.5.4 验证：6 个混合优先级 KI → 3 个批次

## 3. 收敛与验证准备

- [ ] 3.1 对本 session 的 Isaac Wiki explore 结果重新运行 KI Lifecycle（验证分类+优先级+批次）
- [ ] 3.2 确认 commit 08e3ea9 后的 strategy.md KI 表符合新 schema
- [ ] 3.3 确认 KI Lifecycle 在 Architecture Gate 之后执行（Phase 顺序正确）

## 4. 验证与回写收敛

- [ ] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [ ] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [ ] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
