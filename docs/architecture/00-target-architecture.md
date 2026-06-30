# 00 — Target Architecture

> **Status**: Draft (Stage 1 in progress). This document defines the 4-dimensional
> target architecture for chrome-agent. It is the ruler against which Stage 3
> will measure all drift.
>
> **Parent**: [4d-architecture-refactor.md](../plans/4d-architecture-refactor.md)
> **Reference**: [ADR 0013](../adr/0013-four-dimensional-domain-model.md)
> **Diagnosis**: [00-architecture-review.md](00-architecture-review.md)

## §1 Current Capability Map (Baseline)

> Captured 2026-06-30 from code inspection. This is the "as-is" — the target
> profiles in §3 define the "to-be."

### 1.1 Convert

| # | Module | Kernel | 执行路径 | 策略变体 | 输入格式 | LOC | 状态 |
|---|--------|--------|---------------------|-------------|-------------------|-----|--------|
| C1 | `lib/extraction/converter.py` | selectolax | pipeline + explore | generic | MediaWiki HTML | 977 | ✅ Shared kernel |
| C2 | `lib/extraction/html_to_markdown.py` | Python regex | pipeline(cdp) | generic | Generic HTML | 337 | ⚠️ Independent path |
| C3 | `chrome-agent-cli.mjs:1137` `htmlToMarkdown()` | JS regex | scrapling traversal | generic | Generic HTML | ~100 | ⚠️ 3rd impl (Node.js) |
| C4 | `pipeline/converters/wikitext_to_md.py` | Custom parser | pipeline | generic | Wikitext | ~250 | ✅ 输入格式合法 |
| C5 | `pipeline/converters/fandom_html_to_markdown.py` | bs4+markdownify | pipeline | fandom | HTML | 271 | ❌ Dead code |
| C6 | `explore/sample_converter.py` | BS4 (importlib wrapper) | explore | generic | MediaWiki HTML | ~380 | ⚠️ 执行路径镜像 + extract |
| C7 | `pipeline/pipeline/phases/convert.py` | Orchestrator → C1 | pipeline | generic | — | — | Phase |
| C8 | `pipeline/pipeline/phases/convert_html.py` | Orchestrator → C2 | pipeline(cdp) | generic | — | — | Phase |

**关键问题**：
- Generic HTML→MD has **3 independent implementations** (C1/C2/C3), zero shared code, zero equivalence declarations
- C5 (fandom) is dead code — zero callers, all features covered by C1 + preprocessor cleanup ops
- C6 (sample_converter) conflates A=convert + A=extract in one module; uses `importlib.import_module` to reach C1
- C2 and C3 are both regex-based but in different languages (Python vs JS)

### 1.2 Fetch

| # | Module | Location | B (Execution Path) | D (Input Format) | Language |
|---|--------|----------|---------------------|-------------------|----------|
| F1 | `runScraplingFetch()` | `.mjs:750` | scrapling traversal + explore | HTML rendered | Node.js |
| F2 | `runCloakbrowserFetch()` | `.mjs:778` | fallback | HTML rendered | Node.js |
| F3 | `runMediawikiApiFetch()` | `.mjs:817` | scrapling traversal | API JSON | Node.js |
| F4 | `run_fetch()` | `pipeline/phases/fetch.py` | pipeline batch | API JSON | Python |
| F5 | `run_fetch_cdp()` | `pipeline/phases/fetch_cdp.py` | pipeline(cdp) | chrome-cdp cache | Python |
| F6 | `probe()` | `explore/probe_chain.py` | explore | multi-engine HTML | Python |
| F7 | `cloakbrowser_fetcher.py` | standalone | fallback | HTML rendered | Python |

**关键问题**：
- Fetch logic split across Node.js (`.mjs`) and Python, with engine chain orchestration in `.mjs`
- F1/F2/F3 all live in the monolithic `.mjs` file alongside convert logic (C3)

### 1.3 Extract

| # | Module | Location | B (Execution Path) | C (Variant) |
|---|--------|----------|---------------------|-------------|
| E1 | `extract_infobox()` | `lib/extraction/infobox.py` | pipeline + explore | generic |
| E2 | `preprocess_html()` | `lib/extraction/preprocessor.py` | explore (full) + pipeline (no-op) | generic |
| E3 | `extract_card_stats()` | `pipeline/converters/card_stats.py` | pipeline | wiki.gg |
| E4 | `fix_links_in_dir()` | `pipeline/converters/link_fixer.py` | pipeline | generic |
| E5 | inline extract logic | `explore/sample_converter.py` | explore | generic |

