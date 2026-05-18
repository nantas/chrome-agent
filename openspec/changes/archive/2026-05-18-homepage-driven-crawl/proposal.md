# Proposal

## 问题定义

用户通过 chrome-agent 爬取 Binding of Isaac Rebirth Wiki (bindingofisaacrebirth.wiki.gg) 时，面临四个层面的问题：

1. **Pipeline/Converter 代码缺陷**：`standalone.py` 的 API 调用未处理 MediaWiki 重定向首页（`Main_Page` → 实际页面）；`HtmlToMarkdownConverter._to_markdown_link` 未解码 URL 百分号编码（`%27` → `'`），导致 4.6% 的内部链接匹配失败。

2. **策略 Schema 缺口**：用户按首页 UI gallery 的 18 个分类爬取，但策略只有 `taxonomy.list_pages`（28 项 wiki 内部分类体系），缺少 `category → directory` 映射和优先级规则。多分类页面（54% 页面被多个分类链接）的归属完全依赖手写脚本。

3. **管线能力断层**：现有 pipeline（Phase A 全量发现 → Phase B 提取 → Phase C 列表页组装）缺少首页驱动的入口、页面分配逻辑、断点续传和链接修复自动触发。

4. **工具调用方自行产出不稳定运行时**：用户被迫编写 ~600 行后处理脚本（分类分配、link index 构建、全量重转换、链接修复 pass、索引生成），耗时 ~100 分钟，而这些都应是 chrome-agent 管线覆盖的范围。

## 范围边界

**范围内：**
- 修复 `standalone.py` 和 `explore/main.py` 的重定向处理
- 修复 `HtmlToMarkdownConverter._to_markdown_link` 的 URL 编码解码
- 扩展策略 schema，增加 `api.homepage` 配置块（categories、assignment_priority、category_page_types）
- 新增管线 Phase 0：首页解析 → 分类发现 → 页面分配
- Pipeline 集成 `--phase homepage` 入口和 `--resume` 支持
- Pipeline 结束时自动触发 `fix_links_in_dir`
- 回填 Binding of Isaac 站点策略

**范围外：**
- 包名重构（`mediawiki-api-extract` → `mediawiki_api_extract`）— 低优先级，后续 change 处理
- 通用 wiki.gg 首页选择器泛化 — 先以 BOI 验证，泛化到模板属于后续 change
- `link_fixer.py` 的功能修改 — 已正确使用 `unquote()`，无需变更
- Phase A（allpages 全量发现）的修改 — 与 Phase 0 互补共存，不替代

## Capabilities

### New Capabilities

- `homepage-driven-discovery`: 解析 MediaWiki 首页 HTML，按配置的选择器提取分类链接列表，按页面类型（list_page / category_page）选择发现策略（prop=links / categorymembers），构建去重后的页面清单。
- `page-assignment`: 将发现的页面按优先级规则分配到输出子目录。优先级链：手动覆盖 → category_page 特殊成员 → MediaWiki 分类标签匹配（按 `assignment_priority` 排序）。输出标准 manifest JSON（与 Phase A 格式兼容）。
- `pipeline-resume`: 基于输出目录下的持久化状态文件（`.pipeline_state.json`）实现断点续传。Pipeline 启动时检查已完成的页面，Phase B 逐页跳过已完成项。支持 `--resume` 和 `--no-resume` CLI 标志。

### Modified Capabilities

- `mediawiki-api-extraction-pipeline`: 新增 Phase 0 入口点（`--phase homepage`）；`standalone.py` 和 `explore/main.py` 的 MediaWiki API 调用增加 `redirects=true`；Phase C 或 pipeline 结束时自动调用 `fix_links_in_dir`；`--resume` 集成到 orchestrate 流程。
- `pipeline-converters`: `HtmlToMarkdownConverter._to_markdown_link` 增加 `urllib.parse.unquote()` 解码步骤，使 `%27`/`%26` 等百分号编码标题可正确匹配 manifest 索引。
- `site-strategy-schema`: 策略 `api` 下新增 `homepage` 配置块，包含 `page_title`、`category_sections`（选择器列表）、`categories`（名称→目录映射）、`category_page_types`（list_page / category_page 区分）、`assignment_priority`（优先级排序列表）。

## Capabilities 待确认项

- [x] 能力清单已与用户确认：用户选择三层推进（bugfix + pipeline + 命令），对应上述 3 new + 3 modified capabilities。

## Impact

- **代码变更**: 3 个 bugfix（Phase 0），3 个新建模块（`pipeline/phase_0.py`、`pipeline/homepage_parser.py`、`pipeline/page_assigner.py`），3 个文件修改（`orchestrate.py`、`cli.py`、`html_to_markdown.py`），1 个策略文件更新
- **向后兼容**: 所有现有 CLI 命令和策略文件保持兼容。`api.homepage` 为可选配置块，无此块的策略不受影响。`--phase homepage` 是新选项，默认仍为 `all`（Phase A+B+C）
- **策略迁移**: 已有策略文件无需更新；希望使用首页驱动爬取的站点需添加 `api.homepage` 配置
- **破坏性变更**: 无

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`openspec/specs/mediawiki-api-extraction-pipeline/spec.md`、`openspec/specs/pipeline-strategy-schema/spec.md`、`openspec/specs/pipeline-converters/spec.md`
  - 项目页：`/Users/nantasmac/projects/my-wiki/docs/workflow-experience/binding-of-isaac-wiki-crawl.md`
  - 回写目标：上述项目页 + `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
