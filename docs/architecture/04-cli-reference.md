# CLI 命令参考（CLI Command Reference）

## 概述

CLI 入口为 `scripts/chrome-agent-cli.mjs`，通过 `parseArgs()` 解析参数（第 59 行），`main()` 函数分发到对应命令处理器（第 3665 行）。

全局调用方式：

```bash
chrome-agent [--format json|text] [--repo <path|repo://id>] <command> [args]
```

### 命令路由决策树

```
chrome-agent <command> <url>
    │
    ├── explore <url>
    │       └── runExplore() (:1552)
    │           └── python3 scripts/explore/main.py
    │               └── Deep discovery or Platform analysis
    │
    ├── fetch <url>
    │       └── runFetch() (:1766)
    │           ├── findStrategy() (:512) → matched?
    │           │   ├── Yes → selectFetcher() (:545) → Scrapling mode
    │           │   └── No  → scrapling-get (default)
    │           └── Single page content retrieval
    │
    ├── crawl <url>
    │       └── runCrawl() (:1965)
    │           ├── findStrategy() (:512) → discovery.method=sitemap?
    │           │   ├── Yes → Sitemap discovery path
    │           │   │         ├── --discovery-only → runCrawlSitemapDiscovery()
    │           │   │         └── full crawl         → runCrawlSitemapExtraction()
    │           │   └── No  → api.platform=mediawiki?
    │           │       ├── Yes → python3 -m scripts.pipeline pipeline
    │           │       │         runCrawlMediawikiApi() (:2054)
    │           │       └── No  → Scrapling discovery + crawl
    │           │                 runCrawlScrapling() (:2298)
    │           └── Bounded traversal with strategy
    │
    ├── scrape <url>
    │       └── runScrape() (:2736)
    │           └── Scrapling recursive crawl (strategy-free)
    │               selectFetcher() (:545) per page
    │
    ├── batch <urls...>
    │       └── runBatch() (:3221)
    │           └── Obscura serve pool parallel fetch
    │
    └── [strategy commands]
            ├── bootstrap-strategy → runBootstrapStrategy() (:2967)
            ├── freeze             → runFreeze() (:3100)
            └── iterate            → runIterate() (:3164)
```
<!-- Source: scripts/chrome-agent-cli.mjs: runExplore/runFetch/runCrawl/runScrape -->

## 命令列表

| 命令 | 说明 | 目标参数 |
|------|------|----------|
| `explore <url>` | 平台分析工作流 | URL |
| `fetch <url>` | 内容获取工作流 | URL |
| `crawl <url>` | 策略引导有界遍历 | URL |
| `scrape <url>` | 策略无关递归爬取 | URL |
| `batch <urls...>` | 批量并行获取 | 多个 URL |
| `bootstrap-strategy <url>` | 从已有策略派生新策略 | URL + `--from` |
| `freeze <scaffold-path>` | 冻结策略脚手架 | 路径 |
| `iterate <scaffold-path>` | 迭代更新提取规则 | 路径 |
| `doctor` | 环境诊断 | — |
| `clean [--scope all]` | 清理输出 | — |

## 全局参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--format <mode>` | `json\|text` | `text` | 输出模式 |
| `--repo <path>` | string | 自动推断 | 仓库路径或 `repo://` 引用 |
| `-h, --help` | flag | — | 显示帮助 |

## 命令详细说明

### explore

```bash
chrome-agent explore <url> [--report] [--no-report]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `<url>` | positional | 必填 | 目标 URL |
| `--report` | flag | — | 强制输出持久报告 |
| `--no-report` | flag | — | 禁用持久报告 |

**行为**：调用 `scripts/explore/main.py` 执行 deep discovery 管线。未命中已有策略时自动执行引擎链探测 → API 发现 → 结构映射 → 保护识别 → 脚手架生成。

**实现**：`runExplore()`（`chrome-agent-cli.mjs:1552`）

### fetch

```bash
chrome-agent fetch <url> [--report] [--no-report]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `<url>` | positional | 必填 | 目标 URL |
| `--report` | flag | — | 强制输出持久报告 |
| `--no-report` | flag | — | 禁用持久报告 |

