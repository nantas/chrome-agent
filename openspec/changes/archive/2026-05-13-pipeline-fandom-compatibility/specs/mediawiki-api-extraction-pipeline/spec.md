# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction-pipeline`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: 用户确认需要修复 Phase A 页面过滤、Phase B None-safety、Phase B missingtitle 处理、Registry 补充

## 规范真源声明

- 本文件是 `mediawiki-api-extraction-pipeline` 在本次 change 中的行为规范真源

## ADDED Requirements

### Requirement: Phase A Fandom 翻译页过滤

The system SHALL 在 `run_phase_a()` 中，当 `platform_variant` 为 `"fandom"` 时，在生成 manifest 前过滤掉标题以 `_tr` 结尾的页面。

Fandom 将翻译页面（如 `Amir/tr`、`Items/tr`）放置在 ns=0（主命名空间），而标准 MediaWiki 通常在独立命名空间中。这导致 `allpages` 将翻译页计入内容页。

过滤逻辑 SHALL：
1. 在 `pages = discovery_strategy.discover_pages(client, strategy)` 之后
2. 遍历 pages，过滤掉 `title.endswith("/tr")` 或 `title.endswith("_tr")`
3. 记录过滤数量到日志

#### Scenario: 翻译页过滤

- **WHEN** Phase A 发现页面中包含 `"Items/tr"` 和 `"Amir/tr"`
- **AND** `platform_variant == "fandom"`
- **THEN** SHALL 从 pages 列表中移除 `"Items/tr"` 和 `"Amir/tr"`
- **AND** SHALL 记录日志 `"Filtered {count} translation pages (_tr)"`
- **AND** manifest 中 SHALL 不包含翻译页

#### Scenario: 非 Fandom 变体不过滤

- **WHEN** Phase A 发现页面中包含 `"Items/tr"` 但 `platform_variant != "fandom"`
- **THEN** SHALL 不过滤
- **AND** 行为与当前一致

### Requirement: Phase A 页面存在性验证

The system SHALL 在 `run_phase_a()` 中，当 `platform_variant` 为 `"fandom"` 时，在 manifest 生成前使用 `action=query&prop=info&titles=...` 批量验证发现的页面是否确实存在（返回 non-missing 的 pageid）。

验证逻辑 SHALL：
1. 将 pages 分批（每批 50 个 title）
2. 调用 `action=query&prop=info&titles=TITLE1|TITLE2|...`
3. 过滤掉返回 `missing` 的页面
4. 记录过滤数量和百分比

#### Scenario: 页面存在性验证

- **WHEN** Phase A 发现 566 个页面，其中 100 个在 `allpages` 中存在但 `prop=info` 返回 `missing`
- **AND** `platform_variant == "fandom"`
- **THEN** SHALL 从 pages 列表中移除 100 个 missing 页面
- **AND** SHALL 记录日志 `"Filtered {count} pages (missing in prop=info)"`

#### Scenario: 非 Fandom 变体不验证

- **WHEN** `platform_variant != "fandom"`
- **THEN** SHALL 跳过 prop=info 验证
- **AND** 行为与当前一致

### Requirement: Phase B PageNotFoundError 优雅处理

The system SHALL 在 `process_single_page()` 中增加对 `PageNotFoundError` 的捕获，返回 `status: "skipped"`。

同时，Phase B 的统计 SHALL 将 skipped 页面从 failure_count 中独立出来，且 50% failure rate 的 fallback 触发条件 SHALL 仅计算 `status: "error"` 页面（排除 `skipped`）。

#### Scenario: 统计区分 skipped

- **WHEN** Phase B 处理 500 个页面：400 success + 50 skipped + 50 error
- **THEN** `stats["success"]` SHALL 为 400
- **AND** `stats["failure"]` SHALL 为 50（仅 error，不含 skipped）
- **AND** `stats["skipped"]` SHALL 为 50
- **AND** `stats["failure_rate"]` SHALL 计算为 `50/500 = 10%`（分母为 total，非 total-skipped）
- **AND** 因 failure_rate 10% < 50%，不触发 Scrapling fallback

### Requirement: Registry 补充 fandom_infobox

The system SHALL 在 `_STRATEGY_REGISTRY["template_processor"]` 中注册 `"fandom_infobox": FandomInfoboxTemplateProcessor`。

`FandomInfoboxTemplateProcessor` SHALL 实现 `TemplateProcessor` 协议：
- `extract_frontmatter()`: 从 Fandom 的 `{{Infobox ...}}` 模板中提取参数到 frontmatter
- `expand_templates()`: 处理 Fandom 特定的模板（`{{ItemLink}}`、`{{MonsterLink}}` 等）
- `remove_infobox()`: 移除 wikitext 中的 infobox 模板调用
- `clean_remaining_templates()`: 清理其他残余模板标记

当前版本 SHALL 是一个最小可用实现：至少能正确解析 `{{Infobox item|name=...|image=...|description=...}}` 格式。

#### Scenario: Fandom infobox 解析

- **WHEN** wikitext 包含 `{{Infobox item|name=Acorn|image=Acorn.png|description=An acorn.}}`
- **THEN** `extract_frontmatter()` SHALL 返回 `{"name": "Acorn", "image": "Acorn.png", "description": "An acorn."}`
- **AND** `remove_infobox()` SHALL 从 wikitext 中移除该模板调用
