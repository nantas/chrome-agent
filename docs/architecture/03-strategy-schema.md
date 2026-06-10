# 策略 Schema 参考（Strategy Schema Reference）

## 概述

站点策略文件是 chrome-agent 的行为配置权威来源。每个策略文件由 **YAML frontmatter**（机器可读配置）和 **Markdown 正文**（人类可读描述）组成。

**文件位置**：`sites/strategies/<domain>/strategy.md`

### 系统上下文图

```
┌─────────────────────────────────────────────────────────────────────┐
│                     chrome-agent Strategy Context                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐     ┌──────────────────┐     ┌────────────────┐  │
│  │  Explore     │     │  Strategy Files  │     │  Pipeline      │  │
│  │  Discovery   │────>│  (YAML+MD)       │────>│  Orchestrator  │  │
│  │  (生成策略)   │     │  sites/          │     │  orchestrator  │  │
│  │  explore/     │     │  strategies/     │     │  .py           │  │
│  └──────────────┘     └────────┬─────────┘     └───────┬────────┘  │
│                                │                        │          │
│                                │                        v          │
│                                │              ┌──────────────────┐ │
│                                │              │  _STRATEGY_      │ │
│                                └─────────────>│  REGISTRY        │ │
│                                               │  registry.py:61  │ │
│                                               └────────┬─────────┘ │
│                                                        │           │
│                                 ┌──────────────────────┤           │
│                                 v                      v           │
│                        ┌────────────────┐    ┌──────────────────┐  │
│                        │  Pipeline      │    │  Extraction      │  │
│                        │  build_        │    │  Engine          │  │
│                        │  pipeline()    │    │  (explore path)  │  │
│                        └────────────────┘    └──────────────────┘  │
│                                                                     │
│  ┌──────────────────┐                                               │
│  │  registry.json   │<── bootstrap-strategy / freeze 自动同步      │
│  │  (策略索引)       │    真源: frontmatter > registry.json          │
│  └──────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘
```
<!-- Source: scripts/lib/strategy_loader.py, scripts/pipeline/pipeline/registry.py -->

## 策略文件结构

