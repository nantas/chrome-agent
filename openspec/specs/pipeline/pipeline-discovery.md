# Pipeline Domain: Discovery — Merged Spec

## Source Attribution

| Source Spec | Type |
|------------|------|
| `homepage-driven-discovery` | frozen |
| `pipeline-discovery-summary` | frozen |
| `incremental-reprocess` | frozen |

Paths have been updated to reflect the current directory structure.

---

# Pipeline Discovery Specification

## Purpose

Defines homepage-driven page discovery, discovery summary generation, allpages discovery, category exclusion filtering, page assignment to output directories, and incremental reprocessing for failed pages.

---

## Requirements

### Requirement: homepage-html-parsing

系统 SHALL 通过 MediaWiki `action=parse` API 解析策略配置 `api.homepage.page_title` 指定的首页 HTML，提取分类链接。首页 fetch SHALL 使用 `redirects=true` 处理重定向。

#### Scenario: homepage-fetch-with-redirect
- **WHEN** `api.homepage.page_title` 为 `"Main_Page"` 且页面为重定向
- **THEN** API 调用 SHALL 包含 `redirects=true`，返回解析后页面的 HTML

#### Scenario: homepage-fetch-direct
- **WHEN** `api.homepage.page_title` 为实际页面标题（非重定向）
- **THEN** API 调用 SHALL 成功

### Requirement: category-link-extraction

系统 SHALL 使用 `api.homepage.category_sections` 定义的 CSS 选择器从首页 HTML 提取分类链接。每个条目包含 `selector` 字段，可选 `type` 字段（`list_page` 或 `category_page`，默认 `list_page`）。

#### Scenario: extract-gallery-links
- **WHEN** `category_sections` 包含 `{selector: ".gallerytext a"}` 且首页有 gallery 链接的分类
- **THEN** SHALL 提取匹配选择器的所有 `<a>` 元素，解析为页面标题和分类名称

### Requirement: category-discovery-strategy-selection

系统 SHALL 根据分类页面类型选择发现策略：
- `list_page` (ns=0): 使用 `action=parse&prop=links`
- `category_page` (ns=14): 使用 `action=query&list=categorymembers`

#### Scenario: list-page-discovery
- **WHEN** 分类的 `type` 为 `list_page`
- **THEN** SHALL 使用 `action=parse&page=<title>&prop=links` 发现子页面

#### Scenario: category-page-discovery
- **WHEN** 分类的 `type` 为 `category_page`
- **THEN** SHALL 使用 `action=query&list=categorymembers` 发现成员页面

#### Scenario: discovery-deduplication
- **WHEN** 同一页面从多个分类被发现
- **THEN** 页面仅出现一次，发现来源分类被保留

### Requirement: manifest-output-compatibility

首页驱动发现的输出 SHALL 是与 allpages discovery 输出格式结构兼容的 manifest JSON，包含 `pages` 数组（含 `title`、`target_directory`、`target_filename`、`source_categories`、`mw_categories`）。

#### Scenario: manifest-compatible-with-downstream
- **WHEN** discovery 完成
- **THEN** 输出 manifest 可写入 `page_manifest.json`，下游 phase 可无修改消费

### Requirement: category-exclusion-filtering

系统 SHALL 在 `run_phase_0()` 中，`parse_homepage()` 完成后、`_discover_category_pages()` 调用前，按 `api.homepage.exclude_categories` 列表过滤分类。排除按 `categories[].name` 字段名称匹配（大小写敏感）。

#### Scenario: exclude-three-categories
- **WHEN** `api.homepage.exclude_categories` 为 `["Music", "Modding", "Version History"]`
- **AND** `parse_homepage()` 返回 19 个分类（含这三个）
- **THEN** SHALL 过滤掉这三个分类，仅 16 个进入后续遍历

#### Scenario: no-exclusion-configured
- **WHEN** `api.homepage.exclude_categories` 未定义或为空列表
- **THEN** 不过滤任何分类

#### Scenario: exclude-category-not-found
- **WHEN** `exclude_categories` 包含 `"NonExistent"` 但无匹配分类
- **THEN** SHALL 记录 info 日志，不阻断流程

### Requirement: excluded-categories-absent-from-manifest

被排除的分类 SHALL 不在最终 manifest 的任何位置出现（不在 `source_categories`、`assigned_category`、`categories_discovered` 计数中）。

#### Scenario: manifest-excludes-filtered-categories
- **WHEN** Music 分类被排除
- **THEN** manifest 中所有 page 的 `source_categories` 和 `assigned_category` SHALL 不包含 `"Music"`

### Requirement: exclude-categories-merge-with-cli

