# 结构优化重构 & 真源文档规划

> 状态：探索完成，规划产出
> 日期：2026-05-19
> 上下文：基于 `fix-pipeline-quality-gaps` 暴露的系统性结构问题 + 源码审计

---

## 1. 背景与动机

### 1.1 触发来源

`fix-pipeline-quality-gaps` change 在修复 `bindingofisaacrebirth.wiki.gg` 爬取质量问题时，暴露了以下结构性断层：

1. **Phase 命名混乱**：Phase A/0 本质是 Discovery 阶段的两种策略，却被命名为不同 phase，且 orchestrator 自动检测因 CLI 默认值 bug 永远不触发
2. **转换器双路径**：explore 的 `sample_converter.py` 和 pipeline 的 `html_to_markdown.py` 有各自的 infobox 提取和预处理逻辑，Architecture Gate 只校验了前者
3. **策略 schema 歧义**：`discovery_strategy` 与 `api.homepage` 并存产生矛盾
4. **God Orchestrator**：`orchestrate.py` 1208 行承担了策略解析、配置解析、管线执行 10 种关注点
5. **多后端混合调度**：`chrome-agent-cli.mjs` 的 `runCrawl()` 在一个 600 行函数中混合了 MediaWiki API、Scrapling 发现、Scrapling crawl 三种调度路径

部分问题已在该 change 中修复（CLI 参数重构、infobox 表格渲染修复、Architecture Gate 双文件校验），但结构性重构（统一转换器、拆分 orchestrator、提取共享库）被标记为范围外。

### 1.2 源码审计结论

经过对当前代码实际状态的完整审计，系统结构如下：

```
chrome-agent CLI (Node.js, 3792行)
│
├─ runCrawl()  ─┬─ api.platform="mediawiki"  → python3 -m scripts.mediawiki-api-extract
│               ├─ api.platform="mediawiki-fandom" → 同上
│               ├─ discoveryOnly & 非API → Scrapling first_level_links
│               └─ default → Scrapling extract crawl
│
├─ runFetch()  ─┬─ api.platform="mediawiki" → curl MediaWiki API
│               └─ default → Scrapling extract get
│
├─ runScrape()  → Scrapling extract scrape
│
└─ runExplore() ─┬─ 无策略 → deep discovery (scripts/explore/main.py)
                 └─ 有策略 → platform analysis
```

关键依赖关系：

```
orchestrate.py (1208行, 10种关注点)
├── parse_strategy()          ← 策略 YAML 解析 (也被 explore 需要)
├── _STRATEGY_REGISTRY        ← 策略注册表
├── build_pipeline()          ← 策略工厂
├── validate_api_config()     ← 能力校验
├── resolve_rate_limit_config() ← 4层优先级配置解析
├── _resolve_exclude_categories() ← 3层优先级配置解析
├── build_discovery_summary() ← 发现摘要
├── run_phase_fetch()         ← Phase Fetch 编排
├── run_phase_convert()       ← Phase Convert 编排
└── run_pipeline() (387行)    ← 主编排

转换器共享现状：
sample_converter.py ──import──▶ html_to_markdown.convert_html_to_markdown()  ✅ 共享
sample_converter.py 自有 _extract_infobox()  ≠  infox_renderer.py           ⚠️ 重复
sample_converter.py 6-phase cleanup         ≠  html_to_markdown.clean_html() ⚠️ 重叠
```

---

## 2. 目标架构

重构后的目标结构：

```
scripts/
│
├── chrome-agent-cli.mjs            # CLI 入口（大函数拆分）
├── chrome-agent-runtime.mjs        # 运行时（保留不变）
│
├── lib/                             # ★ 新建：共享 Python 库
│   ├── __init__.py
│   ├── strategy_loader.py           # 策略 YAML 解析 (parse_strategy)
│   ├── config_resolver.py           # 配置优先级解析 (rate_limit + exclude)
│   └── extraction/                  # ★ 统一提取引擎
│       ├── __init__.py
│       ├── preprocessor.py          # 统一 HTML 预处理 (合并两套 cleanup)
│       ├── infobox.py               # 统一 Infobox 提取 (合并两套实现)
│       │                              # converter.py 推迟到 Change 3 (随包重命名一起)
│       ├── fandom.py                # Fandom 专用转换
│       └── link_fixer.py            # 链接修复
│
├── pipeline/                        # ★ 重命名：was mediawiki-api-extract
│   ├── __init__.py
│   ├── cli.py                       # CLI 入口
│   ├── __main__.py
│   ├── api_client.py                # MediaWiki API 客户端
│   ├── orchestrator.py              # run_pipeline() — 仅主编排 (~300行)
│   ├── registry.py                  # _STRATEGY_REGISTRY + build_pipeline
│   ├── discovery_summary.py         # build_discovery_summary
│   ├── phases/
│   │   ├── __init__.py
│   │   ├── discovery_homepage.py    # was phase_0.py
│   │   ├── discovery_allpages.py    # was phase_a.py
│   │   ├── fetch.py                 # was phase_b (fetch) + run_phase_fetch
│   │   ├── convert.py               # was phase_b (convert) + run_phase_convert
│   │   └── assemble.py              # was phase_c.py
│   ├── cache.py
│   ├── state.py
│   ├── rate_limiter.py
│   ├── page_assigner.py
│   └── homepage_parser.py
│
└── explore/                         # 站点分析（精简）
    ├── __init__.py
    ├── cli.py                       # was main.py
    ├── deep_discovery.py
    ├── structure_mapper.py
    ├── protection_identifier.py
    ├── scaffold_generator.py
    ├── gates/
    │   ├── architecture.py
    │   └── self_check.py
    ├── ki_lifecycle.py
    ├── freeze.py
    └── iterate.py
```

核心变化：

| 维度 | Before | After |
|------|--------|-------|
| 策略解析 | orchestrate.py 内 + explore 各自实现 | `lib/strategy_loader.py` 统一入口 |
| 配置解析 | orchestrate.py 内 2 个函数 | `lib/config_resolver.py` |
| 提取引擎 | sample_converter + html_to_markdown 各有 infobox/cleanup | `lib/extraction/infobox.py` + `lib/extraction/preprocessor.py` 统一；`converter.py` 推迟到 Change 3 |
| Orchestrator | 1208 行, 10 种关注点 | ~300 行, 仅主编排 |
| Phase 文件 | phase_0/a/b/c 命名 | discovery_homepage/allpages/fetch/convert/assemble |
| CLI 函数 | runCrawl 600 行混合三路 | 3 个独立调度函数 |
| 包名 | mediawiki-api-extract (含连字符) | pipeline |

