# Pipeline Domain: Core — Merged Spec

## Source Attribution

| Source Spec | Type |
|------------|------|
| `mediawiki-api-extraction-pipeline` | frozen |
| `pipeline-cli-entry` | frozen |
| `pipeline-package-identity` | frozen |

Paths have been updated to reflect the current directory structure (`scripts/pipeline/`).

---

# Pipeline Core Specification

## Purpose

Defines the MediaWiki API extraction pipeline's core identity: package structure, CLI entry points, phase lifecycle, and the split fetch/convert architecture. Covers `__main__.py` invocation, CLI subcommand routing, package naming, and the high-level pipeline flow from discovery through fetch, convert, and assembly.

---

## Requirements

### Requirement: package-rename

系统 SHALL 使用 `scripts/pipeline/` 作为包目录。所有内部相对 import 保持不变，所有绝对 import 路径使用 `scripts.pipeline`。

#### Scenario: directory-rename
- **WHEN** `scripts/pipeline/` 目录存在
- **THEN** 所有文件内容保留，所有 Python 绝对 import 路径使用 `scripts.pipeline`

#### Scenario: absolute-imports-updated
- **WHEN** 在 `scripts/pipeline/` 中搜索 `mediawiki_api_extract`
- **THEN** 所有 Python 绝对 import 路径已更新为 `scripts.pipeline`
- **AND** docstring 和注释中的旧路径引用也已更新

### Requirement: main-simplification

`__main__.py` SHALL 直接执行 `from .cli import main`（因 `pipeline` 无连字符，无需 re-invoke workaround）。

#### Scenario: run-as-directory-script
- **WHEN** 执行 `python3 scripts/pipeline <url> --strategy <path> --output <dir>`
- **THEN** 系统 SHALL 正确初始化包路径，以退出码 0 完成管线运行

#### Scenario: run-as-module
- **WHEN** 执行 `python3 -m scripts.pipeline <url> --strategy <path> --output <dir>`
- **THEN** 系统 SHALL 以退出码 0 完成管线运行

### Requirement: main-runnable-as-script

`__main__.py` SHALL 在被 `python3 scripts/pipeline` 直接运行时正确设置 `sys.path`，使包内相对导入正常工作。

#### Scenario: run-as-directory-script
- **WHEN** 执行 `python3 scripts/pipeline <url> --strategy <path> --output <dir>`
- **THEN** 系统 SHALL 正确初始化包路径，以退出码 0 完成管线运行

### Requirement: cli-subcommand-routing

CLI 入口 SHALL 支持子命令路由：`pipeline`（默认）、`fetch`、`reprocess`、`fix-links`、`reconvert`。

#### Scenario: default-pipeline-subcommand
- **WHEN** 执行 `python3 -m scripts.pipeline <url> --strategy <path> --output <dir>`（无显式子命令）
- **THEN** 系统 SHALL 执行全量管线

#### Scenario: fetch-subcommand
- **WHEN** 执行 `python3 -m scripts.pipeline fetch <url> --domain <d> --mode html --output <file>`
- **THEN** 系统 SHALL 路由到 `standalone-extraction` 的单页面获取逻辑

#### Scenario: reprocess-subcommand
- **WHEN** 执行 `python3 -m scripts.pipeline reprocess <url> --pages "A,B" --manifest <path> --output <dir>`
- **THEN** 系统 SHALL 路由到 `incremental-reprocess` 的增量补救逻辑

#### Scenario: fix-links-subcommand
- **WHEN** 执行 `python3 -m scripts.pipeline fix-links <dir> --domain <d> --manifest <path>`
- **THEN** 系统 SHALL 路由到 `unified-link-fixer` 的链接修复逻辑

### Requirement: chrome-agent-cli-path

`chrome-agent-cli.mjs` SHALL 使用 `-m scripts.pipeline` 模式调用管线。

#### Scenario: cli-mjs-api-route
- **WHEN** `chrome-agent-cli.mjs` 检测到 `api.platform=mediawiki`
- **THEN** 它 SHALL 执行 `spawnSync("python3", ["-m", "scripts.pipeline", url, "--strategy", path, "--output", dir, ...])`

### Requirement: logger-name-update

所有 Python 模块中的 logger SHALL 统一使用 `getLogger("pipeline")`（子模块可用 `pipeline.converters` 等点分格式）。

#### Scenario: logger-consistency
- **WHEN** 在 `scripts/pipeline/` 中搜索旧 logger 名称
- **THEN** 返回 0 匹配

### Requirement: external-reference-update

`scripts/explore/` 中引用旧路径的文件 SHALL 更新为 `scripts.pipeline` 路径。

#### Scenario: explore-references
- **WHEN** 在 `scripts/explore/` 中搜索旧包名
- **THEN** 返回 0 匹配