**行为**：Scrapling-first 单页内容获取。匹配站点策略时走对应 fetcher，否则使用 `scrapling-get`。

**提取参数**：当匹配策略声明 `extraction.selectors.content` 时，fetch 通过 scrapling `-s <selector>` 精确提取主内容；未声明选择器时回退 `--ai-targeted` 启发式。该决策由共享 helper `buildScraplingExtractionArgs(strategy, fetcher)`（`scripts/lib/scrapling-extraction-args.mjs`）统一封装，`crawl` 命令的提取循环与 `--phase convert` 缓存转换复用同一 helper。`mediawiki-api` fetcher 保留 `[strategy.path]` 传递；`cloakbrowser` fetcher 保留既有 `--ai-targeted` 透传（其 CLI 不接受 `-s`）。

**实现**：`runFetch()`（`chrome-agent-cli.mjs:1766`）

### crawl

```bash
chrome-agent crawl <url> [options]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `<url>` | positional | 必填 | 目标 URL |
| `--entry-point <id>` | string | — | 从指定入口点开始 |
| `--max-pages <n>` | int | None (null) | 最大遍历页数 |
| `--concurrency <n>` | int | 5 | Markdown 转换并发数 |
| `--keep-html` | flag | false | 保留中间 HTML |
| `--merge` | flag | false | 合并为单文件 |
| `--no-markdown` | flag | false | 跳过 Markdown 转换 |
| `--parallel` | flag | false | 使用 Obscura serve pool 并行 |
| `--workers <n>` | int | 5 | Obscura worker 数（max: 30） |
| `--report` / `--no-report` | flag | — | 报告控制 |
| `--discovery-only` | flag | false | 仅执行发现，输出 `discovery_summary.json` |
| `--from-manifest <path>` | string | — | 从已有 manifest 恢复 |
| `--yes` | flag | — | 绕过确认闸门 |
| `--exclude-category <n>` | string[] | — | 排除分类（可重复） |
| `--phase <phases...>` | string[] | `all` | 执行阶段 |
| `--re-fetch` | flag | false | 强制重新获取 |
| `--pipeline-timeout-seconds <n>` | int | 600 | MediaWiki 每个 discovery/extraction 子进程预算，1–86400 秒 |

**行为**：策略引导有界遍历。MediaWiki 站点自动路由到 API 管线（`scripts/pipeline/`）。

**实现**：`runCrawl()`（`chrome-agent-cli.mjs:1965`）

**Pipeline 子命令路由**：当策略含 `api.platform: mediawiki` 时，内部调用 `python3 -m scripts.pipeline pipeline --strategy <path> --output <dir> <url>`。

### scrape

```bash
chrome-agent scrape <url> [options]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `<url>` | positional | 必填 | 目标 URL |
| `--max-pages <n>` | int | None (null) | 最大爬取页数 |
| `--no-same-domain` | flag | — | 允许跨域链接 |
| `--match <glob>` | string | — | URL 路径 glob 过滤 |
| `--concurrency <n>` | int | 5 | Markdown 转换并发数 |
| `--fetcher <name>` | string | `get` | 覆盖 Scrapling fetcher |
| `--keep-html` | flag | false | 保留中间 HTML |
| `--merge` | flag | false | 合并为单文件 |
| `--no-markdown` | flag | false | 跳过 Markdown 转换 |
| `--parallel` | flag | false | 使用 Obscura serve pool 并行 |
| `--workers <n>` | int | 5 | Obscura worker 数 |

**行为**：策略无关递归爬取，默认输出 Markdown。

**实现**：`runScrape()`（`chrome-agent-cli.mjs:2736`）

### batch

