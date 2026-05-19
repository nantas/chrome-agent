# pipeline-convert-phase Specification

## Purpose
独立的 convert phase，从持久化缓存读取原始内容，应用 strategy extraction 规则执行 HTML→Markdown 转换。纯本地执行，无网络请求。需要 `--from-manifest` 定位页面目录分配。

## Requirements

### Requirement: convert-phase-cli-entry
The system SHALL 支持 `--phase convert` CLI 参数。

`--phase convert` 的行为 SHALL 为：
1. 要求必须提供 `--from-manifest`（缺少时 SHALL 报错退出）
2. 遍历 manifest 中所有页面
3. 对每个页面，从缓存读取原始内容
4. 应用 strategy extraction 配置执行 HTML→Markdown 转换
5. 将生成的 Markdown 写入 output 目录
6. 转换完成后执行 assembly phase（生成 index.md、链接修复、验证）

#### Scenario: convert-without-manifest
- **WHEN** 执行 `--phase convert` 但未提供 `--from-manifest`
- **THEN** SHALL 报错并退出，错误信息为 `"--phase convert requires --from-manifest"`
- **AND** exit code SHALL 非零

#### Scenario: convert-with-manifest
- **WHEN** 执行 `--phase convert --from-manifest <path>`
- **THEN** SHALL 加载 manifest 中的页面列表和目录分配
- **AND** SHALL 对每个页面执行 `convert_single_page()`

### Requirement: convert-from-cache
convert phase 的每个页面处理 SHALL 从缓存文件读取原始内容，而非发起 API 请求。

MediaWiki API 路径：读取 `<cache_root>/<safe_title>.json`，从中提取 `html`、`rendered_html`、`wikitext`、`images` 字段构造 `raw` dict（格式与当前 `fetch_page_content()` 返回一致）。

Scrapling 路径：读取 `<cache_root>/<slug>.html`，构造用于转换的 HTML 字符串。

#### Scenario: mediawiki-convert-from-cache
- **WHEN** convert 页面 `The Lamb`
- **AND** `.cache/mediawiki/<domain>/The_Lamb.json` 存在
- **THEN** SHALL 读取 JSON 文件
- **AND** SHALL 构造 raw dict 包含 `html`、`rendered_html`、`images` 字段
- **AND** SHALL 调用 `HtmlToMarkdownConverter.convert_body()` 执行转换
- **AND** SHALL NOT 发起任何 HTTP 请求

#### Scenario: scrapling-convert-from-cache
- **WHEN** convert URL `https://example.com/docs/intro`
- **AND** `.cache/scrapling/example.com/docs_intro.html` 存在
- **THEN** SHALL 读取 HTML 文件
- **AND** SHALL 通过 Scrapling CLI `--ai-targeted file://` 或 `htmlToMarkdown()` 执行转换

### Requirement: convert-cache-miss-handling
当缓存文件不存在时，convert phase SHALL 将该页面标记为失败，SHALL NOT 回退到 API 请求。

#### Scenario: cache-miss-during-convert
- **WHEN** convert 页面 `Blessed Penny`
- **AND** `.cache/mediawiki/<domain>/Blessed_Penny.json` 不存在（fetch 阶段失败）
- **THEN** SHALL 标记该页为 `"status": "error"`，`"error": "cache_miss"`（不经 API 重试）
- **AND** 继续处理后续页面

### Requirement: convert-phase-no-network
convert phase SHALL NOT 发起任何网络请求。所有输入来自本地缓存文件。

#### Scenario: convert-offline
- **WHEN** 执行 `--phase convert`
- **THEN** 即使目标网站不可达，convert SHALL 正常完成
- **AND** SHALL NOT 调用 `ApiClient` 或 `runEngineFetch`

### Requirement: convert-strategy-extraction-config
convert phase SHALL 使用 strategy 文件中的 `extraction.*` 配置（`cleanup_selectors`、`infobox`、`image_filtering`、`lazyload` 等）执行转换。

修改 strategy 文件的 `extraction` 规则后，重新执行 `--phase convert` SHALL 产出反映新规则的 Markdown 输出。

#### Scenario: extraction-config-change
- **WHEN** strategy 的 `extraction.cleanup_selectors` 新增一个选择器
- **AND** 执行 `--phase convert --from-manifest <path>`（使用同一缓存）
- **THEN** 新生成的 Markdown SHALL 应用新增的清理规则
- **AND** SHALL NOT 重新发起 API 请求

### Requirement: convert-phase-summary
convert 完成后 SHALL 输出摘要：总页面数、成功转换数、缓存缺失数、转换失败数。

#### Scenario: convert-summary
- **WHEN** convert phase 完成
- **THEN** 日志 SHALL 输出 `"Convert phase complete: 1769 total, 1757 converted, 12 cache_miss, 0 failed"`

### Requirement: convert-phase-assembly
convert phase 完成后 SHALL 自动执行 assembly phase（与 `--phase all` 行为一致）：
1. 将 Markdown 写入 `output_dir/<target_directory>/<target_filename>`
2. 生成各目录 `index.md`
3. 执行链接修复（`fix_links_in_dir`）
4. 执行 L6 验证（如启用）

#### Scenario: auto-assembly-after-convert
- **WHEN** convert phase 成功完成
- **THEN** SHALL 按 manifest 目录分配写入 .md 文件
- **AND** SHALL 生成目录索引
- **AND** SHALL 执行链接 relativize
