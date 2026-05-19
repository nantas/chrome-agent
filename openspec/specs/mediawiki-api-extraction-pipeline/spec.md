# mediawiki-api-extraction-pipeline Specification

## Purpose
TBD - created by archiving change pipeline-fandom-compatibility. Update Purpose after archive.
## Requirements
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

### Requirement: Pipeline 启动时策略 schema hard-fail 校验
The system SHALL 在 `run_pipeline()` 中启动阶段增加对策略文件 `content_profile` 的 schema 校验。

校验位置：在 `build_pipeline()` 调用之后、`validate_api_config()` 之前或结合。

校验逻辑：
1. 读取策略文件的 `api.content_profile` 字段
2. 遍历每个字段，检查其 value 是否在 `_STRATEGY_REGISTRY` 对应维度的 key 集合中
3. 所有 ID 有效 → 正常继续
4. 存在无效 ID → `log.error` + `return EXIT_STRATEGY_ERROR`
5. 未指定 `content_profile`（全默认）→ 跳过校验

#### Scenario: 校验通过
- **WHEN** 策略文件指定 `content_profile: { link_resolver: "exact_title_match" }`
- **AND** `"exact_title_match"` 在 `_STRATEGY_REGISTRY["link_resolver"]` 中存在
- **THEN** pipeline SHALL 正常进入后续阶段
- **AND** SHALL 不发出关于 strategy ID 的警告

#### Scenario: 校验拒绝
- **WHEN** 策略文件指定 `content_profile: { link_resolver: "short_name" }`
- **AND** `"short_name"` 在 `_STRATEGY_REGISTRY["link_resolver"]` 中不存在
- **THEN** pipeline SHALL 记录 `log.error("Strategy ID '%s' not registered in %s", id, dimension)`
- **AND** SHALL 返回 `EXIT_STRATEGY_ERROR`
- **AND** SHALL 不执行任何后续管线阶段

#### Scenario: 无 content_profile
- **WHEN** 策略文件未指定 `api.content_profile`
- **THEN** `build_pipeline()` SHALL 使用所有默认策略实现
- **AND** SHALL 不触发 content_profile 校验
- **AND** pipeline SHALL 正常启动

### Requirement: Pipeline platform_variant 行为分支
The system SHALL 在 pipeline 的以下阶段根据 `platform_variant` 值选择行为分支：

1. `run_pipeline()`：解析 `strategy.get("api", {}).get("platform_variant", "standard")` 并传递给下游阶段
2. `run_phase_a()`：Fandom variant 时增加页面存在性验证和翻译页过滤
3. `run_phase_b()` 中的 `process_single_page()`：Fandom variant 时错误处理分支
4. 后续 Phase B/C 的 HTML 清理：variant 指定的 cleanup 规则选择

当前 change 仅定义框架接口。具体的行为分支实现（如上所列）是**可选的**——实现只需要确保 `platform_variant` 字段能被 pipeline 读取和传递。

#### Scenario: Variant 传递
- **WHEN** `run_pipeline()` 执行
- **THEN** 它 SHALL 从策略文件的 `api.platform_variant` 读取版本值
- **AND** SHALL 作为参数传递给 `run_phase_a()` 和 `run_phase_b()`
- **AND** 当未指定时默认为 `"standard"`
- **AND** 当前至少 SHALL 记录 `log.info("Platform variant: %s", variant)` 以便追踪

#### Scenario: 新增 variant 时的分支扩展
- **WHEN** 一个新的 variant 值（如 `"fandom"`）需要在 pipeline 中支持
- **THEN** 开发者 SHALL 在对应的阶段函数中添加 `if variant == "fandom":` 分支
- **AND** SHALL 保持 `standard` 分支的当前行为不变
- **AND** SHALL 确保扩展的变体分支不影响非变体行为

### Requirement: Registry 暴露为可导入模块
The system SHOULD 将 `_STRATEGY_REGISTRY` 从 `orchestrate.py` 的模块级私有变量提升为可被外部模块（如 `bootstrap-strategy` 的 `strategy_scaffold_generator.py`）导入的公共 API。

最低要求：
- 通过 `from ..pipeline.orchestrate import STRATEGY_REGISTRY` 可导入
- 保持 `_STRATEGY_REGISTRY` 作为内部别名的兼容性