---

## 2.5 已知断层模式目录

以下模式在本次 session 源码审计中识别，作为后续变更设计和验证的参考。

### 模式 1: 双实现分裂 (Dual Implementation)

**症状**：同一功能有两套独立实现，零代码共享或仅部分共享。

| 实例 | 位置 | 现状 |
|------|------|------|
| Infobox 提取 | `sample_converter.py:_extract_infobox()` vs `infox_renderer.py:render_infobox_table()` | ⚠️ 完全重复 |
| HTML 预处理 | `sample_converter.py:_apply_extraction()` Phase 1-4 vs `html_to_markdown.py:clean_html()` | ⚠️ 职责重叠 |
| 策略 YAML 解析 | `orchestrate.py:parse_strategy()` vs `sample_converter.py:_load_extraction_rules()` vs `architecture_gate.py` | ⚠️ 各自实现 |
| 核心转换 | `sample_converter.py` → `html_to_markdown.convert_html_to_markdown()` | ✅ 已统一 |

**修复模式**：提取共享实现到 `lib/`，两个调用方改为导入。

### 模式 2: God Object (单文件过载)

**症状**：单一文件承担过多不相关职责，难以独立理解和测试。

| 实例 | 行数 | 职责数 |
|------|------|--------|
| `orchestrate.py` | 1208 | 10 |
| `runCrawl()` | ~500 | 3 种调度路径 |

**修复模式**：按职责拆分到独立模块/函数，每个 ≤ 300 行。

### 模式 3: 参数传递链 (Argument Plumbing)

**症状**：参数经过多层传递，每层重新解析/拼接。

```
Skill (MD) → CLI.mjs (spawn args) → cli.py (argparse) → orchestrate.py
```

**实例**：
- `chrome-agent-cli.mjs:2077-2106` 手动拼接 `--strategy`, `--discovery`, `--phase`, `--re-fetch`, `--from-manifest`, `--exclude-category`, `--max-pages` 共 7 个参数到 `python3 -m scripts.mediawiki-api-extract`
- `chrome-agent-cli.mjs:2073` 硬编码路径检查 `scripts/mediawiki-api-extract`
- `chrome-agent-cli.mjs:2201` 硬编码 fallback 消息

**修复模式**：包重命名时统一更新硬编码路径，但不能消除此模式的根本原因（Node.js ↔ Python 进程边界）。

### 模式 4: 声明式冲突 (Declarative Conflict)

**症状**：策略配置中两个字段控制同一行为但含义矛盾。

**实例**：
- `api.content_profile.discovery_strategy: "allpages"` + `api.homepage: {...}` 同时存在 → 前者被忽略（`fix-pipeline-quality-gaps` 已修复为 homepage 优先）
- `api.homepage.exclude_categories` vs `api.exclude_categories`（已通过优先级链解决）

**修复模式**：单一真源字段 + 明确的优先级链文档。

### 模式 5: 命名漂移 (Naming Drift)

**症状**：实际功能已变化但文件/函数名未更新。

| 实例 | 实际含义 | 当前名称 |
|------|---------|---------|
| `phase_0.py` | 首页驱动发现 | "Phase 0" |
| `phase_a.py` | Allpages 发现 | "Phase A" |
| `infox_renderer.py` | 仅被 `html_to_markdown` 调用 | docstring 声称 "shared" |

**修复模式**：文件/函数名与实际功能对齐。

---

## 2.6 治理约束 (来自 AGENTS.md)

以下治理规则约束本次重构的实施方式：

### 策略注册表权威性

> `_STRATEGY_REGISTRY` in `orchestrate.py` 是策略 ID 的唯一权威来源。

**约束 Change 3**：移动 `_STRATEGY_REGISTRY` 到 `pipeline/registry.py` 后，必须确认：
- 所有引用方更新 import 路径
- `bootstrap-strategy` 命令的校验逻辑同步更新
- `STRATEGY_REGISTRY` 公共导出别名保留

### Pipeline Strategy Schema 扩展协议

> 新增策略实现必须：1. 实现 Strategy 类 → 2. 注册到 `_STRATEGY_REGISTRY` → 3. 在策略文件中引用。严禁先引用后注册。

**约束 Change 2+3**：移动注册表不影响此协议，但需确保 `build_pipeline()` 的校验逻辑在移动后仍然正确。

### 引擎版本治理

> `configs/engine-versions.json` 是所有引擎依赖版本的唯一权威来源。

**约束**：重构不改变引擎版本检测逻辑。`scripts/engine-version-check.sh` 和 preflight 脚本不在此次重构范围内。

### Python 3.9 兼容性

> 避免 `X | Y` 类型注解（3.10+ 语法），用 `Optional[X]` 代替。

**约束 Change 1+2**：新建 `lib/` 的所有模块必须使用 Python 3.9 兼容语法。
> 例外：如果文件顶部有 `from __future__ import annotations`，可以使用 `X | Y`（如 `html_to_markdown.py` 当前做法）。

### `__main__.py` re-invoke 模式

> `scripts/mediawiki-api-extract/__main__.py` 通过 `-m` re-invoke 解决包名含连字符的问题。

**约束 Change 3**：包重命名为 `pipeline`（无连字符）后，此 workaround 不再需要，可以简化 `__main__.py`。

### Node.js 脚本约定

> `.mjs` 文件使用 `import`/`export`（纯 ESM），无 TypeScript。
> CLI 输出 JSON-first。

**约束 Change 5**：`chrome-agent-cli.mjs` 的重构保持此风格。

---

## 2.7 前置条件

`fix-pipeline-quality-gaps` change 还有 5 个未完成任务 (tasks 3.1, 3.2, 4.1, 4.2, 4.3)，其中两个是本次重构的关键前置：

| 任务 | 内容 | 对重构的影响 |
|------|------|-------------|
| 3.1 | 对 BOI 站点完整 crawl 验证 | Change 2 需要此 crawl 产出作为 diff 基线 |
| 3.2 | Architecture Gate 新校验验证 | 确保 Gate 在重构前后行为一致 |

**建议**：在启动 Change 1 之前，先完成这两个验证任务，锁定重构前的产出基线。

---

## 3. Change 拆分

共 5 个实现 change + 2 个文档 change，分 4 个阶段执行。

### 阶段依赖图

