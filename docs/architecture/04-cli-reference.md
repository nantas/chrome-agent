# CLI 命令参考（CLI Command Reference）

## 概述

CLI 入口为 `scripts/chrome-agent-cli.mjs`，通过 `parseArgs()` 解析参数（第 59 行），`main()` 函数分发到对应命令处理器（第 3665 行）。

全局调用方式：

```bash
chrome-agent [--format json|text] [--repo <path|repo://id>] <command> [args]
```

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

**实现**：`runFetch()`（`chrome-agent-cli.mjs:1766`）

### crawl

```bash
chrome-agent crawl <url> [options]
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `<url>` | positional | 必填 | 目标 URL |
| `--entry-point <id>` | string | — | 从指定入口点开始 |
| `--max-pages <n>` | int | 3 | 最大遍历页数 |
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
| `--max-pages <n>` | int | 10 | 最大爬取页数 |
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

**行为**：从已有策略文件复制并适配新站点。自动更新 `registry.json`。

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

### pipeline 子命令参数

通过 `_add_pipeline_args()` 定义（`scripts/pipeline/cli.py:165`）：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | positional | 必填 | 目标 Wiki URL |
| `--strategy` | string | 必填 | 策略文件路径 |
| `--output` | string | 必填 | 输出目录 |
| `--concurrency` | int | None | 并发请求数（覆盖策略配置） |
| `--batch-delay-ms` | int | None | 批次间延迟 |
| `--max-retries` | int | None | 最大重试次数 |
| `--backoff-multiplier` | float | None | 退避乘数 |
| `--jitter` | flag | None | 启用抖动 |
| `--phase` | string[] | `all` | 执行阶段：`all`, `discover`, `fetch`, `convert`, `assemble` |
| `--re-fetch` | flag | false | 强制重新获取（忽略缓存） |
| `--discovery` | string | `auto` | 发现策略：`auto`, `allpages`, `homepage` |
| `--no-api-probe` | flag | false | 跳过 API 端点探测 |
| `--resume` | flag | true | 启用断点续传 |
| `--no-resume` | flag | — | 禁用断点续传 |
| `--resume-flush-interval` | int | 100 | 状态刷新间隔 |
| `--no-auto-fix-links` | flag | false | 跳过自动链接修复 |
| `--validate` | flag | false | 运行 L6 验证 |
| `--exclude-category` | string[] | — | 排除分类（可重复） |
| `--from-manifest` | string | — | 已有 manifest 路径 |
| `--max-pages` | int | None | 最大提取页数 |

### --phase 阶段组合

| 值 | 行为 |
|------|------|
| `all`（默认） | 执行完整管线 |
| `discover` | 仅发现阶段，输出 manifest |
| `fetch` | 仅获取阶段（依赖已有 manifest 或 `--from-manifest`） |
| `convert` | 仅转换阶段（需要 `--from-manifest`） |
| `assemble` | 仅装配阶段（从 `extraction_results.json` 加载） |

多阶段可组合：`--phase fetch convert assemble`

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

---
