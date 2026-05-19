# Specification Delta

## Capability 对齐（已确认）

- Capability: `mediawiki-api-extraction-pipeline`
- 来源: `proposal.md` — Modified Capabilities
- 变更类型: `modified`
- 用户确认摘要: Phase B 拆分为 fetch 和 convert 两个独立 phase；`--phase` choices 新增 `fetch`、`convert`，移除 `extract` 及所有 deprecated 值；`extraction_results.json` 保存 `content` 和 `rendered_html` 以修复 assemble 阶段数据丢失。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: run-phase-fetch
The system SHALL 提供 `run_phase_fetch(client, manifest, strategy, rate_limit_config, domain, content_strategy)` 函数，执行独立的 fetch 流程：

1. 遍历 manifest 中所有页面
2. 对每个页面调用 `content_strategy.fetch_page_content(client, title, {})` 获取原始内容
3. 将返回的 raw dict 写入缓存（`save_page_cache(domain, raw_data)`）
4. 支持缓存跳过：已缓存页面不重复请求
5. 使用与 `run_phase_b()` 相同的 `ThreadPoolExecutor` 并发和 rate limit 控制

#### Scenario: fetch-phase-execution
- **WHEN** `run_phase_fetch()` 被调用
- **AND** manifest 包含 1769 个页面
- **THEN** SHALL 对无缓存的页面调用 API 获取内容
- **AND** SHALL 将每个成功获取的页面写入 `.cache/mediawiki/<domain>/<safe_title>.json`
- **AND** SHALL 跳过已有缓存的页面
- **AND** SHALL NOT 执行任何 Markdown 转换

### Requirement: run-phase-convert
The system SHALL 提供 `run_phase_convert(output_dir, manifest, strategy, domain)` 函数，执行独立的 convert→assembly 流程：

1. 遍历 manifest 中所有页面
2. 对每个页面从缓存加载 raw dict（`load_page_cache(domain, title)`）
3. 调用 `convert_single_page(raw, page_info, manifest_pages, domain, ...)` 执行转换
4. 将生成的 Markdown 写入 output_dir
5. 更新 `extraction_results.json` 包含 `content` 和 `rendered_html`
6. 自动执行 assembly phase

#### Scenario: convert-phase-execution
- **WHEN** `run_phase_convert()` 被调用
- **THEN** SHALL NOT 创建 `ApiClient` 实例
- **AND** SHALL NOT 发起任何 HTTP 请求
- **AND** SHALL 从缓存加载所有页面的原始内容

### Requirement: process-single-page-refactor
`process_single_page()` SHALL 重构为两个函数：

1. `fetch_single_page(client, page_info, domain, content_strategy) -> dict`：仅调 API 获取内容，返回 raw dict，同时写入缓存
2. `convert_single_page(raw, page_info, manifest_pages, domain, frontmatter_fields, template_map, link_resolver, template_processor, extraction_config) -> dict`：仅执行 HTML→Markdown 转换，返回结果 dict

保留 `process_single_page()` 作为兼容包装（内部调用 fetch + convert）。

#### Scenario: fetch-single-page
- **WHEN** `fetch_single_page()` 被调用
- **THEN** SHALL 调用 `content_strategy.fetch_page_content()`
- **AND** SHALL 将 raw dict 写入 CPU 缓存文件
- **AND** SHALL 返回 raw dict

#### Scenario: convert-single-page
- **WHEN** `convert_single_page()` 被调用并以 raw dict 为输入
- **THEN** SHALL 从 raw dict 提取 `html`/`wikitext`/`images`
- **AND** SHALL 调用 `HtmlToMarkdownConverter.convert_body()` 或 `convert_wikitext_to_markdown()`
- **AND** SHALL 返回 `{title, status, content, warnings, frontmatter, rendered_html}`

## MODIFIED Requirements

### Requirement: extraction-results-json-content
`extraction_results.json` 保存时 SHALL 包含每个页面的 `content`（Markdown 正文）和 `rendered_html`（原始 HTML），不仅 `status` 和 `error`。

#### Scenario: extraction-results-full-content
- **WHEN** convert phase 完成
- **THEN** `extraction_results.json` 中每个页面条目 SHALL 包含 `status`、`error`、`content`、`rendered_html`、`images` 字段
- **AND** `--phase assemble` 加载结果时 SHALL 能完整重建 results dict

### Requirement: pipeline-phase-choices
`--phase` CLI 参数的 choices SHALL 更新为：`all`、`discover`、`fetch`、`convert`、`assemble`。

`--phase all` SHALL 依次执行 discover → fetch → convert（fetch 阶段利用缓存跳过已有页面）。

#### Scenario: phase-all-behavior
- **WHEN** 执行 `--phase all`
- **THEN** SHALL 执行完整的 discover → fetch → convert 流程
- **AND** fetch 阶段 SHALL 跳过已有缓存的页面

#### Scenario: phase-fetch-only
- **WHEN** 执行 `--phase fetch`
- **THEN** SHALL 仅执行 discover（需要时）+ fetch
- **AND** SHALL NOT 执行 convert 或 assembly

## REMOVED Requirements

### Requirement: phase-extract
**Reason**: `extract` phase 被 `fetch` + `convert` 两个独立 phase 替代，不再保留合体选项。

**Migration**: 原 `--phase extract` 用户改用 `--phase all`（全流程）或 `--phase fetch` + `--phase convert`（两步）。

### Requirement: deprecated-phase-values
**Reason**: deprecated 值 `A`、`B`、`C`、`homepage` 已标记废弃多时，本次一并移除。

**Migration**: 
- `A` / `B` → 使用 `--phase fetch` 或 `--phase convert`
- `C` → 使用 `--phase assemble`
- `homepage` → 使用 `--discovery homepage`