```
Phase 1 (基础层)
  │
  ├── Change 1: 提取共享库 lib/
  │      │
  │      ▼
  └── Change 2: 统一提取引擎 lib/extraction/  ✅ 已完成
         │
         ▼
Phase 2 (管线层)
  │
  ├── Change 3: 拆分 orchestrator + 重命名包
  │      │
  │      ▼
  └── Change 4: 重命名 Phase 文件
         │
         ▼
Phase 3 (CLI 层)
  │
  └── Change 5: 拆分 CLI 大函数

Phase 4 (文档, 可并行)
  │
  ├── Change D1: 核心架构文档 (8 篇)
  └── Change D2: Spec 合并 (68 → ~20)
```

### Change 1: 提取共享库 `lib/`

| 属性 | 内容 |
|------|------|
| **目标** | 提取跨 explore/pipeline 共享的 Python 模块到 `scripts/lib/` |
| **范围** | 新建 `lib/strategy_loader.py`、`lib/config_resolver.py`；更新所有 import 引用 |
| **风险** | 低 — 纯代码移动，行为完全不变 |
| **依赖** | 无 |
| **预计变更文件** | ~8 个（新建 2 + 修改 6） |

**上下文来源：**
- `orchestrate.py:60-66` `parse_strategy()` — 策略 YAML frontmatter 解析。explore 的 `sample_converter.py:_load_extraction_rules()` (行 580-593) 和 `architecture_gate.py` 有各自的 YAML 读取逻辑，但格式相同（均为 `---\n...\n---` frontmatter 解析）
- `orchestrate.py:257-273` `_resolve_exclude_categories()` — 3 层优先级解析（`api.exclude_categories` → `api.homepage.exclude_categories` → CLI `--exclude-category`）
- `orchestrate.py:276-353` `resolve_rate_limit_config()` — 4 层优先级解析（CLI → strategy local → anti-crawl tier → defaults），被 `run_pipeline()` 在行 862 调用
- `chrome-agent-cli.mjs:546-550` `selectFetcher()` — 引擎选择逻辑中也做了 `api.platform` 检查（`mediawiki`/`mediawiki-fandom`），与 Python 侧的策略解析逻辑相同但不共享代码（Node.js vs Python 边界）

**核心设计：**

```
lib/strategy_loader.py:

  parse_strategy(path: str) → dict
    """Parse strategy YAML frontmatter. Returns full dict."""
    
  parse_extraction_rules(path: str) → dict
    """Parse strategy and return only extraction.* section."""
    
  read_frontmatter(path: str) → dict
    """Parse YAML between first --- markers. Used by Node.js side too."""

lib/config_resolver.py:

  resolve_rate_limit(strategy, cli_args) → RateLimitConfig
    """4-layer priority: CLI → strategy local → anti-crawl tier → defaults"""
    
  resolve_exclude_categories(strategy, cli_excludes) → list[str]
    """3-layer priority: api.exclude_categories → api.homepage.exclude_categories → CLI"""
```

**影响文件：**
- `scripts/mediawiki-api-extract/pipeline/orchestrate.py` — 删除 `parse_strategy()`、`_resolve_exclude_categories()`、`resolve_rate_limit_config()`，改用 `lib/` 导入
- `scripts/explore/sample_converter.py` — `_load_extraction_rules()` 改用 `lib/strategy_loader`
- `scripts/explore/architecture_gate.py` — 策略 YAML 读取改用 `lib/strategy_loader`
- `scripts/explore/main.py` — 同上
- `scripts/mediawiki-api-extract/cli.py` — 策略加载路径更新

**验证标准：**
- `python3 -m scripts.mediawiki-api-extract --help` 正常
- `python3 scripts/explore/main.py --help` 正常
- 现有测试通过：`node --test tests/` + pipeline 单元测试

---

### Change 2: 统一提取引擎 `lib/extraction/` ✅ 已完成

| 属性 | 内容 |
|------|------|
| **目标** | 合并 sample_converter 和 html_to_markdown 的 infobox 提取 + HTML 预处理逻辑到共享库 |
| **范围** | 新建 `infobox.py` + `preprocessor.py`；`infox_renderer.py` 改为薄 wrapper 或删除；`sample_converter.py` 改用共享库；`html_to_markdown.py` 的 `_render_infobox_table()` 调用共享库 |
| **不包含** | `html_to_markdown.py` 文件本身的移动（推迟到 Change 3 随包重命名一起执行） |
| **风险** | 中 — 涉及两套渲染逻辑合并，需确保产出一致 |
| **依赖** | Change 1 (`lib/` 已存在) |
| **预计变更文件** | ~8 个（新建 2 + 修改 4 + 删除/精简 1~2） |

**上下文来源：**
- `sample_converter.py:_extract_infobox()` (行 175-293, 119行, BeautifulSoup) — explore 路径的 infobox 提取
- `infox_renderer.py:render_infobox_table()` (136行, selectolax) — pipeline 路径的 infobox 渲染。docstring 声称 "shared" 但实际仅被 `html_to_markdown.py:457` 调用（`sample_converter.py` 从不导入它）
- `sample_converter.py:_apply_extraction()` Phase 1-4 (行 323-450) — 6 种预处理操作
- `html_to_markdown.py:clean_html()` (行 241-280) — selectolax 预处理
- `html_to_markdown.py:452-470` `_render_infobox_table()` — 通过回调调用 `infox_renderer.render_infobox_table()`
- `html_to_markdown.py` 有 4 个 import 方：`converters/__init__.py`, `strategies/__init__.py`, `standalone.py`, `sample_converter.py`——移动到 Change 3 以避免两次 import 更新

**两套实现的关键差异：**

| 维度 | sample_converter._extract_infobox | infox_renderer.render_infobox_table | 合并方向 |
|------|-----------------------------------|-------------------------------------|---------|
| HTML 解析器 | BeautifulSoup | selectolax（仅接受 parsed node） | 统一函数接受两者，`parser="auto"` |
| field_selector 默认值 | `"tr"` | `"div.pi-data"` | 统一为 `"div.pi-data"`（wiki.gg 标准） |
| handler 查找 | label text + data-source 双路径 | data-source 单路径 | 合并，label text 作为备选 |
| nav 剥离 | 配置驱动 `nav_strip_selectors` | 无 | 采纳 sample 的配置驱动方式 |
| field_handlers | extract_cur_id, count_images, dedup_pools, simplify_collection | extract_cur_id（通过回调） | handler 实现保持回调模式，统一函数签名 |

**核心设计（5 步）：**

