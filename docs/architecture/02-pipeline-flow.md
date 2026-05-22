# 管线数据流（Pipeline Data Flow）

## 概述

MediaWiki API 提取管线（`scripts/pipeline/`）是 chrome-agent 针对 MediaWiki 平台站点的结构化内容提取核心。管线由 `orchestrator.py` 中的 `run_pipeline()` 函数编排，支持五种阶段独立或组合执行。

**权威来源**：`scripts/pipeline/pipeline/orchestrator.py:76` — `run_pipeline(args: argparse.Namespace) -> int`

## 端到端数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│                        输入                                         │
│  CLI args: url, --strategy, --output, --phase, --concurrency, ...  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  策略解析    │  parse_strategy(path) → dict
                    │  管线构建    │  build_pipeline(strategy, domain) → PipelineStrategies
                    │  API 探测    │  probe_api_endpoint(origin, base_url) → base_url
                    └──────┬──────┘
                           │
          ┌────────────────┼───────────────────┐
          │                │                   │
    ┌─────▼─────┐   ┌─────▼──────┐     ┌──────▼──────┐
    │ Homepage   │   │ Allpages   │     │ --from-     │
    │ Homepage  │   │ Allpages   │     │ manifest    │
    │ Discovery │   │ Discovery  │     │ (跳过发现)  │
    └─────┬─────┘   └─────┬──────┘     └──────┬──────┘
          │               │                   │
          └───────────────┼───────────────────┘
                          │
                   ┌──────▼──────┐
                   │ page_       │
                   │ manifest    │
                   │ .json       │
                   │             │
                   │ discovery_  │
                   │ summary     │
                   │ .json       │
                   └──────┬──────┘
                          │
            ┌─────────────┼──────────────┐
            │                            │
     ┌──────▼──────┐              ┌──────▼──────┐
     │ Fetch       │              │ --max-pages │
     │ API 获取    │              │ 分类过滤     │
     │ → .cache/   │              │              │
     └──────┬──────┘              └──────┬──────┘
            │                            │
            └─────────────┬──────────────┘
                          │
                   ┌──────▼──────┐
                   │ .cache/     │
                   │ <platform>/ │
                   │ <domain>/   │
                   │ <page>.json │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ Convert     │
                   │ Convert     │
                   │ 缓存→MD     │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ extraction_ │
                   │ results     │
                   │ .json       │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ Assembly   │
                   │ Assembly    │
                   │ + link-fix  │
                   │ + L6 验证   │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ 输出目录     │
                   │ <domain>/   │
                   │ <category>/ │
                   │ <page>.md   │
                   └─────────────┘
```

## 五阶段详解

### Homepage Discovery — 首页发现

| 项目 | 说明 |
|------|------|
| **入口** | `scripts/pipeline/pipeline/phases/discovery_homepage.py:26` — `run_homepage_discovery()` |
| **触发条件** | 策略含 `api.homepage` 配置，且 `--discovery auto`（默认）或 `--discovery homepage` |
| **输入** | `ApiClient`、strategy dict、origin URL |
| **流程** | 1. `parse_homepage()` 解析首页 HTML 提取分类链接 → 2. 每个分类发现成员页 → 3. `assign_pages()` 分配输出目录 |
| **输出** | `page_manifest.json`（与 Allpages Discovery 格式兼容） |
| **副作用** | 无 |

### Allpages Discovery — 全页发现

| 项目 | 说明 |
|------|------|
| **入口** | `scripts/pipeline/pipeline/phases/discovery_allpages.py:14` — `run_allpages_discovery()` |
| **触发条件** | 策略无 `api.homepage` 或 `--discovery allpages` |
| **输入** | `ApiClient`、strategy dict、`DiscoveryStrategy` 实例 |
| **流程** | 1. `discovery_strategy.discover_pages()` 通过 API 枚举所有页面 → 2. Fandom 翻译页过滤 → 3. 分类排除 → 4. 页面分配 |
| **输出** | `page_manifest.json` |
| **副作用** | 无 |

### Fetch — 内容获取

| 项目 | 说明 |
|------|------|
| **入口** | `scripts/pipeline/pipeline/phases/fetch.py:38` — `run_fetch()` |
| **触发条件** | `--phase fetch` 或 `--phase all`（默认） |
| **输入** | manifest、strategy、`ContentAcquisitionStrategy`、`RateLimitConfig` |
| **流程** | 1. 检查 `.cache/` 已缓存页面（除非 `--re-fetch`） → 2. **快速路径**：若所有页面已缓存则直接返回 `skipped=total`（<1秒） → 3. **预过滤**：分离已缓存/未缓存页面，仅未缓存页面提交线程池 → 4. 并发获取未缓存页面（`ThreadPoolExecutor`，concurrency 由 rate_limit 控制） → 5. `time.sleep(batch_delay_sec)` 仅在实际网络请求（`status=ok`）时执行 → 6. 写入 `.cache/<platform>/<domain>/<page>.json` |
| **输出** | Stats dict（total, fetched, skipped, failed） |
| **副作用** | 写入 `.cache/` 持久化缓存 |

### Convert — 内容转换

| 项目 | 说明 |
|------|------|
| **入口** | `scripts/pipeline/pipeline/phases/convert.py:22` — `run_convert()` |
| **触发条件** | `--phase convert` 或 `--phase all` |
| **输入** | output_dir、manifest、strategy、domain、repo_root |
| **流程** | 1. 从 `.cache/` 读取原始内容 → 2. 根据 `content_acquisition` 策略选择转换路径（wikitext/html/hybrid） → 3. 模板处理 + 链接解析 → 4. 输出 Markdown |
| **输出** | `(results dict, stats dict)`；写入 `extraction_results.json` |
| **副作用** | 无网络请求，纯本地执行 |

### Assembly — 输出装配

| 项目 | 说明 |
|------|------|
| **入口** | `scripts/pipeline/pipeline/phases/assemble.py:14` — `run_assemble()` |
| **触发条件** | `--phase assemble` 或 `--phase all` |
| **输入** | output_dir、manifest、results dict、`ListPageAssembler`、`LinkResolver` |
| **流程** | 1. 创建目录结构 → 2. 写入独立页面文件 → 3. 生成分类索引页 → 4. 列表页装配 → 5. 自动 link-fix |
| **输出** | Stats dict |
| **副作用** | 写入输出目录文件 |

## 缓存机制

缓存由 `scripts/pipeline/pipeline/cache.py` 管理，实现 Fetch 与 Convert 阶段解耦：

```
<repo_root>/.cache/
  └── <platform>/        # "mediawiki" 或 "scrapling"
      └── <domain>/
          ├── Page_Title_1.json
          ├── Page_Title_2.json
          └── ...