**关键问题**：
- E2 uses a `context` parameter to switch between explore/pipeline — Defect 1 (dimension collapse)
- E5 (extract in sample_converter) should be in shared lib, not in an explore module

### 1.4 Discover

| # | Module | Location | B (Execution Path) | Domain |
|---|--------|----------|---------------------|--------|
| D1 | `run_homepage_discovery()` | `pipeline/phases/discovery_homepage.py` | pipeline | MediaWiki page trees |
| D2 | `run_allpages_discovery()` | `pipeline/phases/discovery_allpages.py` | pipeline | MediaWiki page trees |
| D3 | `discover()` | `explore/api_discovery.py` | explore | API endpoint probing |
| D4 | `map_structure()` | `explore/structure_mapper.py` | explore | Page structure analysis |
| D5 | `identify()` | `explore/protection_identifier.py` | explore | Anti-crawl detection |
| D6 | Strategy classes | `pipeline/strategies/discovery.py` | pipeline | Strategy-driven discovery |

**关键问题**：
- Pipeline discover (D1/D2) and explore discover (D3/D4/D5) are **not mirrors** — they serve completely different purposes
- May need to split into sub-capabilities: "page_discovery" vs "site_analysis"

### 1.5 Assemble

| # | Module | Location | B (Execution Path) |
|---|--------|----------|---------------------|
| A1 | `run_assemble()` | `pipeline/phases/assemble.py` | pipeline |
| A2 | `mergeMarkdownFiles()` | `.mjs:1418` | scrapling traversal |

**关键问题**：
- Two implementations in different languages for the same capability

---

## §2 Declaration Schema

能力注册表中的每个模块必须声明其维度坐标、与其他模块的关系以及等价证明。

### 2.1 模块身份

| 字段 | 类型 | 必填 | 说明 |
|-------|------|----------|-------------|
| `module` | path | yes | File path relative to repo root |
| `capability` | string | yes | 能力: `fetch` / `convert` / `extract` / `discover` / `assemble` |
| `sub_capability` | string | no | 细粒度能力分组 (e.g. `infobox`, `site_analysis`) |
| `execution_path` | enum | yes | 执行路径: `pipeline` / `explore` / `scrapling_traversal` / `shared` |
| `strategy_variant` | string | yes | 策略变体: `generic` / `<domain>` or `config_driven` |
| `input_format` | enum | yes | 输入格式: `html_mediawiki` / `html_generic` / `wikitext` / `api_json` |
| `kernel` | path | no | 指向本模块为镜像/变体的共享内核 |
| `relationship` | enum | yes | `kernel` / `mirror` / `variant` / `format_converter` / `standalone` |
| `equivalence` | path | no | 对镜像：指向证明输出等价的测试 |

### 2.2 关系类型

```
kernel
  唯一的共享实现。一个 (capability, input_format) 组合只有一个 kernel。
  所有 mirror 和 variant 最终委托到 kernel。

mirror
  同一 kernel 在不同 执行路径的投影。
  mirror 不包含任何转换逻辑——它是薄壳编排器，直接调 kernel。
  等价契约：mirror 对同一输入必须产生与 kernel 完全相同的输出。

variant
  kernel 在同一 输入格式上的站点特定适配。
  通过 strategy.md frontmatter 的配置驱动（config_driven），不使用代码分叉。
  如果出现必须用代码分叉的 variant，那是新 输入格式的信号。

format_converter
  不同 输入格式的转换器。
  例如 wikitext→MD 是独立的 format_converter，不共享 HTML→MD kernel 的代码。
```

### 2.3 Invariants

| # | 不变式 | 执行机制 |
|---|-----------|-------------|
| I1 | 一个 (capability, input_format) 只有**一个** kernel | Stage 3 审计：同坐标重复 = 漂移 |
| I2 | mirror 不包含转换逻辑，只做编排 | 代码审查闸门：mirror 文件 import kernel 但不含转换逻辑 |
| I3 | variant 走配置驱动，不走代码分叉 | 策略 schema 闸门：无 `variant: file_fork` 字段 |
| I4 | 输入格式边界由输入语法决定，不由站点决定 | 如果新站点需要新解析器 = 新 输入格式；如果只需新配置 = 策略变体 variant |
| I5 | 每个 kernel/mirror 对声明等价测试指针 | Stage 3 审计：无 `equivalence` 字段 = 漂移 |

