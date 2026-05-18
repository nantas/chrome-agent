# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/homepage-driven-discovery/spec.md` — Phase 0 首页驱动发现行为真源
  - `openspec/specs/mediawiki-api-extraction-pipeline/spec.md` — Pipeline 编排与 phase dispatch 行为真源
  - `openspec/specs/pipeline-converters/spec.md` — HTML→Markdown 转换器行为真源
  - `openspec/specs/explore-architecture-gate/spec.md` — Architecture Gate 校验范围真源
  - `openspec/specs/pipeline-strategy-schema/spec.md` — 策略 schema 真源
  - `openspec/specs/page-assignment/spec.md` — 页面分配行为真源
  - `openspec/specs/pipeline-cli-entry/spec.md` — CLI 入口与参数定义真源
- `project_page_ref`:
  - `outputs/handoffs/20260518-crawl-bindingofisaacrebirth-wiki-gg/handoff.md` — 问题汇报文档，本次 change 的问题来源
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — BOI 站点策略，本次 change 的验证目标
- `additional_context_refs`:
  - `openspec/changes/archive/2026-05-18-homepage-driven-crawl/` — Phase 0 原始实现上下文
  - `openspec/changes/archive/2026-05-18-pipeline-exception-handling-and-category-exclusion/` — exclude_categories 实现上下文

## Source of Truth

- 行为规范真源：本 change 的 `specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据；handoff 文档的 4 个 Issue（P-line/S-line）作为问题清单输入，所有行为决策以 specs/ 为准

## 回写目标

- `writeback_targets`:
  - `outputs/handoffs/20260518-crawl-bindingofisaacrebirth-wiki-gg/handoff.md` — 追加修复状态章节，标记 Issue 1-4 解决状态
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — 补全 page_categories、提升 exclude_categories、标注 discovery 策略
- `writeback_owner`: chrome-agent 仓库维护者
- `writeback_timing`: verification 完成后，writeback 阶段执行

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- handoff 中的 Issue 编号（Issue 1-4）在回写时映射到 spec requirement 名称
- 策略文件的 schema 变更以 spec delta 为权威格式

## 待确认项

- [x] 已确认标准页引用
- [x] 已确认项目页引用
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略