```bash
chrome-agent batch <url1> <url2> ... [options]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `<urls...>` | positional | 必填 | 一个或多个 URL |
| `--workers <n>` | int | 5 | Obscura worker 数 |
| `--concurrency <n>` | int | 15 | 超时秒数 |
| `--no-markdown` | flag | false | 跳过 Markdown 转换 |

**行为**：使用 Obscura serve pool 批量并行获取。

**实现**：`runBatch()`（`chrome-agent-cli.mjs:3221`）

### bootstrap-strategy

```bash
chrome-agent bootstrap-strategy <url> --from <domain> [--profile <name>]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `<url>` | positional | 必填 | 目标 URL |
| `--from <domain>` | string | 必填 | 参考策略域名 |
| `--profile <name>` | string | — | 清理配置覆盖 |

**行为**：继承经过校验的平台机制，生成不进入生产 registry 的 draft；填写目标字段和 `lifecycle.review_evidence` 后 freeze。

**实现**：`runBootstrapStrategy()`（`chrome-agent-cli.mjs:2967`）

### freeze

```bash
chrome-agent freeze <scaffold-path>
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `<scaffold-path>` | positional | 必填 | 脚手架策略路径 |

**行为**：冻结策略脚手架——移除 scaffold 标记、更新 registry、生成报告。

**实现**：`runFreeze()`（`chrome-agent-cli.mjs:3100`）

### iterate

```bash
chrome-agent iterate <scaffold-path>
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `<scaffold-path>` | positional | 必填 | 脚手架策略路径 |

**行为**：根据用户反馈重新运行样本转换，更新提取规则。

**实现**：`runIterate()`（`chrome-agent-cli.mjs:3164`）

### doctor

```bash
chrome-agent doctor
```

**行为**：验证 launcher、repo 解析、repo 形状、所有引擎就绪状态。通过 `scripts/engine-version-check.sh --json` 收集版本状态。

**实现**：`runDoctor()`（`chrome-agent-cli.mjs:3521`）

### clean

```bash
chrome-agent clean [--scope all|disposable]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--scope <scope>` | `disposable\|all` | `disposable` | 清理范围 |

**行为**：默认清理可丢弃输出（`outputs/`）；`--scope all` 额外清理缓存（`.cache/`）和报告（`reports/`）。

**实现**：`runClean()`（`chrome-agent-cli.mjs:3627`）

## Pipeline 子命令参考

MediaWiki API 管线通过 Python 子命令调用：

```bash
python3 -m scripts.pipeline <subcommand> [args]
```

**子命令路由**（`scripts/pipeline/cli.py:97`）：

| 子命令 | 说明 |
|--------|------|
| `pipeline` | 运行完整提取管线（默认子命令） |
| `fetch` | 获取并转换单个页面 |
| `reprocess` | 增量重新处理页面 |
| `fix-links` | 修复输出目录中的链接 |
| `reconvert` | 重新转换单个文件 |

### 当前 MediaWiki 阶段与确认门

`crawl --discovery-only`（兼容 `--phase discover`）调用 explore 页面枚举入口，复用已冻结策略的 allpages/homepage 内核，生成 manifest/summary 后停止；不会重跑站点测绘。普通 crawl 缺清单时先发现并等待确认，完整成功且显式 `--yes` 才继续，partial 必须另行确认。discovery-only 不受 --yes 改为抽取。

确认后使用 `crawl <url> --from-manifest <path>`。pipeline 入口保持 `python3 -m scripts.pipeline`，只接受 all/fetch/convert/assemble；直接 --phase discover 将报错。清单在 API probe 前验证，不完整或语义冲突不会降级为 Scrapling 首页抓取。

新清单 schema_version=2；旧无版本清单仅无歧义内存兼容，不改页集合、路径或源文件。详情见 [discover-kernel](../../openspec/specs/discover-kernel/spec.md) 与 [CLI规范](../../openspec/specs/cli/cli-workflows.md)。

## JSON 输出格式

`--format json` 时，CLI 通过 `renderResult()` 输出结构化 JSON：

