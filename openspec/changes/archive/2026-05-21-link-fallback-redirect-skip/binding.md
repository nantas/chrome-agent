# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `orbitos` (OpenSpec Standard v0.3)
- `project_page_ref`:
  - `openspec/specs/pipeline/pipeline-conversion.md` (fix-links-in-directory requirement)
  - `openspec/specs/pipeline-converters/spec.md` (link fixer behavior)
  - `openspec/specs/mediawiki/api.md` (LinkResolver interface)
  - `docs/architecture/06-engine-selection.md` (engine fallback patterns)
- `additional_context_refs`:
  - `scripts/pipeline/strategies/link_resolver.py` (ExactTitleLinkResolver, ShortNameLinkResolver)
  - `scripts/pipeline/converters/link_fixer.py` (post-convert link fixing)
  - `scripts/pipeline/converters/fandom_html_to_markdown.py` (参考：Fandom 已实现 wiki URL fallback)
  - `scripts/pipeline/pipeline/phases/convert.py` (convert phase entry point)

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `openspec/specs/pipeline/pipeline-conversion.md` — 新增 link-resolver-fallback-to-wiki-url scenario
  - `openspec/specs/pipeline-converters/spec.md` — 新增 redirect-detection-and-skip requirement
  - `openspec/specs/mediawiki/api.md` — 更新 LinkResolver resolve() fallback 语义
- `writeback_owner`: change author
- `writeback_timing`: verification 通过后，apply 阶段最后一步

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [ ] 已确认异常处理与冲突策略 — redirect 页面是否应保留为占位文件（含指向目标的链接）还是完全跳过不生成文件