### Requirement: test-reference-update

测试文件中引用旧包路径的 SHALL 更新。

#### Scenario: test-path-update
- **WHEN** 在 `scripts/pipeline/tests/` 中搜索旧包名
- **THEN** 返回 0 匹配

### Requirement: exclude-category-cli-parameter

Pipeline CLI 的 `_add_pipeline_args()` SHALL 支持 `--exclude-category` 参数，类型为 `action="append"`（repeatable），默认值为 `None`。

#### Scenario: single-exclude-category
- **WHEN** 执行 `pipeline <url> --strategy <path> --output <dir> --exclude-category "Music"`
- **THEN** `args.exclude_category` SHALL 为 `["Music"]`

#### Scenario: multiple-exclude-category
- **WHEN** 执行 `pipeline <url> --strategy <path> --output <dir> --exclude-category "Music" --exclude-category "Modding" --exclude-category "Version History"`
- **THEN** `args.exclude_category` SHALL 为 `["Music", "Modding", "Version History"]`

#### Scenario: no-exclude-category-specified
- **WHEN** 执行 `pipeline <url> --strategy <path> --output <dir>`（无 `--exclude-category`）
- **THEN** `args.exclude_category` SHALL 为 `None`

### Requirement: exclude-category-merge-logic

`orchestrator.py` 的 `run_pipeline()` SHALL 在 discovery 执行前合并策略文件的 `api.homepage.exclude_categories` 和 CLI 的 `--exclude-category`：

- 合并 SHALL 取并集，自动去重
- 合并后的列表 SHALL 传递给 discovery phase
- 日志 SHALL 以 info 级别输出排除分类的来源统计

#### Scenario: merge-strategy-and-cli-takes-union
- **WHEN** 策略 `exclude_categories` 为 `["Music", "Modding"]` 且 CLI 传入 `--exclude-category "Version History" --exclude-category "Music"`
- **THEN** 传递的排除列表 SHALL 为 `["Music", "Modding", "Version History"]`（顺序不保证）

### Requirement: re-fetch-cli-flag

The system SHALL 支持 `--re-fetch` CLI flag。当与 `--phase fetch` 或 `--phase all` 一起使用时，SHALL 忽略已有缓存，强制重新获取所有页面并覆盖缓存文件。

#### Scenario: re-fetch-flag
- **WHEN** 执行 `--phase fetch --re-fetch`
- **THEN** SHALL 不检查缓存存在性
- **AND** SHALL 对所有页面重新发起 API 请求并覆盖已有缓存文件

### Requirement: cache-root-resolution

The system SHALL 在 pipeline 入口处解析缓存根目录：读取 strategy 文件 → 提取 `api.platform`（或 `"scrapling"`）→ 提取 `domain` → 构造 `.cache/<platform>/<domain>/` 路径 → 自动创建目录。

#### Scenario: cache-root-resolution-mediawiki
- **WHEN** strategy 的 `api.platform` 为 `"mediawiki"` 且 `domain` 为 `"bindingofisaacrebirth.wiki.gg"`
- **THEN** `cache_root` SHALL 解析为 `<repo_root>/.cache/mediawiki/bindingofisaacrebirth.wiki.gg/`

### Requirement: phase-choices

`--phase` CLI 参数的 choices SHALL 为：`all`、`discover`、`fetch`、`convert`、`assemble`。移除的值：`"extract"`、`"A"`、`"B"`、`"C"`、`"homepage"`。

#### Scenario: valid-phase-choices
- **WHEN** 用户传入 `--phase fetch`
- **THEN** argparse SHALL 接受该值

#### Scenario: invalid-phase-choice
- **WHEN** 用户传入 `--phase extract`
- **THEN** argparse SHALL 拒绝

### Requirement: phase-forwarding-from-cli

`chrome-agent-cli.mjs` 中的 `runCrawl()` SHALL 将 `--phase` 参数传递到 Python pipeline。

#### Scenario: phase-forwarding
- **WHEN** JS CLI 执行 `runCrawl()` 且用户指定 `--phase fetch` 且 strategy 的 `api.platform` 为 `"mediawiki"`
- **THEN** `apiArgs` SHALL 包含 `["--phase", "fetch"]`

### Requirement: gitignore-update

`.gitignore` SHALL 排除 `.cache/` 目录。

#### Scenario: cache-gitignored
- **WHEN** `.cache/` 目录存在
- **THEN** `git status` SHALL NOT 显示 `.cache/` 下任何文件

### Requirement: run-phase-fetch

The system SHALL 提供 `run_phase_fetch()` 函数，执行独立的 fetch 流程：遍历 manifest、获取原始内容、写入缓存、支持缓存跳过，使用相同的并发和 rate limit 控制。

