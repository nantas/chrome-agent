# Binding

## 标准与项目页面绑定

- `spec_standard_ref`: `specs/explore-strategy-pipeline-bridge/spec.md`（新建）
- `project_page_ref`:
  - `scripts/chrome-agent-cli.mjs` — CLI 引擎选择、fetch/explore 后端
  - `scripts/explore/main.py` — deep discovery pipeline 入口
  - `scripts/explore/sample_converter.py` — 策略驱动的样本转换器
  - `sites/anti-crawl/rate-limit-api.md` — 反爬策略
  - `configs/engine-registry.json` — 引擎注册表
- `additional_context_refs`:
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — Isaac Wiki 策略（测试用例）
  - `outputs/20260517-eval-7samples/` — 另一个 session 的退化样本（回归证据）
  - `~/.agents/skills/chrome-agent/SKILL.md` — Agent 工作流 skill

## Source of Truth

- 行为规范真源：`specs/explore-strategy-pipeline-bridge/spec.md`
- 项目页面角色：上下文输入 / 治理展示 / 结果回写
- 非真源说明：项目页面不得替代 spec delta 作为实现与验证依据

## 回写目标

- `writeback_targets`:
  - `scripts/chrome-agent-cli.mjs` — 新增 `runMediawikiApiFetch()`，修改 `selectFetcher()`、`runEngineFetch()`
  - `scripts/explore/sample_converter.py` — 新增 CLI 入口 `main()`
  - `scripts/explore/main.py` — 修改 engine 选择逻辑
  - `configs/engine-registry.json` — 新增 `mediawiki-api` 引擎条目
  - `sites/anti-crawl/rate-limit-api.md` — 更新 `engine_priority`
  - `~/.agents/skills/chrome-agent/SKILL.md` — 新增 Route to sample conversion 章节
- `writeback_owner`: chrome-agent repo maintainer
- `writeback_timing`: 实现完成后，before freeze

## 同步约束

- 页面与 spec 不一致时，以 `specs/` 为准
- 回写只同步结论、状态、摘要与链接，不复制整份 spec/design/tasks
- 若存在未确认引用、未定目标页或权限限制，必须在下方列明

## 待确认项

- [x] 已确认标准页引用 — 新建 spec `explore-strategy-pipeline-bridge`
- [x] 已确认项目页引用 — 4 个源文件 + 2 个测试用例
- [x] 已确认回写目标与权限 — 所有目标在 chrome-agent repo 内可写
- [x] 已确认异常处理与冲突策略 — 页面回写不替代 spec
