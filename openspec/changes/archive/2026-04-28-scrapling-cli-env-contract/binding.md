# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `20_项目/chrome-agent/chrome-agent.md`
- `additional_context_refs`:
  - `repo://chrome-agent` (当前执行仓库)
  - `AGENTS.md` (工作流治理入口，本 change 将 MODIFIED 对应治理行为)
  - `docs/setup/scrapling-first-workflow.md` (当前 Scrapling 安装与 MCP 配置说明，含宿主机绝对路径示例)
  - `.codex/config.toml` (项目级 Codex MCP 配置，当前含 Scrapling 绝对路径)
  - `opencode.json` (项目级 Opencode MCP 配置，当前含 Scrapling 绝对路径)
  - `openspec/specs/agents-governance/spec.md` (工作流治理规范，本 change 将 MODIFIED)
  - `openspec/specs/scrapling-first-browser-workflow/spec.md` (Scrapling-first 运行与 setup 规范，本 change 将 MODIFIED)
  - `docs/setup/chrome-tooling.md` (已有环境变量与安装确认交互模式参考)

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`
  - 本 change 创建的能力：`scrapling-cli-environment`
  - 本 change 修改的能力：`agents-governance`、`scrapling-first-browser-workflow`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `repo://orbitos` 下的项目页面：`20_项目/chrome-agent/chrome-agent.md`
  - Writeback 明细页面：`20_项目/chrome-agent/Writeback记录.md`
- `writeback_owner`: `spec-ops` 或当前 agent 中的 design 角色
- `writeback_timing`: 本 change 的 `verification` 阶段完成后

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 受 git 跟踪的仓库文件不得再写入宿主机用户专属绝对路径；仓库内需以环境变量表达可配置路径
- 用户 shell 配置写入属于显式确认动作；实现阶段在未获确认前不得自动改写 `/Users/nantas-agent/.zshenv`

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
