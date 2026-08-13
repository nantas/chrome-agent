# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/adr/0013-four-dimensional-domain-model.md`（4 维模型，镜像等价契约来源）、`docs/GOVERNANCE.md` §3（change 生命周期）、`docs/architecture/00-target-architecture.md` §4.3（golden snapshot 契约）
- `project_page_ref`: `/var/folders/.../architecture-review-20260812-161301.html`（2026-08-12 improve-codebase-architecture 审查报告，候选 1 + 候选 6 的来源）
- `additional_context_refs`: `openspec/changes/archive/2026-08-12-cleanup-post-4d-drift/`（同 session 的删除批 change，记录候选 2/3/7）；git commits `f03376d`、`ac08bba`（候选 1 实现）、`42e2dcc`（候选 6 实现）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据。本 change 为**回溯性记录**——实现已于本 session 直接提交，此处固化记录并确认 spec 合规

## 回写目标

- `writeback_targets`: 无新增回写（候选 1 的 spec 指针已在 cleanup-post-4d-drift 回填到 `test_convert_equivalence.py`；候选 6 为非能力工具脚本，无 spec/架构页受影响）
- `writeback_owner`: 实施 agent
- `writeback_timing`: 验证通过后、归档前

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 候选 6（fanbox）不归属任何能力，无 spec delta，仅在 tasks 中作为实现记录条目存在

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限（本 change 无新增回写，确认无误）
- [x] 已确认异常处理与冲突策略