discovery phase SHALL 在运行时合并策略文件的 `api.homepage.exclude_categories` 和 CLI 的 `--exclude-category` 参数，取并集。合并逻辑由 `orchestrator.py` 的 `run_pipeline()` 负责。

#### Scenario: merge-strategy-and-cli-excludes
- **WHEN** 策略 `exclude_categories` 为 `["Music", "Modding"]` 且 CLI 传入 `--exclude-category "Version History" --exclude-category "Music"`
- **THEN** 最终排除列表 SHALL 为 `{"Music", "Modding", "Version History"}`（并集去重）

### Requirement: priority-chain-assignment

系统 SHALL 按优先级链将发现的页面分配到输出目录：
1. 手动覆盖（`api.homepage.manual_assignments`）
2. Category page 特殊成员
3. MediaWiki 分类标签匹配（按 `api.homepage.assignment_priority` 顺序）

#### Scenario: manual-override-takes-precedence
- **WHEN** `manual_assignments` 指定 `{"Seeds": "seeds"}`
- **THEN** 页面 SHALL 分配到 `"seeds"` 目录

#### Scenario: mw-category-tag-matching
- **WHEN** 页面有 MW 分类标签 `["Bosses", "Basement bosses"]` 且 `assignment_priority` 列 `Bosses` 在前
- **THEN** 页面 SHALL 分配到 `"bosses"` 目录

#### Scenario: no-matching-category
- **WHEN** 页面无匹配的 MW 分类标签
- **THEN** 分配到 `"misc"` 目录并记录 warning

### Requirement: mw-category-batch-lookup

系统 SHALL 通过 `action=query&prop=categories` 批量查询 MW 分类标签（每批 50 个 title），尊重 rate limit 配置。

### Requirement: assignment-priority-ordering

`api.homepage.assignment_priority` SHALL 为有序列表，较早条目优先级更高。

### Requirement: manifest-enrichment

分配完成后，每个 manifest 页面条目 SHALL 包含 `assigned_category`、`mw_categories`、`assignment_method`（`manual`/`category_page_member`/`mw_category_match`/`default`）。

### Requirement: excluded-categories-not-in-input

`assign_pages()` SHALL 不接收已被排除分类的页面数据。排除在 discovery phase 源头完成。

#### Scenario: assigner-receives-filtered-input
- **WHEN** discovery 排除了 Music、Modding、Version History
- **THEN** `assign_pages()` 接收的参数 SHALL 不包含这些分类的页面

### Requirement: discovery-summary-module

系统 SHALL 将 `build_discovery_summary()` 及其 5 个辅助函数从 `orchestrate.py` 提取到独立模块 `pipeline/discovery_summary.py`。

#### Scenario: module-contents
- **WHEN** `pipeline/discovery_summary.py` 被创建
- **THEN** 文件包含 `build_discovery_summary()` 主函数和全部 5 个辅助函数

### Requirement: discovery-summary-imports

模块 SHALL 不依赖 `orchestrator.py` 中的任何符号。

#### Scenario: no-orchestrator-dependency
- **WHEN** `discovery_summary.py` 的 import 被审查
- **THEN** 不存在对 `orchestrator.py` 或 `orchestrate.py` 的 import

### Requirement: unit-test-compatibility

`scripts/pipeline/tests/test_discovery_summary.py` 中的现有单元测试在模块移动后 SHALL 仍然通过。

#### Scenario: existing-tests-pass
- **WHEN** 执行 `python3 scripts/pipeline/tests/test_discovery_summary.py`
- **THEN** 所有测试用例通过

### Requirement: reprocess-specified-pages

系统 SHALL 提供 `reprocess_pages()` 函数，支持对指定页面列表重新执行内容获取与转换，跳过 discovery。

#### Scenario: reprocess-failed-pages
- **WHEN** 调用 `reprocess_pages` 传入失败页面标题列表和已有 manifest 路径
- **THEN** 系统 SHALL 从 manifest 加载页面元数据，对每个指定页面执行 fetch + convert

#### Scenario: reprocess-without-manifest
- **WHEN** `manifest_path=None`
- **THEN** SHALL 使用 `title_to_filepath` 计算目标路径

### Requirement: reprocess-preserves-successful

增量补救时 SHALL 跳过不在指定列表中的页面，不覆盖已有成功文件。

### Requirement: cli-reprocess-subcommand

CLI SHALL 提供 `reprocess` 子命令。

#### Scenario: cli-reprocess-pages
- **WHEN** 执行 `python3 -m scripts.pipeline reprocess <url> --pages "A,B,C" --manifest <path> --output <dir>`
- **THEN** SHALL 执行增量补救，退出码 0 表示全部成功
