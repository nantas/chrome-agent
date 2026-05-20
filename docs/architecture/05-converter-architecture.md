# 05 — Converter Architecture

> **Spec reference**: `openspec/specs/unified-infobox-extraction/`, `openspec/specs/unified-html-preprocessing/`
>
> **Source modules**: `scripts/lib/extraction/`, `scripts/pipeline/converters/`

## 1. Overview

chrome-agent uses a **two-phase converter model** — preprocessing then conversion — to transform raw HTML from web pages into clean Markdown. The system is designed around a **unified extraction engine** that serves both the explore deep-discovery path and the pipeline MediaWiki API path, sharing core logic while allowing context-specific behavior.

```
Raw HTML
  │
  ├─→ [Phase 1: Preprocessing] ──→ Cleaned HTML
  │       │
  │       ├─ Explore path: 6-step full cleanup (lib/extraction/preprocessor.py)
  │       └─ Pipeline path: lightweight cleanup (converter.py:clean_html)
  │
  └─→ [Phase 2: Conversion] ──→ Markdown output
          │
          ├─ Infobox extraction (lib/extraction/infobox.py)
          └─ HTML→Markdown conversion (lib/extraction/converter.py)
```

## 2. Module Inventory

### 2.1 Shared Extraction Library — `scripts/lib/extraction/`

| Module | Key Function | Purpose |
|--------|-------------|---------|
| `infobox.py` | `extract_infobox()` | Unified infobox extraction (BS4 + selectolax) |
| `preprocessor.py` | `preprocess_html()` | Config-driven HTML cleanup for explore path |
| `converter.py` | `HtmlToMarkdownConverter` | MediaWiki HTML → Markdown (selectolax-based) |
| `converter.py` | `convert_html_to_markdown()` | Standalone convenience wrapper |
| `__init__.py` | — | Package marker |

### 2.2 Pipeline Converters — `scripts/pipeline/converters/`

| Module | Key Class/Function | Purpose |
|--------|-------------------|---------|
| `fandom_html_to_markdown.py` | — | Fandom-specific HTML converter |
| `card_stats.py` | — | Card/game stats table converter |
| `link_fixer.py` | — | Post-conversion link normalization |
| `wikitext_to_md.py` | — | Wikitext source → Markdown converter |

### 2.3 Design Decision: `converter.py` Location

`converter.py` was moved from `scripts/pipeline/converters/` to `scripts/lib/extraction/` during the `finish-refactor-cleanup` change to enable shared access from both the pipeline and explore paths. The rationale for the current location:

1. **Shared access**: Both `sample_converter.py` (explore path) and pipeline phases import `convert_html_to_markdown()`. Co-location in `lib/extraction/` eliminates cross-package imports.
2. **Selectolax dependency**: The converter relies on `selectolax.parser.HTMLParser` as its primary parser — now shared with other `lib/extraction/` modules.
3. **Extraction library coherence**: `lib/extraction/` houses the full content transformation pipeline: infobox extraction, HTML preprocessing, and HTML→Markdown conversion. The one-way dependency from pipeline converters → shared extraction library is maintained via `extract_infobox()` imports.

## 3. Two-Phase Model

### Phase 1: Preprocessing

Preprocessing removes noise, normalizes structure, and isolates content before conversion. The behavior is **context-aware**:

| Context | Trigger | Implementation | Steps |
|---------|---------|---------------|-------|
| **Explore** (full) | `context="explore"` | `preprocessor.preprocess_html()` | 6-step pipeline |
| **Pipeline** (lightweight) | Default pipeline flow | `HtmlToMarkdownConverter.clean_html()` | Selector-based removal only |

#### Explore 6-Step Preprocessing (`preprocessor._preprocess_explore`)

Executed by `scripts/lib/extraction/preprocessor.py`:

