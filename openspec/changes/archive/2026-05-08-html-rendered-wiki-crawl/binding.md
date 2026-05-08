# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: repo://orbitos (`openspec/specs/orbitos-spec-standard-v1/spec.md`)
- `project_page_ref`:
  - `chrome-agent` 仓库：`sites/strategies/slaythespire.wiki.gg/strategy.md`
  - `chrome-agent` 仓库：`scripts/mediawiki-api-extract/` 管线
  - `wiki.gg` 仓库：`/Users/nantasmac/projects/personal/wiki.gg/README.md`
  - `wiki.gg` 仓库：`/Users/nantasmac/projects/personal/wiki.gg/src/wiki_gg/convert/markdown.py`
- `additional_context_refs`:
  - `chrome-agent` 仓库：`docs/playbooks/fallback-escalation.md`
  - `chrome-agent` 仓库：`openspec/specs/engine-contracts/spec.md`

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`（引擎注册、站点策略、扩展 API 规范）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `sites/strategies/slaythespire.wiki.gg/strategy.md`：更新内容获取策略、目录映射规则、分类页生成配置
  - `configs/engine-registry.json`：如有新增引擎类型（html_rendered）则同步更新
  - `scripts/mediawiki-api-extract/`：管线 README 或代码注释更新
- `writeback_owner`: chrome-agent 维护者
- `writeback_timing`: 变更验证完成后（Phase C / verification 通过）

## 同步约束

- 页面与 spec 不一致时，以 `openspec/specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 跨仓库引用（wiki.gg）仅作为经验输入，不直接修改 wiki.gg 仓库

## 待确认项

- [x] 已确认标准页引用 — Orbitos Spec Standard v0.3
- [x] 已确认项目页引用 — slaythespire.wiki.gg strategy + mediawiki-api-extract pipeline
- [x] 已确认回写目标与权限 — chrome-agent 仓库内文件
- [x] 已确认异常处理与冲突策略 — HTML 渲染失败 fallback 到 wikitext
