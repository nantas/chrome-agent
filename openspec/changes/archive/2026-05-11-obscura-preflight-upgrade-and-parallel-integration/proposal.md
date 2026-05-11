# Proposal

## 问题定义

chrome-agent 的 `crawl`/`scrape` 命令在执行批量页面抓取时，使用 Scrapling 串行逐页 fetch。对于非 API 的 HTML/JS 站点（Tier 1-2），串行模式是显著的性能瓶颈：8 页需要 8-17s，50 页需要 75-150s。

Obscura v0.1.2 提供了两种并行能力：
1. `scrape` 子命令的并行批量 fetch → 但只返回元数据（url, title, time_ms），不返回页面内容
2. `serve --workers N` + 并发 `fetch` 模式 → 返回完整 HTML，与 Scrapling 输出完全兼容

已验证：3 workers + 4 并发 fetch = 3.3s 获取 4 页完整 HTML（含 166KB Wikipedia），加速比 2.4-5.3x。

同时，当前 Obscura preflight 固定在 v0.1.0，未包含 worker binary 安装验证。升级到 v0.1.2 是并行整合的前提。

## 范围边界

**范围内：**
- Obscura preflight 版本升级：v0.1.0 → v0.1.2
- Preflight 增加 worker binary 验证步骤
- 新增 `obscura-serve-pool` 引擎（serve + 并发 fetch 模式）
- `crawl`/`scrape` 命令新增 `--parallel` / `--workers` 标志
- 新增 `batch` 命令：URL 列表直接并行 fetch
- crawl 管线路由逻辑：API 站点走管线 B，Browser 站点走管线 A
- 引擎注册表新增条目

**范围外：**
- MediaWiki API 管线本身的改造（管线 B 保持独立）
- 高保护页面（Tier 4，CloakBrowser 仍为权威）
- 修改 Obscura upstream（无 PR 开发）
- 替换 Scrapling 遍历逻辑（Phase 1 仍用 Scrapling get）

## Capabilities

### New Capabilities
- `obscura-preflight-v012`: 升级 Obscura preflight 到 v0.1.2，包含 `obscura-worker` binary 验证
- `obscura-serve-pool`: 新增 crp_lightweight_pool 引擎，通过 serve + 并发 fetch 模式实现批量内容获取
- `batch-command`: 新增 chrome-agent batch 子命令，直接接收 URL 列表并发并行 fetch，绕过遍历阶段

### Modified Capabilities
- `crawl-strategy-router`: crawl 命令增加管线路由逻辑，根据 strategy frontmatter 的 api.platform 字段自动路由到 API 管线或 Browser 爬取管线
- `scrape-parallel-mode`: scrape 命令增加 --parallel 标志，支持三阶段工作流（遍历收集 → serve 并发 fetch → markdown 转换）
- `engine-registry`: 引擎注册表 configs/engine-registry.json 新增 obscura-serve-pool 条目

## Impact

| 组件 | 影响 | 说明 |
|------|------|------|
| `docs/playbooks/obscura-cli-preflight.md` | 修改 | 版本号、下载 URL、验证步骤 |
| `configs/engine-registry.json` | 新增条目 | 新增 `obscura-serve-pool` 引擎（rank 3） |
| `openspec/specs/` | 新增 3 个 spec | 新能力 + 修改能力的 spec delta |
| `scripts/chrome-agent-cli.mjs` | 主要修改 | serve 生命周期管理、并发 fetch、管线路由 |
| `docs/playbooks/fallback-escalation.md` | 修改 | 新增 obscura-serve-pool 的 escalation 路径 |
| `docs/playbooks/scrapling-fetchers.md` | 修改 | 新增 serve pool 文档 |

**无影响组件：**
- `scripts/mediawiki-api-extract/`：管线 B 完全独立
- `scripts/scrapling-cli.sh`：Scrapling 保留为 fallback
- `scripts/cloakbrowser-preflight.sh`：高保护页面不受影响

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 项目页: `docs/plans/2026-05-11-obscura-bulk-scrape-integration-design.md`
  - 项目页: `docs/plans/2026-05-11-obscura-crawl-convergence-analysis.md`
  - 项目页: `docs/plans/2026-05-11-obscura-vs-scrapling-benchmark-report.md`
  - 回写目标: Obsidian vault, `/Projects/chrome-agent/Obscura-Parallel-Integration`