**步骤 2.1** — 新建 `lib/extraction/infobox.py`，统一 infobox 提取逻辑：
```python
def extract_infobox(html_or_node, config: dict, wiki_domain: str = "",
                    *, parser: str = "auto",
                    field_selector=None, label_selector=None, value_selector=None,
                    infobox_handlers=None,
                    render_inline_children_fn=None,
                    apply_handler_fn=None) -> str:
    """Unified infobox extraction.

    parser="auto": 自动检测输入类型 (str→BeautifulSoup, selectolax Node→selectolax)
    parser="selectolax": 强制用 selectolax (pipeline 路径)
    parser="bs4": 强制用 BeautifulSoup (explore 路径)

    函数签名与当前 infox_renderer.render_infobox_table() 向后兼容。
    新增接受 str HTML 的能力（BS4 模式），匹配 sample_converter 的用法。
    """
```

设计要点：
- 保留两者都有的功能：配置驱动 (selector/field_selector/label_selector/value_selector)
- 合并差异：sample 的 `nav_strip_selectors` 配置（KI-6 修复）
- 合并差异：sample 的 field_handlers 查找（label text + data-source 双路径）
- 合并差异：infox_renderer 的 handler 查找方式（data-source 匹配）
- 选择器默认值对齐：统一为 `"div.pi-data"`（pipeline 标准路径），确保产出一致
- 回调函数签名对齐：`(handler_name: str, raw_html: str) → str`

**步骤 2.2** — 新建 `lib/extraction/preprocessor.py`，统一 HTML 预处理：
```python
def preprocess_html(html: str, config: dict, context: str = "pipeline") -> str:
    """Unified HTML preprocessing.

    context="pipeline": lightweight cleanup
      - 移除 REMOVAL_SELECTORS (mw-editsection, .toc, #toc, .hatnote)
      - 移除 ModuleEditIcon 图片
      - 按 skip_patterns 过滤图片
      - 移除 display:none 元素
      - 合并 tooltip 链接
      - 提取 YouTube oEmbed 链接

    context="explore": full 6-phase preprocessing
      - Pipeline context 的全部操作
      - 从 HTML 移除 infobox aside（由 extract_infobox 单独调用）
      - 按 cleanup_selectors 剥离元素
      - 修复 lazyload 图片
      - 执行 cleanup 操作列表（来自 config.cleanup）
      - 按 selectors.content 选择主内容区
    """
```

设计要点：
- `cleanup` 操作列表来自 `config.cleanup`，不硬编码
- 兼容 sample 当前的 `strip_fandom_infobox_tables`、`convert_ambox_to_text`、`unwrap_image_wrappers` 等操作
- `pipeline` 上下文与 `html_to_markdown.clean_html()` 行为一致
- `explore` 上下文取代 `sample_converter._apply_extraction()` 的 Phase 1-4

**步骤 2.3** — `sample_converter.py` 的 `_apply_extraction()` 改为导入 `lib/extraction/`，精确替换为 4 步顺序操作：

当前 `_apply_extraction()` 的 infobox 处理流（必须精确理解）：
```python
# Phase 1: _extract_infobox(soup, config, ...)  ← BeautifulSoup soup 中提取
#          → 返回 Markdown 字符串
#          → soup.select(selector) + el.decompose()  ← 从 DOM 移除 infobox
#
# Phase 2-4: soup 上继续 cleanup
#
# Phase 5: content = soup.select_one(selector) or soup.body
#          md = convert_html_to_markdown(str(content), ...)
#          md = infobox_md + "\n\n" + md  ← 在前面拼接 infobox
```

替换后的 4 步顺序（`lib/extraction/` 统一实现）：
```python
def _apply_extraction(html: str, extraction_rules: dict, ...) -> str:
    """Apply extraction rules — uses shared lib/extraction/."""
    full_html = html  # 原始完整 HTML

    # Step A: 从完整 HTML 中提取 infobox 为 Markdown
    # extract_infobox() 内部解析 HTML → 找到 infobox 容器 → 生成 Markdown
    # 不影响 HTML 本身，只是读取
    infobox_md = extract_infobox(full_html, extraction_rules, base_url, ...)

    # Step B: 预处理 HTML（执行所有 cleanup 操作，包括移除 infobox）
    # preprocess_html(context="explore") 内部：
    #   1. 移除 infobox 容器（通过 extract_infobox 相同的 selector）
    #   2. 剥离 cleanup_selectors 匹配的元素
    #   3. 修复 lazyload 图片
    #   4. 执行 cleanup 操作列表（strip_fandom, unwrap_images, etc.）
    #   5. 按 selectors.content 选择主内容区
    cleaned_html = preprocess_html(full_html, extraction_rules, context="explore")

    # Step C: 转换（同当前 Phase 5）
    md = convert_html_to_markdown(cleaned_html, wiki_domain=..., extraction_config=extraction_rules)

    # Step D: 在前面拼接 infobox Markdown（同当前 Phase 6 开始前）
    if infobox_md:
        md = infobox_md + "\n\n" + md

    return md
```

**为什么 infobox 不会被处理两次？**
- `extract_infobox()` 只*读取* HTML 中的 infobox 容器，不修改 DOM，只返回 Markdown 字符串
- `preprocess_html(context="explore")` 统一执行所有 DOM 修改：移除 infobox 容器、剥离 cleanup_selectors、修复 lazyload、执行 cleanup 操作、选择主内容区
- 两者在*同一份 HTML 字符串*上独立操作，不共享可变状态，无顺序依赖
- **为什么 `_extract_infobox()` 必须被彻底清除而不能保留**：如果保持 `_extract_infobox()` 存在，未来对 `lib/extraction/infobox.py` 的任何 infobox 渲染修改都需要同步更新 `sample_converter.py` 中的复制品，再次引发双实现分裂。Change 2 结束后 `grep "def _extract_infobox" scripts/explore/sample_converter.py` 必须返回空

**步骤 2.4** — `infox_renderer.py` 改为薄 wrapper 或删除：
- 选项 A（推荐）：`infox_renderer.py` 删除，`html_to_markdown.py` 直接导入 `lib.extraction.infobox`
- 选项 B（保守）：`infox_renderer.py` 保持为薄 wrapper，代理到 `lib.extraction.infobox`——支持渐变迁移
- `html_to_markdown.py:457` 的 import 从 `from .infox_renderer import render_infobox_table` 改为：
  ```python
  from scripts.lib.extraction.infobox import extract_infobox as render_infobox_table
  ```

**步骤 2.5** — `html_to_markdown.py` 的 `_render_infobox_table()` 改为调用 `lib/extraction/`：
- `_render_infobox_table()` 改为直接导入 `lib.extraction.infobox.extract_infobox`，替换对 `infox_renderer.render_infobox_table` 的调用
- 回调参数与当前调用一致：`render_inline_children_fn=self._render_inline_children`, `apply_handler_fn=self._apply_infobox_handler`
- `clean_html()` 可选改为调用 `preprocess_html(context="pipeline")`，但不是强制要求（当前 selectolax 实现紧耦合度较低）
- handler 实现 (`_apply_infobox_handler`) 保留在 `html_to_markdown.py` 中，通过回调传入——保持与当前模式一致