1. **Remove infobox container** — Strips the infobox `<aside>` so it doesn't appear in body conversion (infobox is extracted separately).
2. **Strip cleanup selectors** — Removes elements matching `cleanup_selectors` from strategy config.
3. **Fix lazyload images** — Swaps `src` placeholder for `data-src` real URL when `lazyload.enabled` is set.
4. **Execute cleanup operations** — Runs named operations from `cleanup` config list (e.g., `strip_fandom_infobox_tables`, `convert_ambox_to_text`, `unwrap_image_wrappers`, `strip_footer`, `strip_edit_links`, `strip_skip_links`, `strip_category_links`, `convert_nested_images`).
5. **Remove decorative images** — Filters images matching `image_filtering.skip_patterns`.
6. **Select main content** — Extracts content using `selectors.content` CSS selector (defaults to `body`).

#### Pipeline Lightweight Preprocessing (`HtmlToMarkdownConverter.clean_html`)

Executed by `scripts/lib/extraction/converter.py`:

- Removes elements matching `_REMOVAL_SELECTORS` (default: `.mw-editsection`, `.toc`, `#toc`, `.hatnote`; or strategy `cleanup_selectors`).
- Strips `ModuleEditIcon` images and their parents.
- Applies `image_filtering.skip_patterns`.
- Removes elements with `display:none` style.

### Phase 2: Conversion

Conversion transforms preprocessed HTML into Markdown. The key integration point is `HtmlToMarkdownConverter.convert_body()`:

```
convert_body(html):
  1. merge_tooltip_links(html)     # Merge MediaWiki icon+text link pairs
  2. extract_video_links(html)     # Extract YouTube oEmbed links
  3. clean_html(html)              # Remove wiki UI noise
  4. convert(cleaned_html)         # Render HTML tree → Markdown blocks
  5. Insert video links section    # Append to ## In-game Footage
```

The `_render_block` method handles all HTML tag types with recursive descent:
- **Headings**: `<h1>`–`<h6>` → `# text` (h1 promoted to h2)
- **Lists**: `<ul>`/`<ol>` → Markdown lists with nested support
- **Tables**: `<table>` → Markdown pipe tables (with fallback to list format for complex tables)
- **Blockquotes**: `<blockquote>` → `>` prefix
- **Code**: `<pre>` → fenced code blocks
- **Inline**: `<strong>`, `<em>`, `<code>`, `<a>` → Markdown equivalents
- **Images**: `<img>` → `![alt](src)` with skip pattern filtering
- **Infobox containers**: Detected by tag+class match → delegated to `extract_infobox()`

## 4. Unified Infobox Extraction — `lib/extraction/infobox.py`

The `extract_infobox()` function provides a single entry point for infobox extraction that supports both parser backends:

```python
def extract_infobox(
    html_or_node,           # Raw HTML (BS4) or selectolax Node
    config: dict,           # Strategy extraction config
    wiki_domain: str = "",
    *,
    parser: str = "auto",   # "auto" | "bs4" | "selectolax"
    ...
) -> str:                   # Returns Markdown table or ""
```

### Parser Auto-Detection

- `str` input → BS4 mode (explore path)
- selectolax `Node` input → selectolax mode (pipeline path)

### BS4 Mode (`_extract_bs4`)

Used by the explore path. Walks descendants with deduplication, handles:
- Image extraction with `skip_patterns` filtering
- Link resolution (relative → absolute URLs)
- Nav element stripping via `nav_strip_selectors`
- Handler dispatch for special field types (via `_apply_bs4_handler`)

### Selectolax Mode (`_extract_selectolax`)

Used by the pipeline path. Operates on selectolax nodes:
- Uses `render_inline_children_fn` callback for text rendering
- Uses `apply_handler_fn` callback for handler application
- Falls back to `_fallback_text` and `_fallback_text_from_html` when callbacks are unavailable

### Infobox Handlers

Both modes support named handlers for specialized field processing:

| Handler | Purpose |
|---------|---------|
| `text` | Strip HTML, return plain text |
| `image` | Extract primary image as `![](url)` |
| `count_images` | Count images grouped by alt text |
| `extract_cur_id` | Extract current ID from nav span |
| `dedup_pools` | Deduplicate item pool links |
| `simplify_collection` | Reduce collection grid to single link |
| `extract_tags` | Extract tag tooltips from icon links |

Handler lookup uses a **dual-key system**: first by label text, then by `data-source` alias (`ds_key = f"{data_source}({label_text})"`), enabling both human-readable and data-attribute-based handler routing.

## 5. Sample Converter Integration

The explore path's `sample_converter.py` (`scripts/explore/sample_converter.py`) orchestrates the full two-phase pipeline:

```python
def _apply_extraction(html, extraction_rules, known_pages):
    # Step 1: Extract infobox (read-only, returns Markdown)
    infobox_md = extract_infobox(html, extraction_rules, wiki_domain)

    # Step 2: Preprocess HTML (removes infobox, applies cleanup)
    cleaned_html = preprocess_html(html, extraction_rules, context="explore")

    # Step 3: Convert cleaned HTML to Markdown
    md = convert_html_to_markdown(cleaned_html, wiki_domain, extraction_config)

    # Step 4: Prepend infobox + body
    if infobox_md:
        md = infobox_md + "\n\n" + md

    # Post-conversion: text_normalization, url_conversion, youtube_cleanup, cleanup ops
    ...
```

The sample converter CLI provides two subcommands:

| Subcommand | Description |
|------------|-------------|
| `apply` | Convert an existing HTML file using strategy extraction rules |
| `fetch-and-apply` | Fetch page via MediaWiki `action=parse` API, then convert |

## 6. Data Flow Diagram

```
Strategy frontmatter (YAML)
  │
  ├─ extraction.infobox.*          ──→ infobox.py: selector, field/label/value selectors
  ├─ extraction.cleanup_selectors  ──→ preprocessor.py: Step 2 element removal
  ├─ extraction.lazyload.*         ──→ preprocessor.py: Step 3 lazyload fix
  ├─ extraction.cleanup[]          ──→ preprocessor.py: Step 4 named operations
  ├─ extraction.image_filtering.*  ──→ preprocessor.py: Step 5 + converter.py
  ├─ extraction.selectors.content  ──→ preprocessor.py: Step 6 content selection
  ├─ extraction.text_normalization ──→ sample_converter.py: post-conversion regex
  ├─ extraction.url_conversion     ──→ sample_converter.py: relative→absolute URL fix
  ├─ extraction.youtube_cleanup    ──→ sample_converter.py: YouTube embed removal
  ├─ extraction.infobox_field_handlers ──→ infobox.py + converter.py: handler dispatch
  └─ extraction.selectors (always consumed by pipeline infrastructure)
```

## 7. Constraints and Design Principles

1. **Config-driven**: All site-specific behavior is sourced from strategy YAML frontmatter. No hardcoded selectors or domain names in converter code.
2. **Parser-agnostic infobox**: `extract_infobox()` works with both BS4 and selectolax, enabling code reuse across explore and pipeline paths.
3. **Separation of extraction and conversion**: `lib/extraction/` extracts structured data; `pipeline/converters/` transforms format. One-way dependency: converters → extraction library.
4. **Context-aware preprocessing**: Explore gets full 6-step cleanup; pipeline gets lightweight selector-based cleanup. No unnecessary processing.
5. **Balanced element removal**: `converter.py` uses depth-counting balanced tag removal (not regex) for nested HTML elements, avoiding malformed markup issues.

## 关联文档

- [02 — 管线数据流](02-pipeline-flow.md) — MediaWiki API 五阶段管线，converter 的运行时上下文
- [03 — 策略 Schema 参考](03-strategy-schema.md) — extraction.infox 等字段的权威定义
- [08 — 技术栈](08-tech-stack.md) — Python 依赖与兼容性约束
