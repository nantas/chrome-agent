# CONTEXT-MAP.md — chrome-agent 模块关系图

> 描述 Python 执行上下文的依赖和通信关系。`grill-with-docs` / `improve-codebase-architecture` skill 读取此文件理解架构约束。

## 依赖方向

```
┌──────────────────────────────────────────────────────────────────┐
│                    chrome-agent dispatch                         │
│                                                                  │
│  cli.mjs                                                         │
│    │                                                             │
│    ├── resolveAppPython() ────────▶ .venv/ (应用层)               │
│    │    explore main.py / freeze.py / iterate.py                  │
│    │    -m scripts.pipeline                                      │
│    │                                                             │
│    ├── scrapling-cli.sh preflight ──▶ ~/.cache/chrome-agent-     │
│    │    runScraplingPreflight()         scrapling/ (引擎层)      │
│    │                                                             │
│    ├── cloakbrowser-cli.sh preflight ▶ ~/.cache/chrome-agent-    │
│    │    runCloakbrowserFetch()          cloakbrowser/ (引擎层)   │
│    │                                                             │
│    └── engine-version-check.sh ─────▶ 全部引擎版本校验            │
│                                                                  │
│  doctor                                                          │
│    ├── explore_deps → resolveAppPython() → import bs4, yaml      │
│    ├── scrapling_preflight → scrapling-cli.sh preflight          │
│    ├── version_scrapling → engine-version-check.sh               │
│    ├── version_obscura → engine-version-check.sh                 │
│    └── version_cloakbrowser → engine-version-check.sh            │
│           (在 managed venv 内检测，不再硬编码 python3)            │
└──────────────────────────────────────────────────────────────────┘
```

## 共享内核（Shared Kernel）

| 组件 | 位置 | 被谁使用 | 核心依赖 |
|------|------|---------|---------|
| `converter.py` (HtmlToMarkdownConverter) | `scripts/lib/extraction/` | pipeline + explore | `selectolax` → 进应用层 venv |
| `preprocessor.py` (preprocess_html) | `scripts/lib/extraction/` | pipeline + explore | `beautifulsoup4` → 进应用层 venv |
| `config_resolver.py` | `scripts/lib/` | pipeline | `yaml` → 进应用层 venv |
| `strategy_loader.py` | `scripts/lib/` | pipeline + explore | `yaml` → 进应用层 venv |
| `python-resolver.mjs` (resolveAppPython) | `scripts/lib/` | cli.mjs (doctor + 所有应用层 spawn) | 无 Python 依赖 |

## 反腐败层（Anti-Corruption Layer）

| 边界 | 隔离方式 | 备注 |
|------|---------|------|
| 应用层 python vs 系统 python3 | `resolveAppPython()` 优先 `.venv/bin/python`，fallback `python3` | 系统 python3 是最后兜底，正常路径不经过它 |
| 引擎层 python vs 系统 python3 | `resolveManagedPath()` 解析 `~/.cache/` 下各自 venv | 每个引擎有独立的 `managed_path`，永不依赖系统 python3 |
| engine-registry 版本声明 vs 运行时检测 | `engine-version-check.sh` 统一入口，医生不直接写检测逻辑 | |

## Page discovery handoff boundary

`crawl` → `explore/page_discovery.py` → allpages/homepage → v2 manifest/summary → confirmation → pipeline. `lib/manifest_contract.py` validates handoff data; `lib/extraction/schema.py` validates shared consumer configuration. Bootstrap/scaffold drafts pass validated freeze before registry lookup eligibility.

## MediaWiki 完整性边界

`acquisition.py` 定义模式与动态 fallback → `cache.py::admit_page` 统一准入 → fetch 只跳过兼容缓存，失败标题交给 convert → convert 在 resume 前准入并计算指纹 → `convert_page_full` 复用 link-index/source_dir → assembly 只把本次成功页写入索引。Orchestrator 保留转换指纹并持久化失败原因。

存储键由 cache 管理；Markdown 输出名由 manifest/输出命名治理管理。二者不可用同一有损替换代替。恢复入口：[MediaWiki extraction recovery](docs/playbooks/mediawiki-extraction-recovery.md)。

## 正文准入边界

`lib/content_admission.py` 是 fetch 的共享准入内核：Explore probe/sample、CLI HTML 获取与 Scrapling 缓存读取、MediaWiki cache/convert 和 CDP fetch/convert 均消费它。Node 经应用层 Python JSON bridge 调用；引擎环境只获取原始内容。判定在 selector/Markdown 前执行，失败证据不进入成功缓存或当前 assembly。

## Crawl 转换与自检来源边界

`crawl (ordinary/sitemap/cache/prefetched)` → admitted HTML → `CLI convertCrawlHtml` → application Python `lib/crawl_conversion.py` → `convert_page_full`。已匹配策略转换失败终止该页，不切换通用转换器；本次成功 URL 集合决定 artifacts/merge。

`sample_converter` 声明 input_scope → main/iterate 以当前规则构造 `self_check.build_source_context` → run_checks：S1 应保留图片、S9 导航来源、S5 重复来源。raw 证据独立于转换清理结果，notes/skip 保留在汇总。
