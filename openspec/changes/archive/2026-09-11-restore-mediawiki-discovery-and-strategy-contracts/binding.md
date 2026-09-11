# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/GOVERNANCE.md`、`openspec/specs/discover-kernel/spec.md`、`openspec/specs/strategy/strategy-lifecycle.md`、`openspec/specs/explore-architecture-gate/spec.md`。
- `project_page_ref`: `docs/architecture/00-target-architecture.md`、`docs/architecture/07-explore-workflow.md`、`docs/architecture/03-strategy-schema.md`。
- `additional_context_refs`: `AGENTS.md`、`CONTEXT.md`、`CONTEXT-MAP.md`、`docs/architecture/08-tech-stack.md`；治理上游为 `repo://orbitos`，本次不回写外仓。

## Source of Truth

- 行为规范真源：本 change `specs/` 内各 capability 的 `spec.md`；实施以 delta specs 为准，归档合并至 `openspec/specs/`。
- 项目页面角色：上下文输入 / 治理展示 / 结果回写；不得替代 spec delta。
- 历史 pipeline discovery 规范与较新 `discover-kernel` 冲突时以 manifest-only 边界为准；实施同步清理冲突表述。

## 回写目标

- `writeback_targets`: `docs/architecture/00-target-architecture.md`、`01-overview.md`、`02-pipeline-flow.md`、`03-strategy-schema.md`、`04-cli-reference.md`、`05-converter-architecture.md`、`07-explore-workflow.md`、`AGENTS.md`、`CONTEXT.md`、`CONTEXT-MAP.md`（仅涉及的能力/接口变化）；`openspec/specs/` 对应规范。
- `writeback_owner`: 本 change 实施者。
- `writeback_timing`: 实施验证通过后、归档前。本轮只生成规划，不回写上述目标。

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准；回写摘要、状态、接口及链接，不复制完整 artifacts。
- 仅本 change 目录在本轮写权限范围内；现有 registry 与站点未提交内容保持原样。
- 后续实施遵循 C9 测试、C10 全局同步、C11 能力注册及 doctor；不迁移历史产物。

## 待确认项

无阻塞项。用户已授权两组修复规划、ns0 空目录 Misc 兜底及排除历史产物；本轮不宣称拥有外部治理系统写权限。