```json
{
  "status": "success|partial_success|failure",
  "command": "crawl",
  "target": "https://example.wiki.gg",
  "repo_ref": "repo://chrome-agent",
  "run_dir": "/path/to/outputs/20260520-run-tag",
  "duration_ms": 12345,
  "artifacts": [
    {
      "path": "outputs/example.wiki.gg/page.md",
      "lifecycle": "durable|disposable",
      "description": "Extracted page content",
      "action": "created|updated"
    }
  ],
  "metrics": {
    "pages_discovered": 100,
    "pages_fetched": 98,
    "pages_converted": 95
  }
}
```

`renderResult()` 实现于 `chrome-agent-cli.mjs:315`。

## 关联文档

- [01 — 系统总览](01-overview.md) — 多后端架构全景
- [02 — 管线数据流](02-pipeline-flow.md) — MediaWiki API 五阶段管线详解
- [03 — 策略 Schema 参考](03-strategy-schema.md) — 策略配置字段权威参考
- [06 — 引擎选择](06-engine-selection.md) — 引擎选择决策树

---

### MediaWiki pipeline 超时预算

`crawl --pipeline-timeout-seconds <n>` 设置每个 MediaWiki discovery/extraction 子进程的总预算，单位秒，默认 600，允许整数 1–86400。例如 `--pipeline-timeout-seconds 3600` 为每阶段一小时。该选项不修改单个 API 请求超时或其他 backend，也不绕过 discovery/confirmation gate。非法值在启动子进程前拒绝；超时 failure context 包含 `pipeline_timeout_seconds`，保留 handoff 与失败状态。

## HTML 内容准入结果

fetch/crawl 在 selector 与 Markdown 转换前检查原始 HTML；本地转换使用同一次获取的 HTML。挑战页、空输出与读取失败不能成为成功正文。fetch manifest 包含 admission 与 diagnostic_path；诊断文件不作为 Extracted content 发布。Explore 无可用正文返回 failure/content_unavailable，不提示 freeze；结构化部分成功保留原状态。引擎不能提供 HTTP 元数据时为 null，不按退出码推定 200。

### doctor 健康报告与 Explore 诊断

`version_check` 必须覆盖配置中的全部选中引擎；缺脚本、空/坏 JSON、记录缺失或退出码矛盾返回 blocking 的 version_check_failed。合法非零退出的非健康报告仍保留引擎详情。

checks 包含 blocking；可选 CloakBrowser 缺失额外报告 readiness=needs_preflight。此时 doctor 为 partial_success，且仅所有失败检查均非阻塞并无 reload Gate 时 dispatch_allowed=true。必需检查故障返回 failure；skill reload 仍阻塞 dispatch。next_action 给出实际故障的修复步骤。

Explore 成功或失败均提供诊断文件入口及实际引擎链。内部调用/协议错误继续生成 handoff；普通内容不可用返回 failure，不提示将挑战页冻结为策略。

### Sitemap discovery 的 gzip 与失败证据

`crawl --discovery-only` 的 sitemap 路径支持顶层及子 sitemap 的普通 XML 和 gzip 内容。下载后根据实际 gzip 文件头解压，再读取 XML；URL 是否以 `.gz` 结尾不决定解压行为。原始响应文件保留，URL 继续按既有 include/exclude 和去重规则生成清单。

顶层 gzip 损坏返回 `sitemap_decompress_error`；子文件损坏记录 `decompress_error`，部分失败继续汇总正常文件并返回告警，全部失败仍为 `sitemap_all_subs_failed`。解压成功但内容非 sitemap 时仍为解析错误。失败 handoff 链接实际存在的原始 sitemap 文件，不再列出未生成的 `manifest.json`。

本路径仅产出发现清单；确认页面范围后才使用 `--from-manifest` 进入正文提取。实现与验证见 [gzip sitemap change](../../openspec/changes/archive/2026-10-03-fix-gzip-sitemap-discovery/verification.md)。