```yaml
---
# ═══════════════════════════════════════════
# 必填字段
# ═══════════════════════════════════════════
domain: "example.wiki.gg"                # 站点域名（必填，用作匹配键）
description: "简短描述"                    # 站点描述（必填）
protection_level: "low"                   # 保护等级（必填）

# ═══════════════════════════════════════════
# 可选字段
# ═══════════════════════════════════════════
anti_crawl_refs:                          # 引用的反爬策略列表
  - default
  - rate-limit-api
backend: "weird-gloop-mediawiki-1.45"     # 后端家族标记（advisory，不参与运行时匹配）

# --- 站点结构描述 ---
structure:
  pages:                                  # 页面类型列表
    - id: main_page                       # 页面唯一 ID
      label: "Main Page"                  # 人类可读标签
      url_pattern: /wiki/Main             # URL 匹配模式
      url_example: "https://..."          # 示例 URL
      type: static_article                # 页面类型枚举
      content_type: wiki_main_page        # 内容类型枚举
      pagination: none                    # 分页模式
      links_to:                           # 出站链接目标
        - target: list_page               # 目标页面 ID
          selector: ".mw-parser-output a" # CSS 选择器
      requires_auth: false                # 是否需要认证

# --- API 配置 ---
api:
  platform: mediawiki                     # 平台类型（必填，目前仅支持 "mediawiki"）
  platform_variant: standard              # 平台变体：standard | fandom | wiki-gg
  base_url: "https://example.wiki.gg/api.php"  # API 端点
  capabilities:                           # 声明 API 能力
    - page_list
    - category_lookup
    - html_parse
    - wikitext_parse
    - imageinfo_query
  namespaces: [0, 3000]                   # MediaWiki 命名空间过滤

  # 内容配置文件（决定管线各阶段使用的策略实现）
  content_profile:
    discovery_strategy: "category_members"
    content_acquisition: "html_rendered"
    link_resolver: "short_name_with_cross_namespace"
    template_processor: "structured_with_lua_fallback"
    list_page_assembler: "hybrid_frontmatter_and_rendered"

  # 速率限制
  rate_limit:
    tier: "moderate"                      # 引用反爬策略中的速率限制模板
    concurrency: 2                        # 本地覆盖：并发数
    batch_delay_ms: 500                   # 本地覆盖：批次延迟
    retry:                                # 本地覆盖：重试配置
      max_retries: 5
      initial_delay_sec: 1.0
      backoff_multiplier: 2.0
      max_delay_sec: 60.0
      jitter: true

  # 排除分类
  exclude_categories:                     # 顶级排除（优先级最高）
    - "Hidden pages"
  homepage:                               # 首页发现配置
    exclude_categories:                   # 遗留排除（优先级较低）
      - "Deprecated"

  # 分类体系
  taxonomy:
    list_pages:                           # 列表页 → 输出目录映射
      Cards_List: "Cards"
      Relics_List: "Relics"
    page_categories:                      # 页面分类映射
      Items: "Items"
    category_filters: []                  # 分类过滤规则

  # 首页配置（存在时启用 homepage discovery）
  homepage:
    url: "/wiki/Main_Page"
    categories_selector: ".categories a"
    # ...其他首页解析规则

  # 图片过滤
  image_filtering:
    list_pages: base_only                 # 列表页图片过滤策略

  # 页面类型映射
  page_type_map:
    summary_pages:
      - Items
      - Weapons
    entity_pages:
      items_category: "Category:Items"

# --- 提取规则 ---
extraction:
  # 页面级提取规则（供 explore 样本转换使用）
  fields:
    - name: title
      selector: "h1.firstHeading"
      type: text
    - name: description
      selector: ".mw-parser-output p:first-of-type"
      type: text
---
```

## 字段详细说明

### 字段层级树

```
strategy.md (YAML frontmatter)
├── ✅ domain: string
├── ✅ description: string
├── ✅ protection_level: "low" | "medium" | "high"
├── ❌ anti_crawl_refs: string[]
├── ❌ backend: string
├── ❌ structure
│   └── ❌ pages[]
│       ├── id
│       ├── label
│       ├── url_pattern
│       ├── url_example
│       ├── type
│       ├── content_type
│       ├── pagination
│       ├── ❌ links_to[]
│       │   ├── target
│       │   └── selector
│       └── requires_auth
├── ❌ api
│   ├── ✅ platform: "mediawiki"
│   ├── ❌ platform_variant: "standard" | "fandom" | "wiki-gg"
│   ├── ❌ base_url: string
│   ├── ❌ capabilities: string[]
│   ├── ❌ namespaces: int[]
│   ├── ❌ content_profile
│   │   ├── ❌ discovery_strategy: "allpages" | "category_members"
│   │   ├── ❌ content_acquisition: "wikitext_only" | "hybrid_..." | "html_rendered"
│   │   ├── ❌ link_resolver: "exact_title_match" | "short_name_with_cross_namespace"
│   │   ├── ❌ template_processor: "simple_substitution" | "structured_..." | "fandom_infobox"
│   │   └── ❌ list_page_assembler: "frontmatter_driven" | "hybrid_..."
│   ├── ❌ rate_limit
│   │   ├── ❌ tier
│   │   ├── ❌ concurrency
│   │   ├── ❌ batch_delay_ms
│   │   └── ❌ retry { max_retries, initial_delay_sec, ... }
│   ├── ❌ exclude_categories: string[]
│   ├── ❌ homepage { url, categories_selector, ... }
│   ├── ❌ taxonomy { list_pages, page_categories, category_filters }
│   ├── ❌ image_filtering { list_pages }
│   ├── ❌ page_type_map { summary_pages, entity_pages }
│   ├── ❌ card_images
│   └── ❌ card_list_splitting
└── ❌ extraction
    └── ❌ fields[]
        ├── name
        ├── selector
        └── type

✅ = Required  ❌ = Optional
```
<!-- Source: sites/strategies/<domain>/strategy.md frontmatter schema -->