```

**每个缓存文件包含**：`html`、`wikitext`、`rendered_html`、`images`、`content_acquisition`、`fetched_at` 时间戳。

**关键行为**：
- Fetch 阶段：缓存已有页面跳过（`is_cached = title in cached_pages`），除非 `--re-fetch`；全量缓存时走快速路径直接返回（<1秒）；`batch_delay` sleep 仅在实际网络请求时执行
- Convert 阶段：纯读缓存，无网络请求
- 跨 session 复用：缓存持久化在仓库 `.cache/` 目录，支持跨 CLI 调用复用
- `--re-fetch`：强制刷新所有页面，忽略已有缓存

## 速率限制优先级解析

速率限制通过 `scripts/lib/config_resolver.py:resolve_rate_limit_config()` 四层优先级解析：

```
优先级（高→低）:
1. CLI 参数         --concurrency, --batch-delay-ms, --max-retries, ...
2. 站点策略本地覆盖  api.rate_limit.concurrency, api.rate_limit.batch_delay_ms, ...
3. 反爬策略模板     api.rate_limit.tier → sites/anti-crawl/<ref>.md → rate_limit_tiers
4. 代码安全默认值   RateLimitConfig() → concurrency=1, batch_delay_ms=1000, ...
```

**RateLimitConfig 字段**（`scripts/lib/config_resolver.py:24`）：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `concurrency` | int | 1 | 并发请求数 |
| `batch_delay_ms` | int | 1000 | 批次间延迟（毫秒） |
| `max_retries` | int | 5 | 最大重试次数 |
| `initial_delay_sec` | float | 1.0 | 初始退避延迟 |
| `backoff_multiplier` | float | 2.0 | 指数退避乘数 |
| `max_delay_sec` | float | 60.0 | 最大退避延迟 |
| `jitter` | bool | True | 是否启用抖动 |

## 断点续传

管线支持基于状态文件的断点续传（`scripts/pipeline/pipeline/state.py`）：

- **启用**：默认启用（`--resume` 默认 True）
- **禁用**：`--no-resume`
- **状态文件**：`<output>/.pipeline_state.json`
- **记录内容**：`completed_pages`（已完成页面列表）、`phase`（当前阶段）、`total_pages`
- **刷新间隔**：`--resume-flush-interval 100`（每 100 页刷新一次）

## 退出码

定义在 `scripts/pipeline/pipeline/orchestrator.py:35-44`：

| 退出码 | 常量 | 含义 |
|--------|------|------|
| 0 | `EXIT_SUCCESS` | 全部成功 |
| 1 | `EXIT_PARTIAL_SUCCESS` | 部分页面失败 |
| 10 | `EXIT_API_UNREACHABLE` | API 端点不可达 |
| 11 | `EXIT_PHASE_A_FAILURE` | 发现阶段失败 |
| 12 | `EXIT_PHASE_B_FAILURE` | Fetch/Convert 阶段失败 |
| 13 | `EXIT_PHASE_C_FAILURE` | 装配阶段失败 |
| 14 | `EXIT_STRATEGY_ERROR` | 策略验证失败 |
| 20 | `EXIT_INVALID_ARGS` | 无效参数 |
| 30 | `EXIT_VALIDATION_FAILURE` | L6 验证失败 |

## 关联文档

- [01 — 系统总览](01-overview.md) — 多后端架构全景
- [03 — 策略 Schema 参考](03-strategy-schema.md) — 策略 YAML frontmatter 字段权威参考
- [05 — 转换器架构](05-converter-architecture.md) — HTML→Markdown 两阶段转换模型

---
