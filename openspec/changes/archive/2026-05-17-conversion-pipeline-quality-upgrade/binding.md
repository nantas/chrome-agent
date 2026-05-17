# Binding

## 标准与项目页面绑定

- `spec_standard_ref`:
  - `openspec/specs/sample-self-check/spec.md` — 自检体系 S1-S12 规范真源
  - `openspec/specs/explore-workflow/spec.md` — explore 工作流 + agent gate 规范真源
  - `openspec/specs/pipeline-converters/spec.md` — HtmlToMarkdownConverter 接口规范真源
  - `openspec/specs/markdown-conversion-pipeline/spec.md` — 共享转换管线规范真源
  - `openspec/specs/site-strategy/spec.md` — 站点策略 extration 配置规范真源
  - `openspec/specs/site-strategy-template/spec.md` — 平台模板规范真源

- `project_page_ref`:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — Isaac Wiki 站点策略文件
  - `sites/templates/mediawiki-wiki-gg.yaml` — wiki.gg 平台模板
  - `scripts/mediawiki_api_extract/converters/` — 转换器子包
  - `scripts/explore/self_check.py` — 自检脚本
  - `scripts/explore/sample_converter.py` — 样本转换脚本
  - `AGENTS.md` — agent 行为治理
  - `skills/chrome-agent/SKILL.md` — explore gate 行为入口

- `additional_context_refs`:
  - `outputs/isaac-sample-validation/` — 本次 change 的样本验证证据
  - 完整测试复盘记录于 2026-05-16 至 2026-05-17 session（6 轮迭代，v1→v8 converter 演进）

## Source of Truth

- 行为规范真源：`openspec/specs/<capability-id>/spec.md`（上述 6 个 spec 文件）
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面（`AGENTS.md`、`strategy.md`、`skill` 文件）不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `openspec/specs/sample-self-check/spec.md` — 新增 S8-S12 检查项
  - `openspec/specs/explore-workflow/spec.md` — 新增 agent gate 行为和样本验证要求
  - `openspec/specs/pipeline-converters/spec.md` — 新增 balanced removal、tooltip merge 接口
  - `openspec/specs/site-strategy/spec.md` — 新增 `infobox_field_handlers` 配置项

- `writeback_owner`: chrome-agent maintainer（当前仓库 owner）
- `writeback_timing`: 实现完成后（verification pass）执行回写，将结论、状态、摘要同步到 spec 文件和 `AGENTS.md`

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- Project page 更新（`AGENTS.md`、`strategy.md`）为可选回写，不阻塞 change 关闭
- 若 strategy.md 在 change 过程中被修改（如新增 `extraction.infoxbox_field_handlers`），须同步更新 `sites/strategies/registry.json`

## 待确认项

- [x] 已确认标准页引用（6 个 spec 文件均存在于仓库中）
- [x] 已确认项目页引用（Isaac Wiki strategy、wiki-gg 模板、converter 代码、explore scripts）
- [x] 已确认回写目标与权限（4 个 spec delta 回写目标，均在仓库内）
- [x] 已确认 agent gate 行为变更需同步到 `AGENTS.md` explore gate 描述
- [x] 已确认 `skills/chrome-agent/SKILL.md` 中 explore → crawl confirmation gate 引用需更新（当前已存在但需补充自检报告展示要求）
