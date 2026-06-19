# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos` → `99_系统/Harness/OpenSpec_Schema_Source`（`orbitos-change-v1` schema）
- `project_page_ref`:
  - `docs/architecture/04-cli-reference.md`（`fetch` 命令行为与 `runFetch()` 实现）
  - `docs/architecture/06-engine-selection.md`（`scrapling-get` 引擎与提取阶段）
  - `docs/architecture/03-strategy-schema.md`（`extraction.selectors` frontmatter 字段定义）
- `additional_context_refs`:
  - `sites/strategies/posthog.com/strategy.md`（KI-1 触发本次 change，含选择器验证证据）
  - `outputs/posthog-20260619-175346/DELIVERY-REPORT.md`（选择器演进与 S1-S12 质量检测结论）

## Source of Truth

- 行为规范真源：`specs/fetch-strategy-selector/spec.md`（本次 change 新增 capability）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；`docs/architecture/*` 与 `sites/strategies/*/strategy.md` 的回写仅为结论同步与状态标注

## 回写目标

- `writeback_targets`:
  1. `sites/strategies/posthog.com/strategy.md` — KI-1 状态 `open` → `resolved`，补充修复 commit 引用
  2. `docs/architecture/04-cli-reference.md` — `fetch` 命令行为说明中补充"策略 `extraction.selectors.content` 透传至 scrapling `-s`"
  3. `docs/architecture/06-engine-selection.md` — `scrapling-get` 提取阶段说明中补充"优先使用策略选择器，缺失时回退 `--ai-targeted`"
- `writeback_owner`: chrome-agent 维护者（本 change 实施者）
- `writeback_timing`: `tasks.md` 实施完成 + `verification.md` 通过后，于 `writeback.md` 阶段一次性同步

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- `extraction.selectors.content` 的字段权威仍由 `docs/architecture/03-strategy-schema.md` 定义；本次 change 不修改字段语义，仅修改 pipeline 对该字段的消费行为
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用（`repo://orbitos` → `orbitos-change-v1`）
- [x] 已确认项目页引用（`04-cli-reference.md`、`06-engine-selection.md`、`03-strategy-schema.md`）
- [x] 已确认回写目标与权限（strategy.md KI-1 + 两份 architecture 文档，均在本仓库内）
- [ ] 已确认异常处理与冲突策略（待 `design.md` 确认：当策略同时声明 `selectors.content` 与默认 `ai-targeted` 行为时的优先级与回退链；待 `verification.md` 确认回归测试覆盖范围）