#### Scenario: 外部导入 registry
- **WHEN** `strategy_scaffold_generator.py` 需要校验生成的 content_profile ID
- **THEN** 它 SHALL 导入 `from ..pipeline.orchestrate import STRATEGY_REGISTRY`
- **AND** 遍历生成的 `content_profile` 字段，逐个 ID 检查存在性
- **AND** 存在未注册 ID 时停止写入

### Requirement: phase-homepage-entry-point

The system SHALL support `--phase homepage` as a pipeline entry point that runs homepage-driven discovery followed by Phase B and Phase C.

When `--phase homepage` is specified:
- Phase 0 SHALL execute before Phase B
- Phase A SHALL be skipped (discovery is homepage-driven, not allpages)
- The manifest produced by Phase 0 SHALL be consumed by Phase B

#### Scenario: phase-homepage-with-bc

- **WHEN** `chrome-agent mediawiki pipeline --phase homepage,B,C` is invoked
- **THEN** Phase 0 (homepage discovery + page assignment) SHALL execute
- **THEN** Phase B SHALL consume the Phase 0 manifest
- **THEN** Phase C SHALL execute normally
- **THEN** Phase A SHALL NOT execute

#### Scenario: phase-homepage-only

- **WHEN** `chrome-agent mediawiki pipeline --phase homepage` is invoked
- **THEN** only Phase 0 SHALL execute, producing a manifest
- **THEN** no extraction or assembly SHALL be performed

#### Scenario: phase-homepage-missing-strategy

- **WHEN** `--phase homepage` is specified but strategy has no `api.homepage` config
- **THEN** pipeline SHALL log error and return non-zero exit code
- **THEN** no API calls SHALL be made

### Requirement: standalone-redirect-handling

The system SHALL include `redirects=true` in all MediaWiki `action=parse` API calls made by `standalone.py`.

`fetch_and_convert()` SHALL pass `redirects=true` when calling `client.parse()`.

#### Scenario: standalone-follows-redirect

- **WHEN** `fetch_and_convert()` is called for a page that is a redirect (e.g., `Main_Page`)
- **THEN** the API call SHALL include `redirects=true`
- **THEN** the returned content SHALL be from the resolved page
- **THEN** the output SHALL contain content, not an empty file

### Requirement: explore-redirect-handling

The system SHALL include `redirects=true` in the `_fetch_wikitext()` MediaWiki API call in `scripts/explore/main.py`.

#### Scenario: explore-wikitext-fetch-follows-redirect

- **WHEN** `_fetch_wikitext()` is called for a page that is a redirect
- **THEN** the API call SHALL include `redirects=true`
- **THEN** the returned wikitext SHALL be from the resolved page

### Requirement: auto-link-fix-after-pipeline

The system SHALL automatically invoke `fix_links_in_dir()` after Phase C completes (or after Phase B if Phase C is not run).

#### Scenario: link-fix-after-phase-c

- **WHEN** pipeline completes Phase C successfully
- **THEN** `fix_links_in_dir(output_dir, domain, manifest_pages)` SHALL be called
- **THEN** link fix statistics SHALL be logged
- **THEN** link fix failure SHALL NOT cause pipeline failure (logged as warning)

#### Scenario: link-fix-after-phase-b-only

- **WHEN** pipeline runs only Phase B (no Phase C)
- **THEN** `fix_links_in_dir()` SHALL still be called after Phase B completes

## Requirements from change: split-fetch-convert-phases

### ADDED

#### Requirement: run-phase-fetch
The system SHALL 提供 `run_phase_fetch(client, manifest, strategy, rate_limit_config, domain, content_strategy)` 函数，执行独立的 fetch 流程：

1. 遍历 manifest 中所有页面
2. 对每个页面调用 `content_strategy.fetch_page_content(client, title, {})` 获取原始内容
3. 将返回的 raw dict 写入缓存（`save_page_cache(domain, raw_data)`）
4. 支持缓存跳过：已缓存页面不重复请求
5. 使用与 `run_phase_b()` 相同的 `ThreadPoolExecutor` 并发和 rate limit 控制

##### Scenario: fetch-phase-execution
- **WHEN** `run_phase_fetch()` 被调用
- **AND** manifest 包含 1769 个页面
- **THEN** SHALL 对无缓存的页面调用 API 获取内容
- **AND** SHALL 将每个成功获取的页面写入 `.cache/mediawiki/<domain>/<safe_title>.json`
- **AND** SHALL 跳过已有缓存的页面
- **AND** SHALL NOT 执行任何 Markdown 转换

