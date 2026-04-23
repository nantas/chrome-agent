# Proposal

## 问题定义

当前仓库的网页抓取工作流以 `chrome-devtools-mcp` 为默认路径，`chrome-cdp` 作为真实 Chrome live-session 续接路径。这个决策适合浏览器调试和证据采集，但对常见抓取任务存在几个不足：

- 内容抓取、动态渲染、反爬尝试、批量 URL 抓取和站点级任务缺少统一抓取执行层。
- 浏览器诊断工具承担了过多“抓取优先入口”的职责，导致简单内容获取和复杂页面诊断边界不够清晰。
- Scrapling 研究页显示其覆盖普通 HTTP、动态浏览器、stealth、session、CLI、MCP、批量和 Spider 能力，适合作为新的抓取优先路径。

本 change 目标是把仓库工作流重排为 Scrapling-first：优先使用 Scrapling 完成抓取和抽取，解决不了或需要证据补强时再进入 `chrome-devtools-mcp` / `chrome-cdp`。

## 范围边界

范围内：

- 更新仓库网页抓取路由规则，使 Scrapling 成为公开页面、动态页面、受保护页面、批量抓取和登录态实验候选的第一路径。
- 明确 Scrapling 与 `chrome-devtools-mcp`、`chrome-cdp` 的职责边界和切换触发条件。
- 增加 Scrapling 环境接入与最小验证要求，包括 Python `>=3.10`、Scrapling 安装、浏览器依赖和 MCP/CLI smoke check。
- 扩展现有评估基线，使后续实现能用公开、文章、受保护场景验证 Scrapling-first 决策，并为登录态场景记录明确的批准前置条件。

范围外：

- 不在本 change 中建设大型自动化框架。
- 不默认启用站点级 Spider、checkpoint、代理池或持久化爬虫调度；这些只作为后续真实批量需求的 v2 候选。
- 不引入凭据管理；登录态仅做用户明确批准下的只读 session 复用或 live-session 实验。
- 不把全局 `chrome-agent` dispatcher 改造成抓取实现层。

## Capabilities

### New Capabilities

- `scrapling-first-browser-workflow`: 定义 Scrapling 作为网页抓取优先路径的路由、环境、验证和 fallback 行为。

### Modified Capabilities

## Capabilities 待确认项

- [x] 能力清单已与用户确认：Scrapling 应成为默认优先路径，理论上也优先覆盖登录态场景，但需要实际验证。

## Impact

- `AGENTS.md` 的 Tooling Strategy、Selection Rules、Minimum Verification Baseline 需要更新为 Scrapling-first。
- `README.md` 的当前状态、原则和工作规则需要从 DevTools-first 改为 Scrapling-first。
- `docs/decisions/` 需要新增或更新浏览器抓取工作流决策，记录旧决策被新 Scrapling 方案取代的条件。
- `docs/playbooks/browser-tooling-evaluation.md` 需要加入 Scrapling-first 评估矩阵和 fallback 证据要求。
- `docs/setup/` 需要增加 Scrapling 安装、MCP/CLI 配置和 smoke check 说明。
- `sites/` 可在验证后记录 Scrapling 对特定站点的成功、失败或 fallback 经验。

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OpenSpec_Schema_Source/orbitos-change-v1`
  - `project_page_ref`: `/Users/nantasmac/projects/agentic/chrome-agent/AGENTS.md`
  - `writeback_targets`: `/Users/nantasmac/projects/agentic/chrome-agent/AGENTS.md`, `/Users/nantasmac/projects/agentic/chrome-agent/README.md`, `/Users/nantasmac/projects/agentic/chrome-agent/docs/decisions/`, `/Users/nantasmac/projects/agentic/chrome-agent/docs/playbooks/`, `/Users/nantasmac/projects/agentic/chrome-agent/sites/`
