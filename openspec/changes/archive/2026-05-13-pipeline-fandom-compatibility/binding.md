# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: repo://orbitos (`openspec/specs/orbitos-spec-standard-v1/spec.md`)
- `project_page_ref`:
  - `chrome-agent` 仓库：`scripts/mediawiki-api-extract/pipeline/phase_b.py`（主要修改点：missingtitle 处理、None-safety）
  - `chrome-agent` 仓库：`scripts/mediawiki-api-extract/pipeline/phase_a.py`（主要修改点：Fandom 页面过滤）
  - `chrome-agent` 仓库：`scripts/mediawiki-api-extract/pipeline/orchestrate.py`（Registry 补充）
  - `chrome-agent` 仓库：`scripts/mediawiki-api-extract/strategies/acquisition.py`（HtmlRenderedAcquisitionStrategy 修复）
  - `chrome-agent` 仓库：`scripts/mediawiki-api-extract/client.py`（API 错误语义化：PageNotFoundError）
  - `chrome-agent` 仓库：`sites/strategies/neonabyss.fandom.com/strategy.md`（内容校对：更新 content_profile 引用）
- `additional_context_refs`:
  - `chrome-agent` 仓库：`docs/plans/neonabyss-crawl-postmortem.md`（问题清单 P1-P7）
  - `chrome-agent` 仓库：`openspec/changes/pipeline-governance-and-variant/`（治理框架的设计约束）

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `scripts/mediawiki-api-extract/pipeline/orchestrate.py`：Registry 补充（fandom_infobox）
  - `scripts/mediawiki-api-extract/pipeline/phase_b.py`：missingtitle + None-safety 修复
  - `scripts/mediawiki-api-extract/pipeline/phase_a.py`：Fandom 页面过滤逻辑
  - `scripts/mediawiki-api-extract/strategies/acquisition.py`：HtmlRenderedAcquisitionStrategy 修复
  - `scripts/mediawiki-api-extract/client.py`：异常层次引入
  - `sites/strategies/neonabyss.fandom.com/strategy.md`：content_profile 修复
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: 变更验证完成后回写

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks

## 待确认项

- [x] 已确认标准页引用 — Orbitos Spec Standard v0.3
- [x] 已确认项目页引用 — 仓库内 pipeline 代码 + 策略文件
- [x] 已确认回写目标与权限 — 仓库内文件
- [ ] 已确认异常处理与冲突策略 — 设计阶段明确