### 顶级字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `domain` | string | ✅ | 站点域名，用作运行时策略匹配键 |
| `description` | string | ✅ | 站点描述 |
| `protection_level` | string | ✅ | 保护等级：`low` / `medium` / `high` |
| `anti_crawl_refs` | string[] | ❌ | 引用的反爬策略 ID 列表 |
| `backend` | string | ❌ | 后端家族标记（advisory），不参与运行时匹配 |
| `structure` | object | ❌ | 站点结构描述（页面类型、链接关系） |
| `api` | object | ❌ | API 配置（MediaWiki 站点必填） |
| `extraction` | object | ❌ | 提取规则（供 explore 使用） |
| `samples` | array | ❌ | 样本页面列表（供站点回归测试使用） |

### `api` 字段

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `platform` | string | ✅ | — | 平台类型，当前仅支持 `"mediawiki"` |
| `platform_variant` | string | ❌ | `"standard"` | 平台变体枚举 |
| `base_url` | string | ❌ | 自动探测 | MediaWiki API 端点 URL |
| `capabilities` | string[] | ❌ | — | API 能力声明（用于校验） |
| `namespaces` | int[] | ❌ | `[0]` | 命名空间过滤 |
| `content_profile` | object | ❌ | 见默认值 | 管线策略选择（见下表） |
| `rate_limit` | object | ❌ | — | 速率限制配置 |
| `exclude_categories` | string[] | ❌ | `[]` | 顶级分类排除 |
| `homepage` | object | ❌ | — | 首页发现配置 |
| `taxonomy` | object | ❌ | — | 分类体系（list_pages, page_categories） |
| `image_filtering` | object | ❌ | — | 图片过滤规则 |
| `page_type_map` | object | ❌ | — | 页面类型映射 |
| `card_images` | object | ❌ | — | 卡牌图片配置 |
| `card_list_splitting` | object | ❌ | — | 列表页拆分配置 |

### `platform_variant` 枚举

| 值 | 说明 |
|------|------|
| `standard` | 标准 MediaWiki（默认值，未指定时使用） |
| `fandom` | Fandom 托管的 MediaWiki |
| `wiki-gg` | wiki.gg 托管的 MediaWiki |

管线在 `run_pipeline()` 中解析此字段并传递给各阶段函数。当前阶段仅接受和记录，不实现行为分支（`orchestrator.py:139-140`）。

### `samples` 字段

样本页面声明，用于站点样本回归测试（`python3 scripts/test_runner.py site-samples`）。

| 子字段 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `page` | string | ✅ | URL 路径或 cache-safe 路径，标识页面（如 `Packages/.../Pages/Page_239857945.html`） |
| `label` | string | ✅ | 人类可读描述，说明该页面的代表性特征 |

示例：

```yaml
samples:
  - page: "Packages/Docs/Guides/Online_Play_Guide/contents/Pages/Page_239857945.html"
    label: "复杂嵌套表格页面"
  - page: "Packages/Network/Guides/NX-Account_Guide/contents/Pages/Page_106359813.html"
    label: "纯文本无表格页面"
```

- 默认值：空列表（不声明 `samples` 时等同无样本）
- test_runner 扫描 `sites/strategies/*/strategy.md` 中此字段，为每个 `(domain, page)` 动态生成 `unittest.TestCase`
- 样本数据从 `.cache/` 读取，golden file 存放在 `sites/strategies/<domain>/samples/<page>.md`

## content_profile 合法值

### content_profile 策略路由图