**变更后的调用关系：**
```
sample_converter.py (explore 路径) — _apply_extraction() 改写为 4 步:
  Step A: lib.extraction.infobox.extract_infobox(full_html, config)  ← 替换 _extract_infobox()
  Step B: lib.extraction.preprocessor.preprocess_html(full_html, config, context="explore")  ← 替换 Phase 1-4
  Step C: html_to_markdown.convert_html_to_markdown(cleaned_html, domain, config)  ← 不变
  Step D: md = infobox_md + "\n\n" + md  ← 前面拼接
  （Step A + Step B 共同取代 _extract_infobox() + decompose()）

html_to_markdown.py (pipeline 路径):
  ├── clean_html()  → 保持独立  ← 当前无需改动
  ├── _render_infobox_table() → lib.extraction.infobox.extract_infobox()  ← 替换 infox_renderer
  └── _apply_infobox_handler()  → 保留在 html_to_markdown.py 中  ← 通过回调传入
```

**推迟到 Change 3 的内容：**
- `html_to_markdown.py` 文件的整体移动（改为 `lib/extraction/converter.py`）— 原因：4 个 import 方，在 Change 2 移动后再在 Change 3 被包重命名触发第二次更新 = 8 次 import 改动；推迟到 Change 3 随包重命名一次完成 = 4 次
- handler 实现 (`_apply_infobox_handler`) 的移动 — 紧耦合于当前类，Change 3 统一时一起移动更合理

**影响的策略字段：**
- `extraction.infox.*` — 被统一 infobox 提取器消费（原来仅 `infox_renderer` 消费）
- `extraction.infox_field_handlers` — 统一 handler 查找逻辑
- `extraction.cleanup` — preprocessor 统一解释
- `extraction.cleanup_selectors` — 两个路径共享

**验证标准：**
- 对 `bindingofisaacrebirth.wiki.gg` 的 The Sad Onion 页面：explore 路径 + pipeline 路径产出均与重构前一致
- 对 `slaythespire.wiki.gg` 示例页面：同上
- `infox_renderer.py` 不再被任何文件导入（或仅作为薄 wrapper 存在）
- **`grep -n "def _extract_infobox" scripts/explore/sample_converter.py` 返回空**（`_extract_infobox` 被彻底删除，确保不再产生分叉）
- `grep -n "def _apply_infobox_handler" scripts/explore/sample_converter.py` 返回空（对应的 handler 实现也被移除）
- Architecture Gate 校验通过（两个路径使用同一 infobox/cleanup 实现）

---

### Change 3: 拆分 orchestrator + 重命名包

| 属性 | 内容 |
|------|------|
| **目标** | 将 `orchestrate.py` 从 1208 行拆分为 4 个独立模块；将 `mediawiki-api-extract` 包重命名为 `pipeline` |
| **范围** | 新建 `registry.py`、`discovery_summary.py`、`phases/fetch.py`、`phases/convert.py`；`html_to_markdown.py` 及其 handler 实现移动到 `lib/extraction/converter.py`；更新包名；更新所有 import 和 CLI spawn 路径 |
| **风险** | 中 — 涉及包重命名，需要更新 CLI 调用路径和所有 import |
| **依赖** | Change 2 (`lib/extraction/` 已存在) |
| **预计变更文件** | ~12 个（新建 5 + 修改 6 + 删除 1） |

**上下文来源：**

| 提取项 | 源位置 (orchestrate.py) | 行数 | 目标文件 |
|--------|------------------------|------|---------|
| `_STRATEGY_REGISTRY` + `PROFILE_KEY_MAP` | 96-151 | 55 | `pipeline/registry.py` |
| `DEFAULT_STRATEGIES` | 96-100 | 5 | `pipeline/registry.py` |
| `build_pipeline()` | 180-211 | 31 | `pipeline/registry.py` |
| `derive_capabilities()` | 149-178 | 29 | `pipeline/registry.py` |
| `build_discovery_summary()` | 355-605 | 250 | `pipeline/discovery_summary.py` |
| `run_phase_fetch()` | 607-710 | 103 | `pipeline/phases/fetch.py` |
| `run_phase_convert()` | 715-820 | 105 | `pipeline/phases/convert.py` |
| `run_pipeline()` | 822-1208 | 387 | `pipeline/orchestrator.py` (~300行) |
| `validate_api_config()` | 214-233 | 19 | `pipeline/orchestrator.py` |
| exit code 常量 | 47-54 | 8 | `pipeline/orchestrator.py` |

**核心设计：**

```
pipeline/registry.py:

  class PipelineStrategies:  # 从 orchestrate.py 移动
  DEFAULT_STRATEGIES         # 默认策略映射
  _STRATEGY_REGISTRY         # 策略注册表（权威来源）
  PROFILE_KEY_MAP            # content_profile → PipelineStrategies 字段映射
  build_pipeline(strategy, domain) → PipelineStrategies
  derive_capabilities(content_profile) → list[str]

pipeline/discovery_summary.py:

  build_discovery_summary(manifest, strategy, ...) → dict
  _build_homepage_categories()    # 辅助函数
  _build_allpages_categories()    # 辅助函数
  _build_excluded_list()          # 辅助函数
  _build_unclassified()           # 辅助函数
  _estimate_time()                # 辅助函数

pipeline/phases/fetch.py:

  run_phase_fetch(client, manifest, strategy, ...) → dict
  # 从 orchestrate.py 移动，与 phase_b.py 的 fetch_single_page 配合

pipeline/phases/convert.py:

  run_phase_convert(output_dir, manifest, strategy, ...) → tuple[dict, dict]
  # 从 orchestrate.py 移动，与 phase_b.py 的 convert_single_page 配合

pipeline/orchestrator.py:

  EXIT_SUCCESS, EXIT_PARTIAL_SUCCESS, ...  # 退出码常量
  validate_api_config(api_config, strategies) → Optional[str]  # 能力校验
  run_pipeline(args) → int  # 主编排（精简版）
  
  run_pipeline() 内部结构 (精简后 ~300 行):
    ├── 策略加载 (lib.strategy_loader)
    ├── 管线构建 (pipeline.registry)
    ├── API 校验 + 探测
    ├── 配置解析 (lib.config_resolver)
    ├── Discovery 调度 → 调用 phases/discovery_*.py
    ├── Fetch 调度     → 调用 phases/fetch.py
    ├── Convert 调度   → 调用 phases/convert.py
    ├── Assemble 调度  → 调用 phases/assemble.py
    └── Post: link_fix + L6 validation
```

