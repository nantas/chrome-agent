---
title: Neon Abyss Fandom Wiki Crawl — 问题分析与修复记录
date: 2026-05-13
status: draft
tags: [postmortem, mediawiki, pipeline, phase-b, strategy-compatibility]
---

# Neon Abyss Fandom Wiki Crawl — 问题分析与修复记录

## 概述

目标：完整爬取 [neonabyss.fandom.com](https://neonabyss.fandom.com/wiki/Neon_Abyss_Wiki) 的 566 个内容页面。

入口：`chrome-agent crawl "https://neonabyss.fandom.com/wiki/Neon_Abyss_Wiki"`

使用策略：`sites/strategies/neonabyss.fandom.com/strategy.md`

实际交付：通过独立脚本完成抽取与后处理，未完全依赖 `mediawiki-api-extract` 流水线。

---

## 问题清单

### P1. Phase B 全部页面失败 — `HtmlRenderedAcquisitionStrategy` 不处理 missingtitle

**现象**

Phase B 中 566 页面的 77.6% 失败，错误全部为：

```
[WARNING] Page X: 'NoneType' object has no attribute 'replace'
```

仅有少量 success（最终 127/566）。

**根因**

`HtmlRenderedAcquisitionStrategy.fetch_page_content()` 调用 `action=parse&prop=text` 获取渲染 HTML。当页面不存在（API 返回 `missingtitle` 错误）时，`client.parse()` 抛出 `RuntimeError("API error: {'code': 'missingtitle', ...}")`。异常被 `process_single_page()` 的 try/except 捕获，返回 `{"status": "error", "error": "'NoneType' object has no attribute 'replace'"}`。

但并非全部页面都 missingtitle。测试发现 **Bosses**、**Ara**、**Rona** 等页面返回 `missingtitle`，而 **Acorn**、**Items** 等返回正常 HTML。这说明 Phase A 的 `allpages` API 发现包含了许多非内容页面（redirects、不存在的页面、术语条目等）。

Phase A 未做进一步过滤，导致 Phase B 试图 fetch 不存在的页面。

**影响**

- 流水线退出码 12（`EXIT_PHASE_B_FAILURE`）
- 无法自动 fallback 到 Scrapling（在 `chrome-agent-cli.mjs` 中已实现 fallback 逻辑，但需 exit code >= 10 才能触发）

**修复方向**

1. `HtmlRenderedAcquisitionStrategy.fetch_page_content()` 应区分 `missingtitle` 和真正的 API 错误，对 missingtitle 返回空内容而非抛异常。
2. Phase A 应增加内容页验证步骤（如 `action=query&prop=info&titles=...`），过滤掉不存在的页面后再进入 Phase B。
3. `_process_html_page()` 中 `raw.get("html", "")` 应防御性地将 None 转为空字符串（当前 `get("html", "")` 在 key 存在但值为 None 时仍返回 None）。

### P2. 策略注册表缺失 `short_name` 和 `fandom_infobox` 实现

**现象**

```
[WARNING] Unknown strategy ID 'short_name' for link_resolver, using default 'exact_title_match'
[WARNING] Unknown strategy ID 'fandom_infobox' for template_processor, using default 'simple_substitution'
```

**根因**

`neonabyss.fandom.com/strategy.md` 声明了：

```yaml
content_profile:
  link_resolver: "short_name"
  template_processor: "fandom_infobox"
```

但在 `pipeline/orchestrate.py` 的 `_STRATEGY_REGISTRY` 中：

- `link_resolver` 只有 `{"allpages": ..., "category_members": ...}` — 无 `short_name`
- `template_processor` 只有 `{"simple_substitution": ..., "structured_with_lua_fallback": ...}` — 无 `fandom_infobox`

**影响**

降级到默认实现，Fandom 特有的 `{{#invoke}}` 模板和跨命名空间链接无法正确处理，影响 WikiText 转换质量。

**修复方向**

1. 实现 `ShortNameLinkResolver` 策略类（或确认 `short_name` 是否等于现有 `short_name_with_cross_namespace`）。
2. 实现 `FandomInfoboxTemplateProcessor` 策略类，处理 Fandom 特有的 infobox 模板（`<infobox>` 或 `{{Infobox}}`）。
3. 策略注册表应支持动态加载第三方策略包。

### P3. 默认 bash timeout 导致流水线中断

**现象**

```
Command timed out after 120 seconds
```

**根因**

首次运行 `chrome-agent crawl` 时，bash 工具默认 timeout 为 120 秒。对于 566 页面（concurrency=5, batch_delay_ms=500），Phase B 约需 3-5 分钟。管道本身设了 600 秒 timeout，但被 bash wrapper 截断。

**影响**

Phase A 完成（生成了 `page_manifest.json`），但 Phase B 未启动即中断。操作者需要手动重试并设置更长 timeout。

**修复方向**

1. `chrome-agent-cli.mjs` 的 crawl 路径：在 spawn MediaWiki pipeline 时增加 stderr 输出和超时警告。
2. 文档中应说明大 wiki 的预期运行时间和建议 timeout。
3. 考虑在 pipeline 层面输出进度心跳，帮助外部 caller 判断是否仍在运行。

### P4. 无 checkpoint/resume 机制

**现象**

Phase B 失败后，重新运行必须从头开始（Phase A 再次执行全部 566 页面的 API 发现）。虽然 `--phase B C` 可以跳过 Phase A，但需要手动指定。

**根因**

`run_pipeline()` 中 Phase 切换逻辑判断 `--phase` 后决定是否加载已有 manifest：

```python
if "A" in phases or "all" in phases:
    manifest = run_phase_a(...)
else:
    manifest_path = os.path.join(args.output, "page_manifest.json")
    # load existing
```

但 Phase B 结果只保存在 `extraction_results.json`，没有增量 checkpoint——如果 Phase B 中途中断，已成功的页面需要重新 fetch。

**影响**

对于 500+ 页面的大型 wiki，每次失败都需要重跑全部 Phase B，消耗大量 API 配额和时间。

**修复方向**

1. Phase B 增加逐页面 checkpoint：每处理 N 个页面就持久化一次 `extraction_results.json`。
2. 启动时检测已有结果，跳过已成功的页面（可选的 `--skip-existing` 参数）。
3. 支持通过 `--resume` 自动检测上次中断位置。

### P5. Fandom 特有的 API 行为未在策略中体现

**现象**

- 部分页面 `action=parse` 返回 `error: missingtitle` 但 `action=query&list=allpages` 包含它们（说明它们是空的转发页或不再存在的条目）。
- Fandom 使用 `static.wikia.nocookie.net` CDN 分发图片，与通用 MediaWiki 的 `Special:Redirect/file` 不同。
- Fandom 的 CSS 类名（`ambox`, `plainlinks`, `mw-parser-output` 等）需要特定清理规则。

**根因**

策略声明 `platform: mediawiki` 但没有声明 Fandom 的任何特有行为和适配需求。

**影响**

- 内容页存在性验证缺失（P1 的深层原因）
- 图片链接可能无法正确解析
- HTML 清理规则不完全

**修复方向**

1. 策略 schema 增加 `api.platform_variant` 字段，允许声明 `fandom` 子类型。
2. MediaWiki pipeline 根据 platform_variant 加载对应的 HTML 清理规则、模板处理器和错误处理策略。
3. 对 Fandom variant：增加 pre-check API 调用过滤不存在页面；增加 Fandom 专有的 CSS 清理规则。

### P6. `_process_html_page` None-safety 缺失

**现象**

核心错误 `'NoneType' object has no attribute 'replace'` 的精确调用栈在现有 warn 日志中不可见（被 `except Exception` 吞没）。

**根因**

```python
def _process_html_page(raw: dict, title: str, ...):
    html = raw.get("html", "")   # ← raw["html"] is None, get returns None
    ...
    cleaned = converter.clean_html(html)  # ← selectolax.HTMLParser(None)
```

Python 的 `dict.get(key, default)` 仅在 key 不存在时返回 default。当 key 存在但 value 为 `None` 时，返回 `None`。

**修复方向**

1. 改为 `raw.get("html") or ""` 或显式判断 `if not raw.get("html")`。
2. 异常处理增加完整 traceback 日志：当前 `except Exception as e` 只输出 `str(e)`，不记录调用栈。
3. 为 `HtmlToMarkdownConverter.clean_html()` 和 `.convert()` 增加 None/空字符串防护。

### P7. Phase A 包含不存在的页面

**现象**

Manifest 中 566 页面包含 **Bosses**、**Ara**、**Rona** 等 `action=parse` 返回 `missingtitle` 的页面，以及 `_tr` 翻译页面。

**根因**

`AllPagesDiscoveryStrategy` (Phase A) 使用 `action=query&list=allpages`，返回所有主命名空间（ns=0）的条目，包括：

- 无实际内容的空页面/转发
- `_tr` 后缀的翻译页面（由 Fandom 多语言系统自动创建）
- 可能已被删除但 `allpages` 仍残留的条目

**影响**

导致 Phase B 浪费约 15-20% 的 API 请求在不存在的页面上，增加了失败率和处理时间。

**修复方向**

1. Phase A 在生成 manifest 前增加 `action=query&prop=info&titles=...` 批量验证。
2. 允许策略配置排除规则（如 `exclude_patterns: ["*_tr$"]`）。
3. Phase B 遇到 missingtitle 时应 gracefully skip 而非视为 failure。

---

## 实际解决方案

由于上述问题，最终使用独立脚本直接调用 MediaWiki API 完成抽取：

1. 使用 `action=parse&prop=text|wikitext&format=json` 双模式获取内容
2. 对 missingtitle 等 error 直接 skip，不记入 failure
3. 简易 HTML→Markdown 转换器（基于 regex，不依赖 selectolax）
4. 后处理独立脚本完成：列表页移至根目录、链接本地化、创建 index.md

**转换质量 Trade-off**：regex 转换器 vs pipeline 的 selectolax + structured infobox 方案，质量略低（表格未完全结构化、部分 HTML 标记残余），但胜在能完整拿到所有存在页面的内容。

---

## 后续建议优先级

| 优先级 | 问题 | 建议行动 |
|--------|------|----------|
| P0 | P1 + P6 (Phase B None-safety) | 修复 `_process_html_page` 的 None 防护，增加 missingtitle 优雅处理 |
| P0 | P7 (Phase A 过滤) | Phase A 增加内容页验证，支持排除规则 |
| P1 | P2 (策略注册表) | 注册 `short_name` 和 `fandom_infobox` 策略类 |
| P2 | P4 (Checkpoint) | Phase B 增加逐批持久化 checkpoint |
| P2 | P5 (Fandom variant) | 引入 `platform_variant: fandom` 体系 |
| P3 | P3 (Timeout) | 文档补充大 wiki timeout 说明 |

---

*文档目的：记录 MediaWiki API 抽取流水线在 Fandom wiki 上的兼容性问题，为后续 platform_variant 体系设计和 pipeline 健壮性改进提供输入。*
