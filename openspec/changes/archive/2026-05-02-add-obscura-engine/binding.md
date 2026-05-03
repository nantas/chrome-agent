# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OpenSpec_Schema_Source/orbitos-change-v1`
- `project_page_ref`: `repo://chrome-agent/AGENTS.md`
- `additional_context_refs`:
  - `repo://chrome-agent` (当前执行仓库)
  - `docs/governance-and-capability-plan.md` (总体规划文档，Phase 4/5 引擎扩展方向)
  - `openspec/specs/engine-registry/spec.md` (引擎注册规范，本 change 将 MODIFIED 新增引擎类型和条目)
  - `openspec/specs/engine-contracts/spec.md` (引擎契约聚合索引，本 change 将 MODIFIED)
  - `openspec/specs/extension-api/spec.md` (引擎扩展接入规范，本 change 遵循其 artifact checklist)
  - `configs/engine-registry.json` (引擎注册索引，本 change 将 MODIFIED 新增条目)
  - `reports/2026-05-02-obscura-benchmark/` (端到端对比测试证据)
  - `openspec/changes/archive/2026-04-28-phase-4-engine-extension-governance/` (前置 Phase 4 change)

## Source of Truth

- 行为规范真源：`openspec/specs/obscura-fetch-contract/spec.md`（本 change 创建）
- 本 change 修改的能力真源：`engine-registry`、`engine-contracts`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据
- `configs/engine-registry.json` 为引擎注册索引，与 contract spec 不一致时以 contract spec 为准

## 回写目标

- `writeback_targets`:
  - `repo://chrome-agent/AGENTS.md`（引擎扩展治理章节需反映新增引擎）
  - `repo://chrome-agent/docs/governance-and-capability-plan.md`（能力全景图追加 obscura-fetch）
  - `repo://chrome-agent/docs/decisions/`（新增决策记录）
- `writeback_owner`: 当前 agent 中的 design 角色
- `writeback_timing`: 本 change 的 `verification` 阶段完成后

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 执行仓库路径使用 `repo://<repo_id>` 语义，不记录宿主机绝对路径
- 项目页面只保留治理入口、最新状态摘要与回写规则；阶段规划与运行细节下沉到子页
- `configs/engine-registry.json` 中 engines 条目的新增需同步更新其对应的 contract spec
- 新增引擎类型 `cdp_lightweight` 需在 `engine-registry` spec 中定义其类型约束

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
- [ ] 已确认 `obscura` 预编译二进制的安装路径与版本固定策略（待 design 阶段确认）
- [ ] 已确认 stealth 模式的启用策略与与 `scrapling-stealthy-fetch` 的 fallback 关系（待 design 阶段确认）