**包重命名：**
- `scripts/mediawiki-api-extract/` → `scripts/pipeline/`
- 全局替换：`-m scripts.mediawiki-api-extract` → `-m scripts.pipeline`
- 全局替换 import：`from .pipeline` → 保持不变（内部相对路径）
- `scripts/chrome-agent-cli.mjs` 更新 spawn 命令和路径检查
- `tests/` 更新 import 路径

**验证标准：**
```bash
python3 -m scripts.pipeline --help  # 新包名可用
python3 -m scripts.pipeline --strategy ... --output ...  # 完整管线运行正常
node scripts/chrome-agent-cli.mjs crawl <url>  # CLI 端到端正常
node --test tests/  # 测试通过
```

---

### Change 4: 重命名 Phase 文件

| 属性 | 内容 |
|------|------|
| **目标** | 将 Phase 文件命名与实际含义对齐，消除 "Phase 0 vs Phase A" 混淆 |
| **范围** | 重命名 4 个文件 + 更新所有 import 引用 + 更新 log 消息 |
| **风险** | 低 — 纯文件重命名，`fix-pipeline-quality-gaps` 已添加函数别名做过渡 |
| **依赖** | Change 3 (`pipeline/` 包已存在) |
| **预计变更文件** | ~8 个（新建 4 + 修改 4） |

**核心设计：**

| Before | After | 说明 |
|--------|-------|------|
| `pipeline/phase_0.py` | `pipeline/phases/discovery_homepage.py` | 首页驱动发现 |
| `pipeline/phase_a.py` | `pipeline/phases/discovery_allpages.py` | Allpages 发现 |
| `pipeline/phase_b.py` | 拆分到 `phases/fetch.py` + `phases/convert.py` | 提取阶段 |
| `pipeline/phase_c.py` | `pipeline/phases/assemble.py` | 组装阶段 |

**log 消息统一：**
- `"Phase 0"` → `"homepage discovery"`
- `"Phase A"` → `"allpages discovery"`
- `"Phase B"` → `"extraction"`
- `"Phase C"` → `"assembly"`

（`fix-pipeline-quality-gaps` 已完成此变更，本 change 仅同步文件名）

**注意：** `phase_b.py` 的拆分在 Change 3 中已部分完成（`run_phase_fetch` 和 `run_phase_convert` 已提取）。本 change 将 `phase_b.py` 中剩余的 `fetch_single_page()` 和 `convert_single_page()` 分别归入对应文件。

**验证标准：**
- grep 无 `from.*phase_0\|from.*phase_a\|from.*phase_b\|from.*phase_c` 匹配
- 完整 crawl 运行正常

---

### Change 5: 拆分 CLI 大函数

| 属性 | 内容 |
|------|------|
| **目标** | 将 `chrome-agent-cli.mjs` 中 `runCrawl()` 的三路调度提取为独立函数 |
| **范围** | 仅 `scripts/chrome-agent-cli.mjs` |
| **风险** | 低 — 内部重构，外部接口不变 |
| **依赖** | Change 3 (`pipeline/` 包名已更新) |
| **预计变更文件** | 1 个 |

**上下文来源：**
- `chrome-agent-cli.mjs:1965-2460` `runCrawl()` — 约 500 行混合三路调度
- MediaWiki API 路径 (行 2072-2201)：检查 `scripts/mediawiki-api-extract` 目录存在 → 构造 `--strategy`, `--output`, `--concurrency`, `--discovery`, `--phase`, `--re-fetch`, `--from-manifest`, `--exclude-category`, `--max-pages` 参数 → `spawnSync("python3", args)` → 解析退出码 (0=success, 1=partial, ≥10=failure) → 收集 `.md` 和 `extraction_results.json` artifacts
- Scrapling 发现路径 (行 2215-2310)：仅在 `discoveryOnly && !doc?.api?.platform` 时触发 → `runScraplingPreflight()` → `selectFetcher()` → `runEngineFetch()` 获取首页 → `collectLinksFromHtml()` 提取链接 → `pagePatternMatches()` 分组 → 构建 `discovery_summary.json`
- Scrapling crawl 路径 (行 2335-2460)：队列初始化（从 `fromManifest` 或 `startPage`）→ 循环遍历 `while (queue.length > 0 && visited.size < maxPages)` → 每页 `runEngineFetch()` → `collectLinksFromHtml()` 发现新链接 → 分页逻辑 → artifact 收集
- `selectFetcher()` (行 546-550) — 引擎选择：`api.platform === "mediawiki"` → `"mediawiki-api"`，否则按 `engine_preference` 或 protection_level 选择 Scrapling/Obscura/CloakBrowser
- `runEngineFetch()` (行 754-758) — fetcher 路由：`"mediawiki-api"` → `runMediawikiApiFetch()`，`"cloakbrowser"` → `runCloakbrowserFetch()`，其他 → `runScraplingFetch()`
- `runMediawikiApiFetch()` (行 673-751) — 独立于 Python 管线的 fetch 路径：直接用 `curl` 调 `action=parse` API，不经过 `orchestrate.py`
- `runFetch()` (行 1766-1846) — 单页 fetch 命令：同样使用 `selectFetcher()` 路由，mediawiki-api 时传 strategy path 作为 extraArg
- `runScrape()` (行 2729+) — 策略无关递归爬取，始终走 Scrapling
- `runExplore()` (行 1552-1764) — 站点分析：无策略时 `spawnSync("python3", ["scripts/explore/main.py", ...])` 执行 deep discovery

**核心设计：**

```
runCrawlMediawikiApi(repoRoot, strategy, ...) → result
  """MediaWiki API pipeline route.
  
  检查 extraction script 存在 → 构造参数 → spawn python3 → 
  处理 discovery-only / full crawl / 错误 fallback
  """
  
runCrawlScraplingDiscovery(repoRoot, strategy, ...) → result
  """Scrapling first-level link discovery route.
  
  Preflight → fetch homepage → collectLinksFromHtml → 
  build discovery_summary → return
  """

runCrawlScrapling(repoRoot, strategy, ...) → result
  """Standard Scrapling bounded crawl route.
  
  队列初始化 → 循环遍历 → 引擎选择 → 链接发现 → 分页 → 产物收集
  """

runCrawl(...) → result  (精简后 ~60 行)
  """Crawl 入口：策略匹配 → 入口点验证 → 按 api.platform 路由"""
```

**验证标准：**
- `node scripts/chrome-agent-cli.mjs crawl <url>` 三种路径行为与重构前一致
- `node --test tests/` 通过

