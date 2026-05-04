# Writeback Report

## Change

- **Name:** mediawiki-strategy-with-extraction-patterns
- **Schema:** orbitos-change-v1

---

## 回写目标 (Writeback Targets)

| # | 目标文件 | 状态 | 说明 |
|---|----------|------|------|
| 1 | `sites/strategies/vampire.survivors.wiki/strategy.md` | ✅ 已写入 | 新建站点策略文件，含完整 frontmatter 与 Markdown body |
| 2 | `sites/strategies/vampire.survivors.wiki/_attachments/clean-mediawiki.sh` | ✅ 已写入 | 噪音清洗脚本，支持 3 个 profile 与 4 个 rule cluster |
| 3 | `sites/strategies/vampire.survivors.wiki/_attachments/extract-links.py` | ✅ 已写入 | 分类页内部 wiki 链接提取脚本，支持 URL 过滤与去重 |
| 4 | `docs/patterns/mediawiki-extraction.md` | ✅ 已写入 | 通用 MediaWiki 提取模式参考文档 (v1 draft) |
| 5 | `sites/strategies/registry.json` | ✅ 已更新 | 新增 vampire.survivors.wiki 索引条目 |
| 6 | `AGENTS.md` (section 7) | ⏭️ 无需变更 | 遵循既有策略库治理规则，无 schema 变更 |

---

## 字段映射

### registry.json 新增条目

| 字段 | 值 |
|------|-----|
| `domain` | `vampire.survivors.wiki` |
| `description` | `Weird Gloop hosted MediaWiki for Vampire Survivors` |
| `protection_level` | `low` |
| `page_types` | `["static_page", "static_article"]` |
| `pagination` | `["none"]` |
| `entry_points` | `["wiki_category"]` |
| `anti_crawl_refs` | `[]` |
| `file` | `vampire.survivors.wiki/strategy.md` |

### strategy.md frontmatter

| 字段 | 值 |
|------|-----|
| `domain` | `vampire.survivors.wiki` |
| `description` | `Weird Gloop hosted MediaWiki for Vampire Survivors` |
| `protection_level` | `low` |
| `anti_crawl_refs` | `[]` |
| `engine_preference.preferred` | `scrapling-get` |
| `engine_preference.fallback` | `obscura-fetch` |
| `structure.pages` | `wiki_category` (static_page), `wiki_article` (static_article) |
| `structure.entry_points` | `[wiki_category]` |
| `extraction.image_handling.attribute` | `src` |
| `extraction.image_handling.output_format` | `markdown_inline` |
| `extraction.cleanup` | 9 个 MediaWiki 噪音规则标识符 |

---

## 执行摘要

### 新增能力

- **`mediawiki-site-strategy`**: 为 vampire.survivors.wiki 注册完整站点策略，使 `chrome-agent crawl` 可执行 bounded traversal。
- **`mediawiki-extraction-patterns`**: 沉淀 Weird Gloop MediaWiki 的 4 类噪音分类学与跨站点复用指南。
- **`mediawiki-cleanup-script`**: 提供可复用的噪音清洗脚本（`clean-mediawiki.sh`）与链接提取脚本（`extract-links.py`）。

### 验证结果

- `chrome-agent crawl` 试跑成功，3 页 bounded traversal 未越界。
- `clean-mediawiki.sh` 在 vampire-survivors 与 balatro profile 下均成功清洗 Scrapling 输出。
- `extract-links.py` 从 balatrowiki.org 首页成功提取 33 条有效内部 wiki 链接。
- `registry.json` 通过 JSON 解析验证，结构与既有条目一致。

### 未变更项

- **引擎注册表** (`configs/engine-registry.json`): 无需变更，现有引擎已覆盖需求 (`scrapling-get`, `obscura-fetch`)。
- **AGENTS.md**: 策略库治理规则（section 7）无需变更；新增策略完全遵循既有目录结构与 frontmatter 规范。
- **反爬策略库** (`sites/anti-crawl/`): `protection_level=low`，无需新增反爬策略。

### 已知限制

- `chrome-agent crawl` 的链接选择器仅支持简单 `href*="..."` / `href="..."` 模式，不支持 CSS 伪类。当前策略已在此约束下工作，并在 `strategy.md` 中记录该限制。
- `generic-mediawiki` profile 启用全部规则，对未知站点可能过于激进，已添加 `--dry-run` 与运行时警告。
- `balatro` profile 基于推断规则，标记为 draft，建议完整验证后再提升为 frozen。

---

## 变更归档建议

本 change 的所有 artifact 已完成实现与验证。可执行 `/opsx-archive` 进行归档。