---

## §3 Capability Registry (Target Profiles)

### 3.1 Convert

```
                         ┌── 入口：原始内容
                         │
                         ▼
                  ┌──────────────┐
                  │  输入格式判断     │
                  │  输入格式？    │
                  └──────┬───────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ HTML     │  │ Wikitext │  │ API JSON │
    │ (通用/   │  │          │  │          │
    │  MediaWiki)│  │          │  │          │
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │             │
         ▼             ▼             ▼
  ┌────────────┐  ┌──────────┐  ┌──────────┐
  │ converter  │  │ wikitext │  │ 无需转换  │
  │ .py        │  │ _to_md   │  │ (已是 MD) │
  │ (kernel)   │  │ .py      │  │          │
  └─────┬──────┘  └──────────┘  └──────────┘
        │
        ▼
  ┌──────────────────────┐
  │  变体判断 (config)    │
  │  wiki_domain 传入？   │
  └──────┬───────────────┘
         │
    ┌────┴────┐
    ▼         ▼
  domain    domain
  有值      无值
    │         │
    ▼         ▼
  ┌────┐  ┌────────┐
  │启用 │  │纯 HTML │
  │链接 │  │→MD    │
  │解析 │  │(表格/ │
  │info-│  │图片/  │
  │box  │  │清理)  │
  └──┬─┘  └───┬────┘
     │         │
     └────┬────┘
          ▼
   ┌──────────────┐
   │ Markdown 输出 │
   └──────────────┘
```

**决策表**：

| 条件 | 行为 | 模块 |
|------|------|------|
| 输入格式=wikitext | 走 `wikitext_to_md.py` 独立解析器 | `pipeline/converters/wikitext_to_md.py` |
| D=api_json | 内容已是 plain text / wikitext，不经过 HTML 转换；提取阶段直接处理 | — |
| D=html, C=fandom | 走 converter.py kernel + preprocessor fandom cleanup ops（配置驱动） | `lib/extraction/converter.py` + `preprocessor.py` |
| D=html, C=generic, wiki_domain 有值 | 启用链接解析、图片过滤、redirect map | `lib/extraction/converter.py` |
| D=html, C=generic, wiki_domain 无值 | 纯 HTML→MD：表格 rowspan/colspan、图片捕获、标签清理 | `lib/extraction/converter.py` |

**目标模块**：

| # | Module | 关系类型 | 执行路径 | 策略变体 | 输入格式 | 等价测试 |
|---|--------|-------------|--------|--------|--------|-------------|
| CV1 | `lib/extraction/converter.py` | **kernel** | shared (all) | config_driven | html_mediawiki + html_generic | — |
| CV2 | `pipeline/converters/wikitext_to_md.py` | format_converter | pipeline | generic | wikitext | — |
| CV3 | `explore/sample_converter.py` | **mirror** of CV1 | explore | config_driven | html_mediawiki | `tests/test_convert_equivalence.py` |
| CV4 | `pipeline/pipeline/phases/convert.py` | **mirror** of CV1 | pipeline | config_driven | html_mediawiki | `tests/test_convert_equivalence.py` |
| CV5 | `pipeline/pipeline/phases/convert_html.py` | **mirror** of CV1 | pipeline(cdp) | generic | html_generic | `tests/test_convert_equivalence.py` |

**从基线删除**：
- `lib/extraction/html_to_markdown.py` — 功能并入 CV1 的 generic 路径
- `pipeline/converters/fandom_html_to_markdown.py` — 死代码，fandom 走 CV1 + preprocessor config
- `chrome-agent-cli.mjs:1137` `htmlToMarkdown()` — 归类为基础设施回退，不注册

---

### 3.2 Fetch

```
                         ┌── 入口：URL + output path
                         │
                         ▼
                  ┌──────────────┐
                  │  执行路径判断     │
                  │  执行路径？    │
                  └──────┬───────┘
                         │
     ┌──────────┬────────┼────────┬──────────┐
     ▼          ▼        ▼        ▼          ▼
  explore   pipeline  pipeline  scrapling   fallback
           (MediaWiki) (CDP)   traversal
     │          │        │        │          │
     ▼          ▼        ▼        ▼          ▼
  ┌──────┐  ┌──────┐ ┌──────┐ ┌──────┐  ┌──────┐
  │probe │  │media-│ │chrome│ │scrap-│  │cloak-│
  │_chain│  │wiki  │ │-cdp  │ │ling  │  │brow- │
  │      │  │API   │ │cache │ │fetch │  │ser   │
  └──┬───┘  └──┬───┘ └──┬───┘ └──┬───┘  └──┬───┘
     │         │        │        │          │
     ▼         ▼        ▼        ▼          ▼
  ┌──────────────────────────────────────────────┐
  │           Engine Router (基础设施)              │
  │  scripts/chrome-agent-cli.mjs                  │
  │  职责：preflight → dispatch → 统一 {ok,html}    │
  └──────────────────────────────────────────────┘
```