---

### Change D1: 核心架构文档

| 属性 | 内容 |
|------|------|
| **目标** | 创建 8 篇人类可读的真源架构文档 |
| **范围** | `docs/architecture/` 目录 |
| **风险** | 低 — 纯文档，不影响运行时代码 |
| **依赖** | 可与 Change 1-5 并行 |
| **预计变更文件** | 8 个新建 |

**文档清单与核心大纲：**

```
docs/architecture/
│
├── 01-overview.md           # 系统全景
│   - 系统定位与核心设计原则
│   - 多后端架构全景图
│   - 技术栈总览表
│   - 仓库目录结构说明
│
├── 02-pipeline-flow.md      # 数据流详解 ★ 最重要
│   - 端到端流程图
│   - 五阶段详解（每个阶段的输入/输出/副作用）
│   - 缓存机制（Fetch ↔ Convert 解耦）
│   - 断点续传机制
│   - 速率限制优先级解析
│
├── 03-strategy-schema.md    # 策略 Schema 参考 ★ 权威真源
│   - YAML frontmatter 完整字段参考（含类型、必填、默认值、示例）
│   - registry.json 格式
│   - 反爬策略格式
│
├── 04-cli-reference.md      # CLI 参考
│   - 所有命令与参数表
│   - 管线子命令说明
│
├── 05-converter-architecture.md  # 转换器架构
│   - 预处理 + 转换的两阶段模型
│   - 统一提取引擎 (lib/extraction/) 设计
│   - Infobox 提取机制
│
├── 06-engine-selection.md   # 引擎选择
│   - 已注册引擎清单
│   - 引擎选择决策树
│   - Preflight 机制
│   - Fallback 升级路径
│
├── 07-explore-workflow.md   # Explore 工作流
│   - Deep discovery 流程
│   - 策略生成与冻结
│   - Architecture Gate 校验
│
└── 08-tech-stack.md         # 技术栈依赖
    - 运行时依赖表（Python + Node.js）
    - 外部引擎依赖（Scrapling, Obscura, CloakBrowser）
    - 版本固定策略
    - 安装脚本链
    - 兼容性约束
```

**编写原则：**
- 以代码实际行为为准，不以 spec 为准（spec 可能过时）
- 每个流程图配 ASCII art
- 策略 schema 文档是 YAML frontmatter 的唯一权威真源

---

### Change D2: Spec 合并

| 属性 | 内容 |
|------|------|
| **目标** | 将 68 个 spec 合并为 ~20 个能力域 spec，消除碎片化 |
| **范围** | `openspec/specs/` 目录 |
| **风险** | 中 — 涉及删除和合并，需确保不丢失有效约束 |
| **依赖** | 应在 Change 1-5 完成后执行（spec 引用新的模块路径） |
| **预计变更文件** | ~70 个（合并新建 ~20 + 删除/归档 ~50） |

**合并映射：**

| 目标 Spec | 合并来源 (当前 spec 数) |
|-----------|----------------------|
| `pipeline/pipeline-core.md` | mediawiki-api-extraction-pipeline + pipeline-cli-entry (2) |
| `pipeline/pipeline-discovery.md` | homepage-driven-discovery + discovery-phase-unification (2) |
| `pipeline/pipeline-fetching.md` | pipeline-fetch-phase + page-content-cache (2) |
| `pipeline/pipeline-conversion.md` | pipeline-convert-phase + pipeline-converters + html-conversion-pipeline + shared-infobox-renderer + tooltip-icon-link-merge (5) |
| `pipeline/pipeline-assembly.md` | page-assignment + unified-link-fixer + homepage-discovery-category-extraction (3) |
| `explore/explore-deep-discovery.md` | explore-workflow + explore-backend-detection + explore (3) |
| `explore/explore-scaffold.md` | strategy-scaffold-generation + strategy-templates (2) |
| `explore/explore-validation.md` | explore-architecture-gate + sample-self-check + explore-strategy-pipeline-bridge (3) |
| `explore/explore-ki.md` | explore-ki-lifecycle (1) |
| `engines/engine-registry.md` | engine-registry + engine-contracts + extension-api (3) |
| `engines/engine-contracts.md` | 8 个 *-contract (合并为统一契约格式) (8) |
| `strategy/strategy-schema.md` | site-strategy-schema + anti-crawl-schema + pipeline-strategy-schema (3) |
| `strategy/strategy-lifecycle.md` | site-strategy + bootstrap-strategy-cli + site-strategy-template (3) |
| `cli/cli-interface.md` | global-capability-cli + global-workflow-skill (2) |
| `cli/cli-workflows.md` | scrapling-first-browser-workflow + strategy-guided-crawl + scrape-command (3) |
| `governance/governance.md` | agents-governance + capabilities-derivation + master-plan + capability-contracts (4) |
| `governance/handoff.md` | handoff-emission + handoff-gate (2) |
| `governance/output.md` | output-lifecycle + output-lifecycle-git-governance (2) |
| `mediawiki/api.md` | mediawiki-api-contract + mediawiki-api-extraction + mediawiki-extraction-patterns (3) |
| `misc/` | 其余 spec 按活跃度保留或归档 | (10) |

**执行策略：**
1. 先创建目标 spec 文件，合并内容
2. 验证 Architecture Gate 仍能正确校验（spec 文件名变化不影响）
3. 删除旧 spec 文件前执行 `grep -r "specs/<old-name>" openspec/` 确认无引用
4. 更新所有 change 中的 spec 引用

---

## 4. 执行计划

```
Week 1-2: Phase 1 (基础层)
  ├── Change 1: 提取共享库 lib/          [2-3天]
  └── Change 2: 统一提取引擎              ✅ 完成
  
Week 3-4: Phase 2 (管线层)
  ├── Change 3: 拆分 orchestrator + 重命名包 [3-4天]
  └── Change 4: 重命名 Phase 文件          [1-2天]

Week 5: Phase 3 (CLI 层)
  └── Change 5: 拆分 CLI 大函数            [1-2天]

Week 3-5: Phase 4 (文档，与 Phase 2 并行)
  ├── Change D1: 核心架构文档              [持续]
  └── Change D2: Spec 合并                 [Phase 2 完成后]
```

---

## 5. 风险与缓解

