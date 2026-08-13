# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `docs/adr/0013-four-dimensional-domain-model.md`（4 维模型，镜像等价契约）、`docs/architecture/00-target-architecture.md` §3.1 + §4.3（convert capability 目标声明 + golden snapshot 契约）、`docs/GOVERNANCE.md` §3（change 生命周期）
- `project_page_ref`: 架构审查报告候选 5（standalone.py 未声明第三编排器）+ 候选 3（convert 内核双入口）来源 `/var/folders/.../architecture-review-20260812-161301.html`；`openspec/changes/archive/2026-08-12-arch-review-followups/verification.md`（本 session 已确认 convert 三镜像等价被 `test_convert_equivalence.py` 守护）
- `additional_context_refs`: `scripts/pipeline/standalone.py`（折叠对象）、`scripts/pipeline/cli.py`（5 子命令路由，签名不变）、`scripts/pipeline/pipeline/phases/convert.py::_process_html_page`（CV4 镜像，折叠目标）

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`: `docs/architecture/00-target-architecture.md` §3.1（声明 standalone 为 CV4 薄壳变体 + 补「内核三层接口」声明）；`CONTEXT.md`（若 standalone 相关术语需补）
- `writeback_owner`: 实施 agent
- `writeback_timing`: 验证通过后、归档前

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- cli.py 子命令签名（fetch/reprocess/reconvert 的参数与退出码）SHALL 不变，仅其底层实现改走 CV4

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略（折叠修复 preprocess 漂移属 bug 修复方向，非引入差异）