```
content_profile (YAML)
    │
    ├── discovery_strategy
    │       │
    │       ├── "allpages"          ──→ registry["discovery"]["allpages"]
    │       │                        ──→ AllPagesDiscoveryStrategy
    │       └── "category_members"   ──→ registry["discovery"]["category_members"]
    │                                 ──→ CategoryMembersDiscoveryStrategy
    │
    ├── content_acquisition
    │       │
    │       ├── "wikitext_only"               ──→ registry["content_acquisition"]["wikitext_only"]
    │       │                                    ──→ WikitextOnlyAcquisitionStrategy
    │       ├── "hybrid_wikitext_plus_rendered" ──→ registry["content_acquisition"]["hybrid_..."]
    │       │                                    ──→ HybridAcquisitionStrategy
    │       └── "html_rendered"                 ──→ registry["content_acquisition"]["html_rendered"]
    │                                            ──→ HtmlRenderedAcquisitionStrategy
    │
    ├── link_resolver
    │       │
    │       ├── "exact_title_match"              ──→ registry["link_resolver"]["exact_title_match"]
    │       │                                      ──→ ExactTitleLinkResolver
    │       └── "short_name_with_cross_namespace" ──→ registry["link_resolver"]["short_name_..."]
    │                                              ──→ ShortNameLinkResolver
    │
    ├── template_processor
    │       │
    │       ├── "simple_substitution"         ──→ registry["template_processor"]["simple_..."]
    │       │                                    ──→ SimpleSubstitutionTemplateProcessor
    │       ├── "structured_with_lua_fallback" ──→ registry["template_processor"]["structured_..."]
    │       │                                    ──→ StructuredTemplateProcessor
    │       └── "fandom_infobox"               ──→ registry["template_processor"]["fandom_infobox"]
    │                                            ──→ FandomInfoboxTemplateProcessor
    │
    └── list_page_assembler
            │
            ├── "frontmatter_driven"               ──→ registry["list_page_assembler"]["frontmatter_..."]
            │                                        ──→ FrontmatterDrivenListPageAssembler
            └── "hybrid_frontmatter_and_rendered"   ──→ registry["list_page_assembler"]["hybrid_..."]
                                                     ──→ HybridListPageAssembler
```
<!-- Source: scripts/pipeline/pipeline/registry.py:_STRATEGY_REGISTRY -->

以下 ID 来自 `_STRATEGY_REGISTRY`（`scripts/pipeline/pipeline/registry.py:61`）。

> **注意**：此清单为快速参考，不替代 `_STRATEGY_REGISTRY` 作为权威来源。以代码为准。

| 维度 | YAML 字段名 | 合法 ID | 说明 |
|------|------------|---------|------|
| **discovery** | `discovery_strategy` | `allpages` | 通过 `action=query&list=allpages` 枚举所有页面 |
| | | `category_members` | 通过分类成员查询发现页面 |
| **content_acquisition** | `content_acquisition` | `wikitext_only` | 仅获取 wikitext 源码 |
| | | `hybrid_wikitext_plus_rendered` | 同时获取 wikitext 和渲染后 HTML |
| | | `html_rendered` | 仅获取渲染后 HTML |
| **link_resolver** | `link_resolver` | `exact_title_match` | 精确标题匹配 |
| | | `short_name_with_cross_namespace` | 短名称匹配，支持跨命名空间 |
| **template_processor** | `template_processor` | `simple_substitution` | 简单模板替换 |
| | | `structured_with_lua_fallback` | 结构化处理，Lua 模板降级 |
| | | `fandom_infobox` | Fandom Infobox 模板专用处理器 |
| **list_page_assembler** | `list_page_assembler` | `frontmatter_driven` | 前端数据驱动的列表页装配 |
| | | `hybrid_frontmatter_and_rendered` | 混合前端数据与渲染内容装配 |

### 默认值

未指定 `content_profile` 时使用以下默认值（`registry.py:44`）：

| 维度 | 默认 ID |
|------|---------|
| discovery | `allpages` |
| content_acquisition | `wikitext_only` |
| link_resolver | `exact_title_match` |
| template_processor | `simple_substitution` |
| list_page_assembler | `frontmatter_driven` |

### 扩展协议

