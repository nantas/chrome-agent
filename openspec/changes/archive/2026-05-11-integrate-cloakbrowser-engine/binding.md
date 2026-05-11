# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OpenSpec_Schema_Source/orbitos-change-v1`
- `project_page_ref`: `repo://chrome-agent/AGENTS.md`
- `additional_context_refs`:
  - `repo://chrome-agent` (当前执行仓库)
  - `repo://chrome-agent/openspec/specs/engine-registry/spec.md` (引擎注册规范，本 change 将新增 cloakbrowser-fetch 条目)
  - `repo://chrome-agent/openspec/specs/engine-contracts/spec.md` (引擎契约聚合索引，需更新 escalation chain)
  - `repo://chrome-agent/openspec/specs/obscura-fetch-contract/spec.md` (现有 cdp_lightweight 引擎契约，用于对比评估)
  - `repo://chrome-agent/docs/playbooks/fallback-escalation.md` (需更新以包含 CloakBrowser)
  - `repo://chrome-agent/configs/engine-registry.json` (需新增 cloakbrowser-fetch 条目)
  - `repo://chrome-agent/docs/decisions/2026-05-02-obscura-verification-outcome.md` (obscura 验证结论，影响 CloakBrowser 的定位决策)

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`
- 本 change 将新建 `cloakbrowser-fetch-contract` spec
- 本 change 将修改 `engine-contracts` 和 `engine-registry` spec
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `repo://chrome-agent/openspec/specs/cloakbrowser-fetch-contract/spec.md` (新引擎契约)
  - `repo://chrome-agent/openspec/specs/engine-registry/spec.md` (新增引擎条目)
  - `repo://chrome-agent/openspec/specs/engine-contracts/spec.md` (更新 escalation chain 和错误矩阵)
  - `repo://chrome-agent/docs/playbooks/fallback-escalation.md` (更新升级路径)
  - `repo://chrome-agent/configs/engine-registry.json` (注册引擎)
  - `repo://chrome-agent/AGENTS.md` (更新引擎选择规则)
- `writeback_owner`: 当前 agent 中的 design 角色
- `writeback_timing`: 本 change 的 `tasks` 阶段完成时

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 执行仓库路径使用 `repo://<repo_id>` 语义，不记录宿主机绝对路径

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [ ] 已确认异常处理与冲突策略 — 若测试发现 CloakBrowser 在 Linux Chromium 146 上表现与 macOS 145 有显著差异，需在 design 中注明
