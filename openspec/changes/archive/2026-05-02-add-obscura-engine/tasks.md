# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `obscura-fetch-contract` spec 中所有 requirements 的可实现性
  - Input contract: URL, wait_until, selector, timeout, stealth, extract_format, eval, user_agent, proxy, obey_robots
  - Output contract: url, title, content, content_type, status_code, redirect_chain, links, timing_ms, network_events
  - Error contract: network, timeout, block, parse, browser
  - Performance: RSS ≤15MB idle, ≤50MB peak, ≤50% of scrapling-fetch wall time
  - CDP compatibility: Target, Page, Runtime, DOM, Network, Fetch, Storage, Input, LP domains
  - Smoke-check: news.ycombinator.com → title + ≥20 stories + HTTP 200 + ≤5000ms

- [x] 1.2 确认 `engine-registry` spec MODIFIED requirements 的变更范围
  - 类型枚举新增 `cdp_lightweight`
  - 评分维度新增 cdp_lightweight efficiency range (0.70-0.90)
  - Default rank 中 cdp_lightweight 定位在 http 和 playwright 之间
  - obscura-fetch entry: efficiency=0.85, stability=0.55, adaptability=0.65, composite_score=62, default_rank=2
  - 现有引擎 rank 后移: scrapling-fetch 2→3, scrapling-bulk-fetch 3→4, scrapling-stealthy-fetch 3→4, chrome-devtools-mcp 4→5, chrome-cdp 5→6

- [x] 1.3 确认 `engine-contracts` spec MODIFIED requirements 的变更范围
  - Scrapling-first rule 纳入 cdp_lightweight 类型
  - Page type mapping: dynamic_content/dynamic_list 优先 obscura-fetch
  - 错误矩阵新增 obscura-fetch 列
  - Escalation chain: scrapling-get → obscura-fetch → scrapling-fetch → stealthy-fetch → devtools-mcp
  - Smoke-check inventory 新增 obscura-fetch 行

- [x] 1.4 确认依赖前置条件
  - `obscura` 预编译二进制可通过 GitHub Releases 下载
  - 目标平台 (macOS ARM64 / Linux x86_64) 有对应 release

## 2. 核心实现任务

- [x] 2.1 更新 `configs/engine-registry.json`
  - 新增 `obscura-fetch` 条目（type: cdp_lightweight, status: draft, default_rank: 2）
  - 现有引擎 default_rank 后移（scrapling-fetch 2→3, scrapling-bulk-fetch 3→4, scrapling-stealthy-fetch 3→4, chrome-devtools-mcp 4→5, chrome-cdp 5→6）
  - 验证：JSON 格式正确，所有 engine id 唯一，composite_score 计算正确
  - 引用：`specs/engine-registry/spec.md` → ADDED Requirements → obscura-fetch engine entry

- [x] 2.2 更新 `openspec/specs/engine-registry/spec.md`（真源同步）
  - 将 change spec delta 中的 MODIFIED/ADDED requirements 合并到 frozen spec
  - 类型枚举：`http`, `playwright`, `playwright_stealth`, `cdp_managed`, `cdp_live`, `cdp_lightweight`, `playwright_bulk`
  - 验证：spec 与 registry.json 一致

- [x] 2.3 更新 `openspec/specs/engine-contracts/spec.md`（真源同步）
  - 将 change spec delta 中的 MODIFIED requirements 合并到 frozen spec
  - 错误矩阵、escalation chain、smoke-check 清单追加 obscura-fetch
  - 验证：所有变更点与 delta spec 一致

- [x] 2.4 创建 `docs/playbooks/obscura-cli-preflight.md`
  - Obscura 二进制检测逻辑：OBSURA_CLI_PATH → 受管路径 → 自动下载 → 源码编译
  - 安装命令：`curl -LO <release-url>` 并解压到 `$HOME/.cache/chrome-agent-obscura/bin/`
  - 版本固定策略：下载后通过 `--help` 校验，锁定版本
  - 参考：`docs/playbooks/scrapling-cli-preflight.md` 的结构和格式

- [x] 2.5 更新 AGENTS.md 引擎扩展治理章节
  - 在引擎扩展治理章节追加 obstura-fetch 的简要说明
  - 引用 `docs/playbooks/obscura-cli-preflight.md`
  - 验证：AGENTS.md 中引擎列表与 registry 一致

- [x] 2.6 创建 `docs/decisions/2026-05-02-obscura-engine-addition.md`
  - Context: chrome-agent 效率断层 + Obscura 端到端对比测试结论
  - Decision: 作为 cdp_lightweight 类型引擎接入，rank 2
  - Consequences: 正面（效率提升）、风险（v0.1.0 稳定性）、迁移（rank 后移）
  - 更新 `docs/decisions/README.md` 索引

## 3. 收敛与验证准备

- [x] 3.1 执行 smoke-check（obscura-fetch-contract spec → Smoke-check scenario）
  - 验证项 1: `obscura fetch https://news.ycombinator.com --dump html` → title "Hacker News" + ≥20 story entries
  - 验证项 2: HTTP 状态码 200
  - 验证项 3: timing ≤ 5000ms
  - 证据存放：`reports/2026-05-02-obscura-smoke-check.md`

- [x] 3.2 执行 registry consistency check
  - `configs/engine-registry.json` 中所有 engine id 唯一
  - 每个 engine 的 `contract_spec` 对应 `openspec/specs/<contract_spec>/spec.md` 存在
  - `composite_score` 计算公式验证
  - `default_rank` 无重复、无跳跃

- [x] 3.3 执行 escalation chain 演练
  - 场景 1: 静态页面 → scrapling-get 成功，不触发 obscura-fetch
  - 场景 2: 动态页面（scrapling-get 失败/不适配）→ obscura-fetch 被选中
  - 场景 3: obscura-fetch 失败 → scrapling-fetch 被选中（fallback 正确）

- [x] 3.4 执行 preflight playbook smoke test
  - 清理受管路径后执行 preflight → 自动下载并验证
  - 已存在时跳过下载
  - 环境变量 OBSURA_CLI_PATH 被正确识别

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 `writeback.md`（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据
  - `AGENTS.md` 引擎扩展治理章节更新
  - `docs/governance-and-capability-plan.md` 能力全景图追加 obscura-fetch
  - `docs/decisions/README.md` 索引更新