| 风险 | 可能性 | 影响 | 缓解 |
|------|--------|------|------|
| 包重命名导致 import 断裂 | 中 | 高 | 使用 `sed` 批量替换 + `grep` 验证零残留引用 |
| 统一 infobox 渲染改变产出格式 | 中 | 中 | 用两个目标站点的样本页面做 diff 对比验证 |
| CLI spawn 路径硬编码断裂 | 低 | 高 | `chrome-agent-cli.mjs` 中有集中路径检查逻辑，单点修改 |
| Spec 合并丢失有效约束 | 低 | 中 | Architecture Gate 作为回归检测；grep 确认无未合并引用 |
| 并行文档变更与代码变更冲突 | 低 | 低 | 文档 Change 独立目录，不与代码文件冲突 |

---

## 6. 成功标准

重构完成后：

1. `orchestrator.py` ≤ 350 行，仅包含 `run_pipeline()` 和辅助函数
2. `lib/extraction/` 是 infobox 提取和 HTML 预处理的唯一实现 — `grep 'def _extract_infobox\|def _apply_infobox_handler' scripts/explore/sample_converter.py` 返回空
3. 无 `phase_0`/`phase_a`/`phase_b`/`phase_c` 文件
4. `runCrawl()` ≤ 80 行
5. 对 `bindingofisaacrebirth.wiki.gg` 和 `slaythespire.wiki.gg` 的完整 crawl 产出与重构前一致
6. `docs/architecture/02-pipeline-flow.md` 和 `03-strategy-schema.md` 成为新人理解系统的首要入口

---

## 附录 A: Node.js ↔ Python 边界引用清单

以下是 `chrome-agent-cli.mjs` 中对 Python 包路径的所有硬编码引用。Change 3（包重命名）和 Change 5（大函数拆分）时必须全部更新。

### A.1 spawn 命令中的包路径

| 位置 (行号) | 当前值 | Change 3 后 | 上下文 |
|------------|--------|------------|--------|
| 2073 | `path.join(repoRoot, "scripts", "mediawiki-api-extract")` | `path.join(repoRoot, "scripts", "pipeline")` | `runCrawl()` MediaWiki API 路径检查 |
| 2077 | `"-m", "scripts.mediawiki-api-extract"` | `"-m", "scripts.pipeline"` | `runCrawl()` spawn 参数 |
| 2201 | `"mediawiki-api-extract script not found"` | `"pipeline script not found"` | fallback 消息 |

### A.2 Python import 引用（管线内部）

以下 import 在 Change 3 中需要批量更新（`scripts/mediawiki-api-extract/` 内部所有 `.py` 文件）：

```python
# 内部绝对 import（__main__.py 中）
# Before: from scripts.mediawiki_api_extract.cli import main
# After:  from scripts.pipeline.cli import main

# 内部相对 import（不变，因为包内相对路径）
from .pipeline.orchestrate import run_pipeline  # 保持不变
from ..converters.html_to_markdown import ...    # 保持不变
```

### A.3 `__main__.py` re-invoke 逻辑

`scripts/mediawiki-api-extract/__main__.py` 当前使用特殊 re-invoke 模式处理含连字符的包名：

```python
# 当前逻辑（推测）：
# 检测到通过 `python3 scripts/mediawiki-api-extract/` 直接调用时，
# re-invoke 为 `python3 -m scripts.mediawiki-api-extract`
```

Change 3 重命名为 `pipeline` 后，包名不含连字符，此 workaround 可能不再需要。但 `-m scripts.pipeline` 调用方式保留不变。

### A.4 `chrome-agent-cli.mjs` 其他引用

| 行号 | 内容 | 影响 Change |
|------|------|------------|
| 546-550 | `apiPlatform === "mediawiki" \|\| apiPlatform === "mediawiki-fandom"` → `"mediawiki-api"` | Change 5 |
| 754-758 | `runEngineFetch()` fetcher 路由 | Change 5 |
| 1706 | `hasApiPlatform` 检查（用于 explore 路径的 conversionEngine 判断） | Change 5 |
| 1775-1776 | `runFetch()` 中 `fetcher === "mediawiki-api"` 判断 | Change 5 |

### A.5 `tests/` 中的引用

```
tests/chrome-agent-runtime.test.mjs  — 测试 CLI runtime，需确认无硬编码包路径
tests/ (如有)                        — pipeline Python 测试，需更新 import
```

---

## 附录 B: 站点策略验证基线

重构过程中需要保持产出一致性的目标站点：

| 站点 | 策略路径 | 管线类型 | 用途 |
|------|---------|---------|------|
| `bindingofisaacrebirth.wiki.gg` | `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` | MediaWiki API (homepage) | 主要验证目标：infobox 表格、分类页 index、exclude_categories |
| `slaythespire.wiki.gg` | `sites/strategies/slaythespire.wiki.gg/strategy.md` | MediaWiki API (allpages) | 次要验证目标：双命名空间、Fandom infobox模板 |
| `balatrowiki.org` | `sites/strategies/balatrowiki.org/strategy.md` | MediaWiki API | 扩展验证 |

每个 Change 的验证都应至少覆盖前两个站点。

---

## 附录 C: 本 Session 关键发现索引

以下发现来自本 session 的源码审计和讨论，是后续各 Change 设计决策的依据：

| ID | 发现 | 来源 | 关联 Change |
|----|------|------|------------|
| F1 | `infox_renderer.py` docstring 声称 "shared" 但实际仅被 `html_to_markdown.py` 调用 | 源码审计 | Change 2 |
| F2 | `sample_converter.py` 的 `convert_html_to_markdown()` 调用在 Phase 5（共享），但 Phase 1-4 的预处理和 infobox 提取是独立的 | 源码审计 | Change 2 |
| F3 | `orchestrate.py` 中 `run_phase_fetch()` (607-710) 和 `run_phase_convert()` (715-820) 与 `phase_b.py` 的逻辑相关但不在一起 | 源码审计 | Change 3 |
| F4 | `run_pipeline()` 最后 100 行 (1100-1208) 混合了 link_fix、L6 validation、状态 flush | 源码审计 | Change 3 |
| F5 | `runMediawikiApiFetch()` 使用 `curl` 直调 API，不经过 Python 管线 — 是独立的 fetch 路径 | 源码审计 | Change 5 |
| F6 | Python 3.9 兼容性：`html_to_markdown.py` 使用了 `from __future__ import annotations` 来支持 `X | Y` 语法 | 源码审计 + AGENTS.md | Change 1, 2 |
| F7 | 跨仓库参考：`html_to_markdown.py:20-22` 引用了 `/Users/nantasmac/projects/personal/wiki.gg/` 作为设计参考 | 源码审计 | 文档 |
| F8 | `selectFetcher()` 在 Node.js 侧做 `api.platform` 检查，与 Python 侧的 `build_pipeline()` 逻辑平行但不共享 | 源码审计 | Change 5 |
