# Pipeline Domain: HTML Preprocessing — Merged Spec

## Source Attribution

| Source Spec | Type |
|------------|------|
| `unified-html-preprocessing` | frozen |

Paths have been updated to reflect the current directory structure.

---

# HTML Preprocessing Specification

## Purpose

Provides context-driven HTML preprocessing for both explore and pipeline paths. Reads extraction config to determine which cleanup operations to execute, including lazyload image fixing, content area selection, and config-driven cleanup operations (strip infobox tables, ambox conversion, footer removal, edit link removal, etc.).

---

## Requirements

### Requirement: context-driven-preprocessing

系统 SHALL 在 `lib/extraction/preprocessor.py` 中提供 `preprocess_html()` 函数，接受 `html` 字符串、`config` dict、和 `context` 参数（`"explore"` 或 `"pipeline"`）。

#### Scenario: explore context full preprocessing
- **WHEN** `preprocess_html(html, config, context="explore")` 被调用
- **THEN** 函数 SHALL 按顺序执行：(1) 通过 `config.infobox.selector` 移除 infobox 容器，(2) 移除匹配 `config.cleanup_selectors` 的元素，(3) 通过 `config.lazyload` 修复 lazyload 图片，(4) 执行 `config.cleanup` 列表中的清理操作，(5) 移除匹配 `config.image_filtering.skip_patterns` 的装饰图片，(6) 通过 `config.selectors.content` 选择主内容

#### Scenario: pipeline context lightweight preprocessing
- **WHEN** `preprocess_html(html, config, context="pipeline")` 被调用
- **THEN** 函数 SHALL 执行轻量清理——这是未来用途的占位；Change 2 不修改 `html_to_markdown.py` 中的 `clean_html()`

### Requirement: config-driven-cleanup-operations

系统 SHALL 解释 `config.cleanup` 列表确定执行哪些清理操作，不硬编码操作名称。

#### Scenario: strip_fandom_infobox_tables
- **WHEN** `"strip_fandom_infobox_tables"` 在 cleanup 列表中
- **THEN** 带 `item-table-header`、`item-table-body`、`item-table-description`、`item-table-appearance`、`infobox-table`、`portable-infobox` 类的 table SHALL 被移除

#### Scenario: convert_ambox_to_text
- **WHEN** `"convert_ambox_to_text"` 在 cleanup 列表中
- **THEN** ambox table SHALL 被替换为含 `⚠️` 前缀的段落

#### Scenario: unwrap_image_wrappers
- **WHEN** `"unwrap_image_wrappers"` 在 cleanup 列表中
- **THEN** 仅包裹单个 `<img>` 的 `<a>` 元素 SHALL 被 unwrap（标签移除，子节点保留）

#### Scenario: strip_footer
- **WHEN** `"strip_footer"` 在 cleanup 列表中
- **THEN** 匹配 `#catlinks`、`#mw-hidden-catlinks`、`.printfooter`、`.mw-footer`、`#footer` 的元素 SHALL 被移除

#### Scenario: strip_edit_links
- **WHEN** `"strip_edit_links"` 在 cleanup 列表中
- **THEN** 匹配 `.mw-editsection` 的元素 SHALL 被移除

#### Scenario: strip_skip_links
- **WHEN** `"strip_skip_links"` 在 cleanup 列表中
- **THEN** accessibility skip-to-content 导航链接 SHALL 被移除

#### Scenario: strip_category_links
- **WHEN** `"strip_category_links"` 在 cleanup 列表中
- **THEN** 分类链接容器和 "Categories:" 段落 SHALL 被移除

#### Scenario: convert_nested_images
- **WHEN** `"convert_nested_images"` 在 cleanup 列表中
- **THEN** `<figure>` 和 `<picture>` wrapper SHALL 被替换为内部 `<img>` 子元素

### Requirement: config-driven-lazyload-fix

系统 SHALL 基于 `config.lazyload` 设置修复 lazyload 图片。

#### Scenario: lazyload enabled with placeholder and src_attr
- **WHEN** `config.lazyload.enabled` 为 true，`placeholder_pattern` 和 `real_src_attr` 已设置
- **THEN** `src` 包含 placeholder pattern 的图片 SHALL 将 `src` 替换为 `data-*` 属性值

### Requirement: content-selection

系统 SHALL 基于 `config.selectors.content` 选择主内容区域。

#### Scenario: content selector matches
- **WHEN** `config.selectors.content` 匹配 HTML 中的元素
- **THEN** 仅返回该元素的 HTML

#### Scenario: content selector no match
- **WHEN** `config.selectors.content` 不匹配
- **THEN** 返回完整 body 内容作为 fallback

### Requirement: output-html-string

系统 SHALL 返回清理后的 HTML 字符串（非解析对象）。

#### Scenario: successful preprocessing
- **WHEN** preprocessing 完成
- **THEN** 返回值 SHALL 为可传入 `convert_html_to_markdown()` 的原始 HTML 字符串
