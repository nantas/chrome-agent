# Tasks

## 1. Spec 覆盖与实现准备

- [ ] 1.1 确认 `explore-architecture-gate` spec 覆盖全部 5 个 requirement（gate-position, strategy-to-pipeline-validation, pipeline-to-strategy-audit, gate-must-pass-before-confirmation, gate-output-format）
- [ ] 1.2 确认 pipeline 源码路径：`scripts/explore/sample_converter.py` 中的 `_apply_extraction()` 和 `_extract_infobox()` 为检查目标
- [ ] 1.3 确认 agent audit checklist 5 项覆盖 commit 55ac8d4 的所有违规类型

## 2. 核心实现任务

### 2.1 程序化校验：strategy-to-pipeline

- [ ] 2.1.1 创建 `scripts/explore/architecture_gate.py`，提供 `validate(samples, raw_markdowns, extraction_rules, sample_type, wiki_domain, skip_patterns=None)` 入口
- [ ] 2.1.2 实现 `_detect_dead_config(strategy: dict, pipeline_path: str) -> list[str]`：读取 strategy extraction 块的所有顶层 key，在 pipeline 源码中搜索对应的 `.get()` / `[]` 消费模式
- [ ] 2.1.3 实现 `cleanup` 操作的枚举校验：检查 strategy 中列出的每个 operation name 在 pipeline 源码中存在
- [ ] 2.1.4 验证：构造含死配置的 strategy dict（如 `wiki_gg_specific` 字段），确认检测器正确识别

### 2.2 Agent 审计清单：pipeline-to-strategy

- [ ] 2.2.1 定义审计规则函数 `_audit_pipeline(pipeline_path: str, strategy: dict) -> list[dict]`，返回 violation 列表
- [ ] 2.2.2 检查项 A：硬编码 HTML 选择器 — `grep` pipeline 源码中类选择器/ID选择器，与 strategy 的 `infobox.selector`、`cleanup_selectors` 比对
- [ ] 2.2.3 检查项 B：硬编码 CSS 类名 — 同上，聚焦类名字符串
- [ ] 2.2.4 检查项 C：硬编码站点域名 — `grep` 域名模式，与 `image_handling.base_url` 比对
- [ ] 2.2.5 检查项 D：硬编码文件名模式 — `grep` 特定图片/文件模式，与 `image_filtering.skip_patterns` 比对
- [ ] 2.2.6 检查项 E：无条件站点操作 — 检查 YouTube/lazyload/URL 转换是否有 `if cfg["enabled"]:` 守卫
- [ ] 2.2.7 验证：对 commit 55ac8d4 版本的 sample_converter.py 运行审计，确认检测到全部硬编码

### 2.3 Gate 输出与集成

- [ ] 2.3.1 `validate()` 函数返回 `{ status, strategy_to_pipeline: {status, dead_config[]}, pipeline_to_strategy: {status, violations[]} }` 格式
- [ ] 2.3.2 在 `scripts/explore/main.py` 的 Phase 6/7 之间插入 Gate 调用：self-check 完成后、用户确认前
- [ ] 2.3.3 Gate 失败时阻止后续执行，输出 violation 列表并返回 `partial_success` 给 CLI

## 3. 收敛与验证准备

- [ ] 3.1 使用 commit 55ac8d4 的 strategy + pipeline 快照作为回归测试用例
- [ ] 3.2 使用 commit 08e3ea9（修复后）验证 Gate 通过
- [ ] 3.3 使用 `bindingofisaacrebirth.wiki.gg` 的完整 pipeline 运行 Gate 确认生产就绪

## 4. 验证与回写收敛

- [ ] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [ ] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [ ] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
