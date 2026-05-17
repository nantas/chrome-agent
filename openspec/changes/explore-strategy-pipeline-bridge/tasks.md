# Tasks

## 1. Spec 覆盖与实现准备

- [ ] 1.1 确认 specs: `explore-strategy-pipeline-bridge` (new, 6 reqs), `engine-contracts` (modified, 4 reqs), `explore-workflow` (modified, 2 reqs), `site-strategy` (modified, 2 reqs) — 全部 14 requirements 已覆盖
- [ ] 1.2 确认依赖：`sample_converter.py` 需要 `bs4`, `yaml`, `markdownify`，已在 explore pipeline deps check 中验证

## 2. 核心实现任务

### Phase 1: 引擎选择修复

- [ ] 2.1 `selectFetcher()` 添加 `api.platform` 检测 — 修改 `scripts/chrome-agent-cli.mjs:432`
  - 验证: `selectFetcher({ document: { api: { platform: "mediawiki" } } }, null)` → `"mediawiki-api"`
  - 验证: `selectFetcher({ document: {} }, null)` → `"get"` (现有行为不变)
- [ ] 2.2 新增 `runMediawikiApiFetch()` 函数 — `scripts/chrome-agent-cli.mjs`
  - 从 strategy 读取 `api.base_url`、从 URL 提取 page title、调用 `action=parse` API、写 HTML 到 outputPath
  - 验证: 对 Isaac Wiki 主页调用，产出有效 HTML 文件
- [ ] 2.3 `runEngineFetch()` 添加 `"mediawiki-api"` 分支 — `scripts/chrome-agent-cli.mjs:548`
  - 验证: `runEngineFetch(repoRoot, "mediawiki-api", url, outputPath)` → 调用 `runMediawikiApiFetch()`

### Phase 1: 样本转换 CLI

- [ ] 2.4 `sample_converter.py` 新增 `main()` + argparse CLI — `scripts/explore/sample_converter.py`
  - 子命令: `apply` (已有 HTML) 和 `fetch-and-apply` (API fetch + 转换)
  - 验证: `python3 scripts/explore/sample_converter.py apply --strategy <path> --html <path> --title "X" --output <path>` → JSON `{ok: true}`
  - 验证: `fetch-and-apply` 子命令对 "The Sad Onion" 产出 Markdown，无 KI-5/KI-6 退化
- [ ] 2.5 `main.py` engine 选择引用 `api_config` — `scripts/explore/main.py:63`
  - 验证: 对 API-discovered 站点，`engine` = `"mediawiki-api"` 而非 `probe_result.success_engine`

### Phase 2: 工作流文档

- [ ] 2.6 SKILL.md 新增 "Route to sample conversion" 章节 — `~/.agents/skills/chrome-agent/SKILL.md`
  - 记录: API 站点 → `sample_converter.py fetch-and-apply`；非 API 站点 → `chrome-agent fetch`
  - 记录: 转换后运行 self-check
- [ ] 2.7 AGENTS.md 记录 `sample_converter.py` CLI 用途 — `AGENTS.md`
- [ ] 2.8 `runExplore()` 返回中增加 `conversion_engine` / `converter_path` 字段 — `chrome-agent-cli.mjs`

### Phase 3: 基础设施

- [ ] 2.9 `engine-registry.json` 新增 `mediawiki-api` 条目 — `configs/engine-registry.json`
  - `id: "mediawiki-api"`, `type: "api"`, `status: "frozen"`, `default_rank: 0`
- [ ] 2.10 更新 `rate-limit-api` 反爬策略 engine_priority — `sites/anti-crawl/rate-limit-api.md`
  - 新增 `engine: "mediawiki-api"`, `rank: 0`；现有 `scrapling-fetch` 降为 `rank: 1`

## 3. 收敛与验证准备

- [ ] 3.1 端到端验证：Isaac Wiki explore → `selectFetcher` → API fetch → `sample_converter.py` → 样本质量 = 本 session V4+ 标准
- [ ] 3.2 回归验证：非 MediaWiki 站点（无 `api.platform`）引擎选择不变
- [ ] 3.3 断点验证：另一个 session 复现场景 — agent 调用 explore → 使用 `sample_converter.py` 而非裸 markdownify

## 4. 验证与回写收敛

- [ ] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [ ] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [ ] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据
