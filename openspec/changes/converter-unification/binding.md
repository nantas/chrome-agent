# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/pipeline-converters/spec.md` — pipeline 转换器行为真源（含 HtmlToMarkdownConverter）
  - `openspec/specs/explore-architecture-gate/spec.md` — Architecture Gate 校验范围真源
  - `openspec/specs/markdown-conversion-pipeline/spec.md` — Markdown 转换管线规范
- `project_page_ref`:
  - `openspec/changes/fix-pipeline-quality-gaps/` — 前一个 change，当前转换器双路径问题的来源与已修复部分
  - `scripts/mediawiki-api-extract/converters/html_to_markdown.py` — pipeline 路径转换器（统一目标）
  - `scripts/explore/sample_converter.py` — explore 路径转换器（被统一方）
- `additional_context_refs`:
  - `docs/playbooks/evidence-collection.md` — 证据收集方法

## Source of Truth

- 行为规范真源：本 change 的 `specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；前一个 change 的验证报告（verification.md）提供了两条路径的质量对比证据

## 回写目标

- `writeback_targets`:
  - `scripts/mediawiki-api-extract/converters/html_to_markdown.py` — 修改为统一转换器基础
  - `scripts/explore/sample_converter.py` — 转换为委托给 HtmlToMarkdownConverter
  - `scripts/explore/architecture_gate.py` — `_PIPELINE_FILES` 缩减为单一文件
- `writeback_owner`: chrome-agent 仓库维护者
- `writeback_timing`: verification 完成后，writeback 阶段执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 前一个 change（fix-pipeline-quality-gaps）的 Architecture Gate 双文件校验在本 change 完成后需更新为单文件

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