**决策表**：

| 执行路径 | 引擎 | 协议 | 职责 |
|--------|------|------|------|
| explore | probe_chain (多引擎串行探测) | scrapling → obscura → cloakbrowser → cdp | 确定能用哪个引擎抓取此站点 |
| pipeline (MediaWiki) | MediaWiki action=parse API | HTTP API | 批量获取 wiki 页面 HTML |
| pipeline (CDP) | chrome-cdp cache | 本地缓存读取 | 从 chrome-cdp session 已抓取的缓存中加载 HTML |
| scrapling traversal | scrapling fetch | CLI spawn | 遍历路径中每个 URL 独立抓取 |
| fallback | cloakbrowser | CLI spawn | scrapling 不可用时的兜底引擎 |

**目标模块**：

| # | Module | 关系类型 | 执行路径 | 备注 |
|---|--------|-------------|--------|-------|
| F1 | `scripts/pipeline/pipeline/phases/fetch.py` | kernel (MediaWiki) | pipeline | MediaWiki API 批量 fetch + 重试/退避 |
| F2 | `scripts/pipeline/pipeline/phases/fetch_cdp.py` | kernel (CDP) | pipeline(cdp) | 注意：读本地缓存，不做网络请求 |
| F3 | `scripts/explore/probe_chain.py` | kernel (探针) | explore | 多引擎串行探测，输出可用引擎 |

**基础设施（不注册为能力）**：
- `scripts/chrome-agent-cli.mjs` `runEngineFetch()` — 引擎路由 + spawn 管理
- `scripts/chrome-agent-cli.mjs` `runScraplingFetch()` / `runCloakbrowserFetch()` / `runMediawikiApiFetch()` — 引擎适配器
- `scripts/cloakbrowser_fetcher.py` — standalone 入口，实际由 `.mjs` spawn

**合并**: F3(`.mjs` mediawiki-api fetch) + F4(`fetch.py`) → F1 统一实现

---

### 3.3 Extract

```
                         ┌── 入口：原始/清理后内容
                         │
                         ▼
                  ┌──────────────┐
                  │  提取类型？    │
                  └──────┬───────┘
                         │
     ┌──────────┬────────┼────────┬──────────┐
     ▼          ▼        ▼        ▼          ▼
  infobox   preprocess  card     link      (future)
  提取       HTML清理    _stats   _fixer
     │          │         │        │
     ▼          ▼         ▼        ▼
  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
  │info- │  │pre-  │  │card  │  │link  │
  │box.py│  │proce-│  │_stats│  │_fixer│
  │      │  │ssor  │  │.py   │  │.py   │
  │      │  │.py   │  │      │  │      │
  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
     │         │         │        │
     ▼         ▼         ▼        ▼
  ┌──────────────────────────────────────┐
  │  提取结果合并                          │
  │  (infobox + body → 最终 Markdown)      │
  └──────────────────────────────────────┘
```

**决策表**：

| 提取步骤 | 模块 | 策略变体 | 何时执行 |
|---------|------|------|---------|
| Infobox 提取 | `lib/extraction/infobox.py` | generic（config 驱动） | 页面有 infobox 容器时 |
| HTML 预处理 | `lib/extraction/preprocessor.py` | generic + fandom（config 驱动） | 始终执行（统一路径，无 context 分支） |
| 卡牌统计 | `pipeline/converters/card_stats.py` | wiki.gg | strategy 声明 `card_stats` capability 时 |
| 链接修正 | `pipeline/converters/link_fixer.py` | generic | pipeline assemble 阶段后处理 |

**目标模块**：

| # | Module | 关系类型 | 执行路径 | 策略变体 | 关键变更 |
|---|--------|-------------|--------|--------|--------------------------|
| E1 | `lib/extraction/infobox.py` | kernel | shared (all) | generic | 不变 |
| E2 | `lib/extraction/preprocessor.py` | kernel | shared (all) | generic | **删 `context` 参数**，统一清理路径 |
| E3 | `pipeline/converters/card_stats.py` | variant | pipeline | wiki.gg | 不变 |
| E4 | `pipeline/converters/link_fixer.py` | kernel | pipeline | generic | 不变 |

