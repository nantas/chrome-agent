# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `20_项目/chrome-agent/chrome-agent.md`
- `additional_context_refs`:
  - `repo://chrome-agent` (当前执行仓库)
  - `docs/governance-and-capability-plan.md` (总体规划文档，Phase 4 定义来源)
  - `openspec/changes/archive/2026-04-28-phase-1-governance-foundation/` (前置 Phase 1 change，治理基础)
  - `openspec/changes/archive/2026-04-28-phase-2-contract-freeze/` (前置 Phase 2 change，契约冻结)
  - `openspec/changes/archive/2026-04-28-phase-3-strategy-standardization/` (前置 Phase 3 change，策略库标准化)
  - `openspec/specs/capability-contracts/spec.md` (契约元模型，Phase 1 产出)
  - `openspec/specs/agents-governance/spec.md` (治理层规范，Phase 1 产出)
  - `openspec/specs/engine-contracts/spec.md` (引擎契约聚合索引，Phase 2 产出，本 change 将 MODIFIED)
  - `openspec/specs/anti-crawl-schema/spec.md` (反爬策略 schema，Phase 3 产出，本 change 将 MODIFIED)
  - `openspec/specs/site-strategy-schema/spec.md` (站点策略 schema，Phase 3 产出，本 change 将 MODIFIED)
  - `sites/anti-crawl/` 下 5 个反爬策略文件 (本 change 将修改 engine_sequence → engine_priority)
  - `sites/strategies/` 下 4 个站点策略文件 (可选 engine_preference 字段新增)

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`
  - 本 change 创建的能力：`engine-registry`、`extension-api`、`scrapling-bulk-fetch-contract`
  - 本 change 修改的能力：`engine-contracts`、`anti-crawl-schema`、`site-strategy-schema`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据
- `configs/engine-registry.json` 为引擎注册索引，与各引擎 contract spec 不一致时以 contract spec 为准

## 回写目标

- `writeback_targets`:
  - `repo://orbitos` 下的项目页面：`20_项目/chrome-agent/chrome-agent.md`
  - Writeback 明细页面：`20_项目/chrome-agent/Writeback记录.md`
- `writeback_owner`: `spec-ops` 或当前 agent 中的 design 角色
- `writeback_timing`: 本 change 的 `verification` 阶段完成后

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 执行仓库路径使用 `repo://<repo_id>` 语义，不记录宿主机绝对路径
- 项目页面只保留治理入口、最新状态摘要与回写规则；阶段规划与运行细节下沉到子页
- `configs/engine-registry.json` 中 engines 条目的新增/修改需同步更新其对应的 contract spec
- `anti-crawl-schema` 和 `site-strategy-schema` 的 MODIFIED 变更需保持与 Phase 3 已归档策略文件的向后兼容

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
