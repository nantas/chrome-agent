# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/agents-governance/spec.md`（doctor 命令与 skill preflight 契约）
- `project_page_ref`: `docs/playbooks/chrome-agent-global-install.md`（全局安装手册）
- `additional_context_refs`:
  - `AGENTS.md` — 治理规则（工作流路由、引擎选择策略）
  - `skills/chrome-agent/SKILL.md` — workflow skill 契约

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `docs/playbooks/chrome-agent-global-install.md` — 更新安装手册，增加版本新鲜度检查与自动更新说明
  - `skills/chrome-agent/SKILL.md` — 更新 Backend Contract 部分，说明 doctor 返回 `repo_freshness` 字段和重载提示
  - `AGENTS.md` — 如有必要更新 doctor 检查项索引
- `writeback_owner`: 本 change 实施者
- `writeback_timing`: 实施完成后，在 verification 通过后同步

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