#### Scenario: fetch-phase-execution
- **WHEN** `run_phase_fetch()` 被调用且 manifest 包含 1769 个页面
- **THEN** SHALL 对无缓存的页面调用 API 获取内容并写入缓存，跳过已有缓存页面，不执行 Markdown 转换

### Requirement: run-phase-convert

The system SHALL 提供 `run_phase_convert()` 函数，执行独立的 convert→assembly 流程：从缓存加载、执行 HTML→Markdown 转换、写入 output_dir、自动执行 assembly。

#### Scenario: convert-phase-execution
- **WHEN** `run_phase_convert()` 被调用
- **THEN** SHALL NOT 创建 `ApiClient` 实例或发起 HTTP 请求，从缓存加载所有页面的原始内容

### Requirement: process-single-page-refactor

`process_single_page()` SHALL 重构为两个函数：
1. `fetch_single_page()`: 仅调 API 获取内容，返回 raw dict，写入缓存
2. `convert_single_page()`: 仅执行 HTML→Markdown 转换，返回结果 dict

保留 `process_single_page()` 作为兼容包装。

### Requirement: extraction-results-json-content

`extraction_results.json` 保存时 SHALL 包含每个页面的 `content`（Markdown 正文）和 `rendered_html`（原始 HTML）。

#### Scenario: extraction-results-full-content
- **WHEN** convert phase 完成
- **THEN** 每个页面条目 SHALL 包含 `status`、`error`、`content`、`rendered_html`、`images` 字段

### Requirement: pipeline-phase-choices

`--phase all` SHALL 依次执行 discover → fetch → convert。`--phase fetch` 仅执行 discover + fetch。

#### Scenario: phase-all-behavior
- **WHEN** 执行 `--phase all`
- **THEN** fetch 阶段 SHALL 跳过已有缓存的页面

### Requirement: standalone-redirect-handling

系统 SHALL 在所有 MediaWiki `action=parse` API 调用中包含 `redirects=true`。

### Requirement: explore-redirect-handling

系统 SHALL 在 `scripts/explore/main.py` 的 `_fetch_wikitext()` 中包含 `redirects=true`。

### Requirement: auto-link-fix-after-pipeline

系统 SHALL 在 Phase C 完成后（或 Phase B 后如无 Phase C）自动调用 `fix_links_in_dir()`。链接修复失败 SHALL NOT 导致 pipeline 失败。

### Requirement: phase-homepage-entry-point

系统 SHALL 支持 `--phase homepage` 作为 pipeline entry point，执行 homepage-driven discovery 后接 fetch/convert/assemble。

#### Scenario: phase-homepage-with-bc
- **WHEN** `--phase homepage,B,C` 被调用
- **THEN** homepage discovery SHALL 执行，Phase A SHALL 被跳过

### Requirement: Registry 补充 fandom_infobox

系统 SHALL 在 `_STRATEGY_REGISTRY["template_processor"]` 中注册 `"fandom_infobox": FandomInfoboxTemplateProcessor`。

### Requirement: Pipeline 启动时策略 schema hard-fail 校验

系统 SHALL 在 `run_pipeline()` 中启动阶段增加对策略文件 `content_profile` 的 schema 校验。无效 ID → `EXIT_STRATEGY_ERROR`。

### Requirement: Pipeline platform_variant 行为分支

系统 SHALL 从策略文件的 `api.platform_variant` 读取变体值并传递给下游阶段。未指定时默认为 `"standard"`。

### Requirement: Registry 暴露为可导入模块

`_STRATEGY_REGISTRY` SHALL 可被外部模块导入（如 `bootstrap-strategy`）。

### Requirement: 函数来源外部化

`orchestrator.py` SHALL 从共享库导入 `parse_strategy()`、`resolve_rate_limit_config()`、`RateLimitConfig` 等函数，而非内联定义。

### Requirement: rate_limit.py 删除

系统 SHALL 删除 `scripts/pipeline/pipeline/rate_limit.py`（函数已迁移至共享库）。

### Requirement: Pipeline platform_variant 行为分支 — Phase A Fandom 翻译页过滤

在 `run_phase_a()` 中，当 `platform_variant` 为 `"fandom"` 时，在生成 manifest 前过滤掉标题以 `_tr` 结尾的页面。

### Requirement: Pipeline platform_variant 行为分支 — Phase A 页面存在性验证

在 `run_phase_a()` 中，当 `platform_variant` 为 `"fandom"` 时，在 manifest 生成前批量验证发现的页面是否存在。

### Requirement: Pipeline platform_variant 行为分支 — Phase B PageNotFoundError 优雅处理

在 `process_single_page()` 中增加对 `PageNotFoundError` 的捕获，返回 `status: "skipped"`。failure rate 仅计算 `status: "error"` 页面。
