# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`:
  - `repo://orbitos/20_项目/chrome-agent/chrome-agent.md`
- `additional_context_refs`:
  - `repo://chrome-agent`
  - `AGENTS.md`
  - `README.md`
  - `docs/playbooks/chrome-agent-global-install.md`
  - `openspec/specs/global-workflow-skill/spec.md`
  - `openspec/specs/global-capability-cli/spec.md`
  - `openspec/specs/install-chain/spec.md`
  - `openspec/specs/master-plan/spec.md`
  - `openspec/changes/archive/2026-04-29-skill-first-entry-reframe/`

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 本次 change 修改的能力：`global-workflow-skill`、`global-capability-cli`、`install-chain`、`master-plan`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `repo://orbitos/20_项目/chrome-agent/chrome-agent.md`
  - `repo://orbitos/20_项目/chrome-agent/Writeback记录.md`
- `writeback_owner`: 当前 change 执行者
- `writeback_timing`: implementation 与 verification 完成后

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- `skills/chrome-agent/SKILL.md` 的工作流指导必须与 `global-workflow-skill` spec 对齐
- `scripts/chrome-agent-runtime.mjs` 的默认仓库解析顺序必须与 `global-capability-cli` 和 `install-chain` spec 对齐
- 若安装文档、README 与 CLI 实际行为不一致，以已冻结 spec 与验证结果为准

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
