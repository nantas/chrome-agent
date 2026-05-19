# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/mediawiki-api-extraction-pipeline/spec.md`
  - `openspec/specs/pipeline-cli-entry/spec.md`
  - `openspec/specs/pipeline-resume/spec.md`
  - `openspec/specs/strategy-guided-crawl/spec.md`
- `project_page_ref`:
  - chrome-agent 仓库内 AGENTS.md（能力变更需同步 README.md 能力清单）
- `additional_context_refs`:
  - `outputs/20260518T073409-crawl-bindingofisaacrebirth-wiki-gg/` — 最后一次 Isaac 全量爬取产物（作为基线参考）
  - `outputs/handoffs/20260518-crawl-bindingofisaacrebirth-wiki-gg/handoff.md` — 品质报告与已知问题

## Source of Truth

- 行为规范真源：`specs/<capability-id>/spec.md`（上述四个 capability spec 的 delta）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `AGENTS.md`：更新第 2 节 Capability Framework 中 pipeline 相关能力的描述
  - `README.md`：如有能力描述变更，按 readme-governance 规则更新
- `writeback_owner`: 当前 change 作者
- `writeback_timing`: verification 阶段完成后

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用（四个 capability spec）
- [ ] 已确认项目页引用（AGENTS.md / README.md 能力描述；Obsidian 项目页面如存在，待发现后补充）
- [x] 已确认回写目标与权限
- [x] 已确认异常处理与冲突策略（fetch 失败页面记录错误日志，不阻断其余页面；缓存格式变更时通过 --re-fetch 刷新）
