# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: Orbitos Spec Standard v0.3（`openspec/specs/` 下现有冻结能力规范）
- `project_page_ref`:
  - `AGENTS.md` §0.5 Development Hard Constraints（Python 3.9+ / ESM / pipeline 调用方式 / 测试框架）
  - `docs/architecture/02-pipeline-flow.md`（五阶段管线 + 缓存机制）
  - `docs/architecture/07-explore-workflow.md`（8-step deep discovery + scaffold 生成）
  - `docs/architecture/08-tech-stack.md`（依赖、语言约定、测试基础设施）
  - `docs/governance-and-capability-plan.md`（output-lifecycle 能力规划）
- `additional_context_refs`:
  - `scripts/pipeline/pipeline/cache.py`（缓存实现真源）
  - `scripts/pipeline/pipeline/phases/fetch.py`（Fetch 阶段实现真源）
  - `scripts/explore/strategy_scaffold_generator.py`（scaffold 生成实现真源）
  - `sites/strategies/developer.nintendo.com/strategy.md`（本次爬取的站点策略产出）

## Source of Truth

- 行为规范真源：`openspec/specs/` 下的能力规范文件
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `docs/architecture/02-pipeline-flow.md`：更新缓存机制章节，增加 chrome-cdp 引擎说明
  - `docs/architecture/07-explore-workflow.md`：更新 scaffold 生成章节，记录 overwrite guard 行为
  - `AGENTS.md` §0.5：若新增 Python 3.9+ 代码需遵守硬性约束，不新增约束则不回写
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: implement 阶段完成后，verification 通过后回写

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用（Orbitos Spec Standard v0.3）
- [x] 已确认项目页引用（AGENTS.md + 架构文档 + 治理计划）
- [x] 已确认回写目标与权限（三份文档 + AGENTS.md 条件性回写）
- [ ] 待确认：是否需要新增 `openspec/specs/cdp-pipeline` 能力规范，或扩展现有 `pipeline-fetch` / `explore-scaffold` 规范