新增策略实现必须严格遵循顺序：
1. 实现 Strategy 类（继承 Protocol 接口）
2. 注册到 `_STRATEGY_REGISTRY` 对应维度
3. 在策略文件中引用已注册的 ID

严禁在 Step 2 之前执行 Step 3。违反此顺序的策略文件引用会被 pipeline 启动校验拒绝（`EXIT_STRATEGY_ERROR`）。

## registry.json 格式

### 站点策略 registry.json

**路径**：`sites/strategies/registry.json`

```json
{
  "entries": [
    {
      "domain": "example.wiki.gg",
      "description": "站点描述",
      "protection_level": "low",
      "page_types": ["static_article"],
      "pagination": ["none"],
      "entry_points": ["wiki_article"],
      "anti_crawl_refs": [],
      "file": "example.wiki.gg/strategy.md",
      "backend": "weird-gloop-mediawiki-1.45"
    }
  ]
}
```

**治理规则**：
- `registry.json` 仅为索引摘要，与 frontmatter 不一致时以 frontmatter 为准
- `bootstrap-strategy` 命令自动更新 registry
- 手动创建策略需手动更新 registry

### 反爬策略 registry.json

**路径**：`sites/anti-crawl/registry.json`

```json
{
  "entries": [
    {
      "id": "cloudflare-turnstile",
      "protection_type": "cloudflare_turnstile",
      "sites": ["wiki.supercombo.gg"],
      "detection_summary": "HTTP 403, page title 'Just a moment...'",
      "primary_engine": "scrapling-stealthy-fetch",
      "file": "cloudflare-turnstile.md"
    }
  ]
}
```

## 反爬策略文件格式

**路径**：`sites/anti-crawl/<mechanism>.md`

```yaml
---
id: default                           # 策略 ID（与文件名一致）
protection_type: none                 # 保护类型枚举
sites: []                             # 受影响站点列表
detection:                            # 检测信号
  http:
    status_codes: []
  page_content:
    has_content: true
engine_priority:                      # 引擎优先级列表
  - engine: scrapling-get
    rank: 1
  - engine: scrapling-fetch
    rank: 2
    config:
      network_idle: true
success_signals:                      # 成功判定信号
  page_content:
    has_content: true
failure_signals:                      # 失败判定信号
  page_content:
    dom_markers: []
  http:
    status_codes: [403, 429]
---
```

### 反爬策略 YAML 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 策略标识符，与文件名（去 `.md`）一致 |
| `protection_type` | string | 保护机制类型 |
| `sites` | string[] | 受影响站点域名列表 |
| `detection` | object | 检测规则（HTTP 状态码、页面内容特征） |
| `engine_priority` | array | 引擎尝试优先级列表 |
| `success_signals` | object | 成功判定条件 |
| `failure_signals` | object | 失败判定条件 |
| `rate_limit_tiers` | object | 速率限制模板（可选，被站点策略 `api.rate_limit.tier` 引用） |

### 速率限制模板

反爬策略可定义 `rate_limit_tiers` 供站点策略引用：

```yaml
rate_limit_tiers:
  moderate:
    concurrency: 2
    batch_delay_ms: 500
    retry:
      max_retries: 5
      initial_delay_sec: 1.0
      backoff_multiplier: 2.0
      max_delay_sec: 60.0
      jitter: true
  aggressive:
    concurrency: 1
    batch_delay_ms: 2000
    retry:
      max_retries: 10
      initial_delay_sec: 2.0
      backoff_multiplier: 3.0
      max_delay_sec: 120.0
      jitter: true
```

## 关联文档

- [01 — 系统总览](01-overview.md) — 多后端架构全景
- [02 — 管线数据流](02-pipeline-flow.md) — 策略驱动的五阶段管线
- [04 — CLI 参考](04-cli-reference.md) — 所有命令与管线子命令的参数说明
- [05 — 转换器架构](05-converter-architecture.md) — extraction 规则如何被消费

---