**删除**: `explore/sample_converter.py` 中的 `_apply_extraction()` 编排逻辑 → 移入 `converter.py.convert_page_full()`

---

### 3.4 Discover

```
                         ┌── 入口：URL
                         │
                         ▼
                  ┌──────────────┐
                  │  probe_chain  │
                  │  引擎可用性探测 │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ api_discovery │
                  │  API 端点探测  │
                  └──────┬───────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
      ┌──────────┐ ┌──────────┐ ┌──────────┐
      │structure │ │protection│ │page      │
      │_mapper   │ │_identifier│ │manifest  │
      │页面结构   │ │反爬等级   │ │生成      │
      │映射      │ │识别      │ │          │
      └────┬─────┘ └────┬─────┘ └────┬─────┘
           │            │            │
           └────────────┼────────────┘
                        ▼
                 ┌──────────────┐
                 │  策略脚手架   │
                 │  scaffold     │
                 │  _generator   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  样本转换 +   │
                 │  自检 → 冻结  │
                 └──────────────┘
```

**决策表**：

| 步骤 | 模块 | 职责 | 输出 |
|------|------|------|------|
| 1 | `probe_chain.py` | 多引擎串行探测，找到能抓取此站点的引擎 | `success_engine`, raw HTML |
| 2 | `api_discovery.py` | 探测 MediaWiki API / sitemap 等端点 | API endpoints list |
| 3 | `structure_mapper.py` | 分析页面结构（导航、内容区、模板类型） | Structure map |
| 4 | `protection_identifier.py` | 识别反爬保护等级和类型 | Protection level + engine override |
| 5 | `page_manifest 生成` | 根据站点结构生成页面清单 | `page_manifest.json` |
| 6 | `scaffold_generator.py` | 生成 strategy.md 脚手架 | Strategy scaffold |
| 7 | `sample_converter.py` + `self_check.py` | 样本转换 + 质量自检 + 架构闸门 | Validated samples |
| 8 | `freeze.py` | 移除 scaffold 标记，注册 strategy | Frozen strategy.md |

**目标模块**：

| # | Module | 关系类型 | 备注 |
|---|--------|-------------|-------|
| D1 | `scripts/explore/probe_chain.py` | kernel | 引擎可用性探测 |
| D2 | `scripts/explore/api_discovery.py` | kernel | API 端点发现 |
| D3 | `scripts/explore/structure_mapper.py` | kernel | 页面结构映射 |
| D4 | `scripts/explore/protection_identifier.py` | kernel | 反爬识别 |
| D5 | `scripts/explore/scaffold_generator.py` | kernel | 策略脚手架生成 |
| D6 | `scripts/explore/sample_converter.py` | kernel | 样本转换 + 编排 |
| D7 | `scripts/explore/self_check.py` | kernel | 质量自检 + 架构闸门 |
| D8 | `scripts/explore/freeze.py` | kernel | 策略冻结 |

**从 pipeline 移入**:
- `pipeline/phases/discovery_homepage.py` → explore page_manifest 生成步骤
- `pipeline/phases/discovery_allpages.py` → explore page_manifest 生成步骤
- `pipeline/strategies/discovery.py` → explore 复用其策略接口

**Pipeline 不再有 discover 阶段**: 页面清单来自 strategy 中 explore 冻结的 manifest。
如需更新站点地图，用户重新走 explore → freeze 流程。

---

### 3.5 Assemble

```
                         ┌── 入口：convert 输出的 .md 文件
                         │
                         ▼
                  ┌──────────────┐
                  │  目录结构创建  │
                  │  按 taxonomy  │
                  │  分目录      │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  List page    │
                  │  拆分         │
                  │  (card_stats) │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  链接修正      │
                  │  (link_fixer) │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  最终输出      │
                  │  outputs/     │
                  │  <domain>/    │
                  └──────────────┘
```

**目标模块**：

| # | Module | 关系类型 | 备注 |
|---|--------|-------------|-------|
| A1 | `scripts/pipeline/pipeline/phases/assemble.py` | kernel | 唯一 assemble 实现 |

**不注册为能力**:
- `chrome-agent-cli.mjs` `mergeMarkdownFiles()` — 遍历路径的轻量合并工具

---

## §4 Cross-Cutting Design Decisions

