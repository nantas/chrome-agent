# 管线数据流（Pipeline Data Flow）

## 概述

MediaWiki API 提取管线（`scripts/pipeline/`）是 chrome-agent 针对 MediaWiki 平台站点的结构化内容提取核心。管线由 `orchestrator.py` 中的 `run_pipeline()` 函数编排，支持五种阶段独立或组合执行。

**权威来源**：`scripts/pipeline/pipeline/orchestrator.py:76` — `run_pipeline(args: argparse.Namespace) -> int`

**Sitemap 发现路径**：对于无 MediaWiki API 的静态文档站点，存在独立的 sitemap 发现路径——`sitemap.xml` 解析（支持 `<sitemapindex>`：自动迭代子 sitemap、串行 fetch、`Set` 去重合并；单子 sitemap 失败不阻断，全失败才 handoff `sitemap_all_subs_failed`）→ `page_pattern` include 过滤 → `discovery.exclude_patterns` 排除 → 自动分组 → 输出 `page_manifest.json` → 确认闸门（confirmation gate）→ 线性 scrapling 提取。该路径由策略的 `discovery.method: sitemap` 触发，与 MediaWiki API 管线互斥（详见 [03 — 策略 Schema](03-strategy-schema.md) 与 [04 — CLI 参考](04-cli-reference.md)）。

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
                     ┌──────▼──────┐
                     │  --from-     │
                     │  manifest    │
                     │  (explore 产出)│
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │  page_       │
                     │  manifest    │
                     │  .json       │
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
                   │ v2-<sha256(title)>.json │
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
| **流程** | 1. 检查 `.cache/` 已缓存页面（除非 `--re-fetch`） → 2. **快速路径**：若所有页面通过身份/模式/载荷准入则直接返回 `skipped=total` → 3. **预过滤**：分离兼容/缺失或不兼容页面，仅后者提交线程池 → 4. 并发获取未缓存页面（`ThreadPoolExecutor`，concurrency 由 rate_limit 控制） → 5. `time.sleep(batch_delay_sec)` 仅在实际网络请求（`status=ok`）时执行 → 6. 写入 `.cache/<platform>/<domain>/v2-<sha256(title)>.json` |
| **输出** | Stats dict（total, fetched, skipped, failed） |
| **副作用** | 写入 `.cache/` 持久化缓存 |

### Fetch CDP — Chrome CDP 获取

| 项目 | 说明 |
|------|------|
| **入口** | `scripts/pipeline/pipeline/phases/fetch_cdp.py` — `run_fetch_cdp()` |
| **触发条件** | 通过 CDP 会话获取非 MediaWiki 站点的页面内容 |
| **输入** | 页面 URL 列表、domain、repo_root、CDP 提取回调函数 |
| **流程** | 1. 对每个页面检查 `.cache/chrome-cdp/` 是否已缓存 → 2. 未命中则通过 CDP 回调提取 HTML → 3. 调用 `save_page_cache()` 写入缓存 |
| **输出** | Stats dict（total, fetched, skipped, failed） |
| **副作用** | 写入 `.cache/chrome-cdp/<domain>/` 持久化缓存 |

与 MediaWiki Fetch 的关系：`fetch.py` 强依赖 `ApiClient` 和 `ContentAcquisitionStrategy`，CDP fetch 使用回调函数接口，两者保持独立避免耦合。

### Convert HTML — HTML 转 Markdown

| 项目 | 说明 |
|------|------|
| **入口** | `scripts/pipeline/pipeline/phases/convert_html.py` — `run_convert_html()` |
| **触发条件** | 需要将 CDP 缓存的 HTML 转换为 Markdown 时调用 |
| **输入** | 页面列表、domain、repo_root、output_dir |
| **流程** | 1. 从 `.cache/chrome-cdp/` 读取缓存的 HTML → 2. 调用 `html_to_markdown()` 转换（含表格 rowspan/colspan 处理） → 3. 写入 `.md` 文件到输出目录 |
| **输出** | Stats dict（total, converted, skipped, failed） |
| **副作用** | 写入输出目录 `.md` 文件 |

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

### L6 验证 — 图片可用性校验的 URL→`File:` 解析

`validate_images`（`scripts/pipeline/strategies/__init__.py`）从输出 Markdown 的图片 URL 推导待核验的 `File:` 名，三级解析（`_image_file_title`）：

1. 含 `Special:Redirect/file/`：取前缀后、`?` 前部分；
2. 含 `/revision/` 的 Fandom CDN URL（`static.wikia.nocookie.net/.../<name>.png/revision/latest/scale-to-width-down/111?cb=...`）：取 `/revision/` 前路径末段（真实文件名，而非尺寸参数）；
3. 其余 URL：取路径末段。

修复前 CDN 变换后缀被当作文件名（`111?cb=...`），单站产生 ~17k 条 `api_missing` 误报。回归守护：`tests/test_validate_images_filename.py`。

## 缓存机制

缓存由 `scripts/pipeline/pipeline/cache.py` 管理，实现 Fetch 与 Convert 解耦。新文件为 `.cache/<platform>/<domain>/v2-<sha256(exact-title)>.json`，包含原始 `title`、schema version、acquisition 标记、来源及相应载荷。枚举读取 metadata，不从文件名反解标题。唯一临时文件加原子替换保证完整写入；安全旧文件候选仅在 title 精确相等时可读，读取不会迁移或重命名旧文件。详见 [ADR 0014](../adr/0014-mediawiki-cache-identity.md)。CDP 调用方仍决定自己的 title 身份，但通过同一存储层保存。

`admit_page()` 统一检查 title、已记录 API 来源、当前 resolved acquisition 和必需载荷。HTML 要求非空 html；wikitext 要求字符串；hybrid 动态 fallback 要求 rendered_html。markerless 旧缓存只在表示明确时内存适配。

- Fetch 只跳过兼容条目；全部兼容时不创建线程池；新响应准入后才写缓存。`--re-fetch` 强制获取，本次失败标题传给 convert，旧缓存不能掩盖重抓失败；fetch-only 失败返回非零。
- Convert 在 resume 之前准入，不隐式联网。只有 completed、目标文件和转换指纹全部匹配才跳过。指纹覆盖 raw/config/acquisition/输出及链接上下文/converter revision，排除 fetched_at。
- HTML 生产路径委托共享 `convert_page_full` 五步；成功落盘才存指纹。编排层保留指纹，不重新并入旧 completion；结构化失败写入 extraction_results，assembly 不把失败页或旧目录残留作为本次成功输出。

缺 HTML 时必须重新获取，不能仅离线重转。实际恢复先审核新 manifest，再选择重抓或完整 HTML 缓存重转，详见 [恢复手册](../playbooks/mediawiki-extraction-recovery.md)。

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

- [00 — 目标架构](00-target-architecture.md) — **架构真源**：pipeline 作为 B 轴执行路径的 4 维坐标
- [01 — 系统总览](01-overview.md) — 多后端架构全景

---

## Manifest admission and list indexes

Manifest/phase validation precedes API probing. Pipeline accepts fetch/convert/assemble/all and never performs discover. Legacy manifests are copied for unambiguous metadata adaptation without changing paths or page membership. Included `is_list_page` identities and canonical list decisions drive real indexes; absent/excluded detached list content cannot expand scope. Link indexes target the resulting index.md. New discovery assigns Misc only to unclassified ns0 pages with no existing directory.
