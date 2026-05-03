# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OpenSpec_Schema_Source/orbitos-change-v1`
- `project_page_ref`: `repo://chrome-agent/AGENTS.md`
- `additional_context_refs`:
  - `repo://chrome-agent` (当前执行仓库)
  - `openspec/changes/add-obscura-engine/` (前置 change，obscura-fetch 引擎接入)
  - `openspec/specs/obscura-fetch-contract/spec.md` (obscura-fetch 引擎契约，本 change 将验证其 stealth 和 smoke-check 边界)
  - `openspec/specs/engine-registry/spec.md` (引擎注册规范，本 change 不修改但验证结果可能影响 status)
  - `reports/2026-05-02-obscura-smoke-check.md` (已完成的基本 smoke-check)
  - `/tmp/obscura-benchmark/` (端到端初始 benchmark，含 stealth 初步数据)

## Source of Truth

- 行为规范真源：`openspec/specs/obscura-fetch-contract/spec.md`（验证目标的契约依据）
- 本 change 是 pure verification change，不创建/修改任何 capability spec
- 验证结论将回写到 `reports/` 目录和决策记录

## 回写目标

- `writeback_targets`:
  - `repo://chrome-agent/reports/`（验证报告输出）
  - `repo://chrome-agent/docs/decisions/`（若验证结论影响 spec 或 status，追加决策记录）
  - `repo://chrome-agent/openspec/specs/obscura-fetch-contract/spec.md`（若 stealth 验证结果需修正 spec 中的 stealth 描述边界）
- `writeback_owner`: 当前 agent 中的 design 角色
- `writeback_timing`: 本 change 的 `verification` 阶段完成后

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 执行仓库路径使用 `repo://<repo_id>` 语义，不记录宿主机绝对路径

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [ ] 已确认异常处理与冲突策略 — 若验证发现 Obscura 存在严重限制，可能触发 spec 修正 change
