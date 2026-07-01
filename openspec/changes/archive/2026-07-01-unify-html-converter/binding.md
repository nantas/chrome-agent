# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `openspec/specs/pipeline-converters/spec.md`, `openspec/specs/pipeline-convert-phase/spec.md`
- `project_page_ref`: `docs/architecture/00-target-architecture.md` (能力目标架构), `docs/adr/0013-four-dimensional-domain-model.md` (4 维领域模型)
- `additional_context_refs`: `docs/architecture/01-overview.md`, `docs/architecture/05-converter-architecture.md`, `docs/plans/4d-architecture-refactor.md`

## Source of Truth

- 行为规范真源：`specs/convert-kernel/spec.md`（本次 change 输出）
- 已有规范：`openspec/specs/pipeline-converters/spec.md`（`HtmlToMarkdownConverter` 行为契约）、`openspec/specs/pipeline-convert-phase/spec.md`（convert phase 流程契约）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `AGENTS.md` §2 Capability Framework — 更新 Convert 能力镜像/变体声明
  - `docs/architecture/01-overview.md` — 移除 `html_to_markdown.py` 和 `fandom_html_to_markdown.py` 引用
  - `docs/architecture/05-converter-architecture.md` — 更新模块清单（删除 fandom 行）、更新 4 维定位小节
  - `openspec/specs/pipeline-converters/spec.md` — 若本次修改影响现有 SHALL 条款
- `writeback_owner`: 本 change 执行者
- `writeback_timing`: 所有 implementation tasks 完成后，verification 通过前

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 回写目标 `openspec/specs/pipeline-converters/spec.md` 仅在本次修改改变了其 SHALL 行为时更新

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