#### Requirement: run-phase-convert
The system SHALL 提供 `run_phase_convert(output_dir, manifest, strategy, domain)` 函数，执行独立的 convert→assembly 流程：

1. 遍历 manifest 中所有页面
2. 对每个页面从缓存加载 raw dict（`load_page_cache(domain, title)`）
3. 调用 `convert_single_page(raw, page_info, manifest_pages, domain, ...)` 执行转换
4. 将生成的 Markdown 写入 output_dir
5. 更新 `extraction_results.json` 包含 `content` 和 `rendered_html`
6. 自动执行 assembly phase

##### Scenario: convert-phase-execution
- **WHEN** `run_phase_convert()` 被调用
- **THEN** SHALL NOT 创建 `ApiClient` 实例
- **AND** SHALL NOT 发起任何 HTTP 请求
- **AND** SHALL 从缓存加载所有页面的原始内容

#### Requirement: process-single-page-refactor
`process_single_page()` SHALL 重构为两个函数：

1. `fetch_single_page(client, page_info, domain, content_strategy) -> dict`：仅调 API 获取内容，返回 raw dict，同时写入缓存
2. `convert_single_page(raw, page_info, manifest_pages, domain, frontmatter_fields, template_map, link_resolver, template_processor, extraction_config) -> dict`：仅执行 HTML→Markdown 转换，返回结果 dict

保留 `process_single_page()` 作为兼容包装（内部调用 fetch + convert）。

##### Scenario: fetch-single-page
- **WHEN** `fetch_single_page()` 被调用
- **THEN** SHALL 调用 `content_strategy.fetch_page_content()`
- **AND** SHALL 将 raw dict 写入 CPU 缓存文件
- **AND** SHALL 返回 raw dict

##### Scenario: convert-single-page
- **WHEN** `convert_single_page()` 被调用并以 raw dict 为输入
- **THEN** SHALL 从 raw dict 提取 `html`/`wikitext`/`images`
- **AND** SHALL 调用 `HtmlToMarkdownConverter.convert_body()` 或 `convert_wikitext_to_markdown()`
- **AND** SHALL 返回 `{title, status, content, warnings, frontmatter, rendered_html}`

### MODIFIED

#### Requirement: extraction-results-json-content
`extraction_results.json` 保存时 SHALL 包含每个页面的 `content`（Markdown 正文）和 `rendered_html`（原始 HTML），不仅 `status` 和 `error`。

##### Scenario: extraction-results-full-content
- **WHEN** convert phase 完成
- **THEN** `extraction_results.json` 中每个页面条目 SHALL 包含 `status`、`error`、`content`、`rendered_html`、`images` 字段
- **AND** `--phase assemble` 加载结果时 SHALL 能完整重建 results dict

#### Requirement: pipeline-phase-choices
`--phase` CLI 参数的 choices SHALL 更新为：`all`、`discover`、`fetch`、`convert`、`assemble`。

`--phase all` SHALL 依次执行 discover → fetch → convert（fetch 阶段利用缓存跳过已有页面）。

##### Scenario: phase-all-behavior
- **WHEN** 执行 `--phase all`
- **THEN** SHALL 执行完整的 discover → fetch → convert 流程
- **AND** fetch 阶段 SHALL 跳过已有缓存的页面

##### Scenario: phase-fetch-only
- **WHEN** 执行 `--phase fetch`
- **THEN** SHALL 仅执行 discover（需要时）+ fetch
- **AND** SHALL NOT 执行 convert 或 assembly

### REMOVED

#### Requirement: phase-extract
**Reason**: `extract` phase 被 `fetch` + `convert` 两个独立 phase 替代，不再保留合体选项。

**Migration**: 原 `--phase extract` 用户改用 `--phase all`（全流程）或 `--phase fetch` + `--phase convert`（两步）。

#### Requirement: deprecated-phase-values
**Reason**: deprecated 值 `A`、`B`、`C`、`homepage` 已标记废弃多时，本次一并移除。

**Migration**:
- `A` / `B` → 使用 `--phase fetch` 或 `--phase convert`
- `C` → 使用 `--phase assemble`
- `homepage` → 使用 `--discovery homepage`