### 4.1 Naming Schema

```
格式：{sub_capability?}/{input_format?}_{function}.py

规则：
- 目录表达 sub_capability（如 extraction/ 下放 infobox / preprocessor）
- 文件名表达 输入格式差异（wikitext_to_md 暴露 输入格式=wikitext）
- 策略变体不出现于文件名——走 strategy.md 配置驱动
- 执行路径不出现于文件名——走目录（pipeline/ vs explore/）
- kernel 不标注
```

### 4.2 Variant Mechanism Policy

> **规则：策略变体走配置驱动，不走代码分叉。**

| 机制 | 适用场景 | 证据位置 |
|------|---------|---------|
| strategy.md `extraction.cleanup` | 站点特定 HTML 清理操作 | `preprocessor.py` |
| strategy.md `extraction.image_filtering` | 图片跳过/保留规则 | `converter.py` |
| strategy.md `capabilities` | 声明需要的提取能力（如 card_stats） | `registry.py` |
| **永不**新建 `xxx_html_to_markdown.py` | — | I3 不变式 |

判定：如果新站点需要新解析器（新语法、新 DOM 结构），那是新 输入格式信号，
走 format_converter。如果只是 cleanup ops 不同，走 strategy.md 配置。

### 4.3 镜像等价契约

> **规则：golden snapshot 测试。同一 HTML 样本分别走 kernel 和 mirror，断言输出相同。**

- 同一 HTML 输入 → 同一 MD 输出是确定性变换
- golden snapshot 不需要手写断言——差异即漂移
- 已存在 `test_runner.py site-samples` 机制可复用

契约：
1. 每个 mirror 在声明中填写 `equivalence` 字段指向测试文件
2. 测试取同一 HTML 样本，分别走 kernel 和 mirror，断言输出相同
3. CI 每次运行 equivalence tests

### 4.4 Mirror Anti-Patterns

```python
# ❌ mirror 包含转换逻辑
def sample_convert(html):
    soup = BeautifulSoup(html, 'html.parser')
    return str(soup)  # 自己实现 → 漂移

# ✅ mirror 是薄壳编排器
from scripts.lib.extraction.converter import HtmlToMarkdownConverter

def run_convert(...):
    converter = HtmlToMarkdownConverter(wiki_domain=domain)
    return converter.convert_body(html)  # 不实现任何转换逻辑
```

```python
# ❌ kernel 有 执行路径分支
def preprocess_html(html, config, context="explore"):  # ❌ context 参数
    if context == "pipeline":
        return html  # 跳过清理 → 漂移

# ✅ kernel 统一路径
def preprocess_html(html, config):  # 无 context
    return _apply_cleanup_ops(html, config.get("cleanup", []))
```

### 4.5 D-Axis Split Policy

| 场景 | 是否不同输入格式 | 理由 |
|------|------|------|
| Wikitext → MD vs HTML → MD | ✅ 不同 输入格式 | 语法完全不同，需独立解析器 |
| Fandom HTML vs wiki.gg HTML | ❌ 同 输入格式 | 都是 MediaWiki-rendered HTML，差异在 策略变体（cleanup ops） |
| Nintendo 门户 HTML vs MediaWiki HTML | ❌ 同 输入格式 | 都是 HTML，差异在有无 wiki 语义——可通过 `wiki_domain` 可选参数处理 |
| API JSON | ✅ 不经过 convert | 直接走 extract，不是 convert 的职责 |

---

## §5 Infrastructure Boundaries

以下模块存在于代码库中，但**不纳入能力注册表**——它们是基础设施，负责「怎么调用」而非「做什么」：

| Module | 角色 | 归类理由 |
|--------|------|---------|
| `scripts/chrome-agent-cli.mjs` `runEngineFetch()` | 引擎路由器 | 统一所有引擎的 preflight + spawn + 错误包装，是 Node.js 侧的编排基础设施 |
| `scripts/chrome-agent-cli.mjs` `htmlToMarkdown()` | JS 轻量回退 | 当 Python/Scrapling 不可用时的兜底转换，~100 行纯函数，不引入到能力体系 |
| `scripts/chrome-agent-cli.mjs` `mergeMarkdownFiles()` | 文件合并工具 | 遍历路径的低开销合并，是 assemble pipeline 的轻量替代，不替代 `run_assemble()` |
| `scripts/chrome-agent-runtime.mjs` | 启动器 | repo 解析 + CLI 分发，不参与业务能力 |
