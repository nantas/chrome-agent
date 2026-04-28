# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OrbitOS_Spec_Standard/OrbitOS_Spec_Standard_v0.3.md`
- `project_page_ref`: `repo://orbitos/20_项目/chrome-agent/chrome-agent.md`
- `additional_context_refs`:
  - `repo://chrome-agent`
  - `docs/governance-and-capability-plan.md`
  - `AGENTS.md`
  - `openspec/specs/agents-governance/spec.md`
  - `openspec/specs/master-plan/spec.md`
  - `openspec/specs/site-strategy-schema/spec.md`
  - `openspec/specs/engine-contracts/spec.md`
  - `openspec/specs/engine-registry/spec.md`
  - `openspec/specs/scrapling-cli-environment/spec.md`

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`
  - 本 change 创建的能力：`global-capability-cli`、`install-chain`、`output-lifecycle`、`strategy-guided-crawl`
  - 本 change 修改的能力：`agents-governance`、`master-plan`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据
- 全局 launcher、repo-registry 映射、环境变量 fallback 都服务于执行入口，不替代仓库内 specs 的行为定义

## 回写目标

- `writeback_targets`:
  - `repo://orbitos/20_项目/chrome-agent/chrome-agent.md`
  - `repo://orbitos/20_项目/chrome-agent/Writeback记录.md`
- `writeback_owner`: 当前 change 执行者
- `writeback_timing`: implementation 与 verification 完成后

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- `repo://chrome-agent` 的解析以全局 `repo-registry` 为主，环境变量 fallback 只用于运行时定位，不改变规范真源
- 若全局 CLI、仓库 AGENTS 路由规则、或站点策略行为发生冲突，以仓库内 spec 与 AGENTS 约束为准
- 删除旧 global skill 时，只迁移入口契约，不迁移其 prompt 文本为新的规范真源

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
