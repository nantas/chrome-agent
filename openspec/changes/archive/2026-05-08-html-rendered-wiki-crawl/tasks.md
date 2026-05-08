# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 `html-rendered-acquisition` spec 的实现范围：新增 `HtmlRenderedAcquisitionStrategy` 类，实现 `ContentAcquisitionStrategy` 协议
- [x] 1.2 确认 `semantic-directory-mapping` spec 的实现范围：新增 `title_to_filepath()` 函数，覆盖 ns=0/3000/14
- [x] 1.3 确认 `category-page-generator` spec 的实现范围：新增 `CategoryPageAssembler` 类，在 Phase C 中处理 ns=14 页面
- [x] 1.4 确认 `html-to-markdown-converter` spec 的实现范围：新增 `HtmlToMarkdownConverter` 类，融合 wiki.gg 清洗和转换逻辑
- [x] 1.5 确认 `mediawiki-api-extraction-pipeline` spec 的实现范围：扩展 `_STRATEGY_REGISTRY`、Phase B 分支逻辑、discovery namespace 扩展
- [x] 1.6 确认 `site-strategy-slaythespire` spec 的实现范围：更新策略文件 frontmatter 和 taxonomy

## 2. 核心实现任务

### Phase A 扩展（Discovery）

- [x] 2.1 扩展 `CategoryMembersDiscoveryStrategy.discover_pages()` 支持多 namespace 遍历
  - **Spec 引用**: `mediawiki-api-extraction-pipeline` / "discover-all-namespaces"
  - **实现路径**: 遍历 `api.namespaces` 列表，对每个 ns 调用 `categorymembers`
  - **验证方式**: 运行 `python -m mediawiki-api-extract` 对 slaythespire 策略，确认 manifest 包含 ns=0、ns=3000、ns=14 的页面

- [x] 2.2 扩展 `AllPagesDiscoveryStrategy.discover_pages()` 支持多 namespace 遍历
  - **Spec 引用**: `mediawiki-api-extraction-pipeline` / "discover-all-namespaces"
  - **实现路径**: 遍历 `api.namespaces`，对每个 ns 调用 `allpages`
  - **验证方式**: 同上

- [x] 2.3 实现 `title_to_filepath()` 语义化目录映射函数
  - **Spec 引用**: `semantic-directory-mapping` / "namespace-based-directory-mapping"
  - **实现路径**: 基于 ns 和 title 计算 (target_directory, target_filename)
  - **验证方式**: 单元测试覆盖所有 scenario（ns=0 实体页、ns=3000 实体页、ns=3000 列表页、ns=14 分类页）

- [x] 2.4 在 Phase A manifest 构建中集成目录映射
  - **Spec 引用**: `mediawiki-api-extraction-pipeline` / "generate-manifest-with-paths"
  - **实现路径**: `phase_a.py` 中调用 `title_to_filepath()` 填充 `target_directory` 和 `target_filename`
  - **验证方式**: 检查生成的 `page_manifest.json` 中分类页路径为 `Category_Name/index.md`

### Phase B 扩展（Content Extraction）

- [x] 2.5 实现 `HtmlRenderedAcquisitionStrategy`
  - **Spec 引用**: `html-rendered-acquisition` / "api-parse-html-fetch"
  - **实现路径**: `client.parse(page=title, prop="text")`，返回 `{"html": ..., "wikitext": None}`
  - **验证方式**: 单元测试 mock API 响应，确认返回 HTML 正确

- [x] 2.6 在 `_STRATEGY_REGISTRY` 中注册 `"html_rendered"`
  - **Spec 引用**: `mediawiki-api-extraction-pipeline` / "strategy-registry-extension"
  - **实现路径**: `pipeline.py` 的 `_STRATEGY_REGISTRY["content_acquisition"]["html_rendered"]`
  - **验证方式**: 运行管线，策略为 `html_rendered` 时不 fallback 到默认策略

- [x] 2.7 实现 `HtmlToMarkdownConverter` 清洗逻辑
  - **Spec 引用**: `html-to-markdown-converter` / "html-cleaning-rules"
  - **实现路径**: 基于 wiki.gg `clean/html.py`，新增 `display:none` 过滤
  - **验证方式**: 单元测试输入含 `.mw-editsection`、`.toc`、`.hatnote`、`display:none` 的 HTML，确认输出不含这些元素

- [x] 2.8 实现 `HtmlToMarkdownConverter` 转换逻辑
  - **Spec 引用**: `html-to-markdown-converter` / "block-element-rendering", "inline-element-rendering"
  - **实现路径**: 基于 wiki.gg `convert/markdown.py`，适配标准 Markdown 输出
  - **验证方式**: 单元测试覆盖 heading、list、table、blockquote、image、link、bold/italic/code

- [x] 2.9 扩展链接解析器为标准 Markdown 相对链接
  - **Spec 引用**: `html-to-markdown-converter` / "internal-link-conversion"
  - **实现路径**: 扩展 `ShortNameLinkResolver`，输出 `[text](relative/path.md)`，使用 `os.path.relpath()`
  - **验证方式**: 单元测试验证跨目录链接（StS2→StS1、同级、子目录）的相对路径正确

- [x] 2.10 扩展 `process_single_page` 支持 HTML 路径分支
  - **Spec 引用**: `mediawiki-api-extraction-pipeline` / "process-html-rendered-page"
  - **实现路径**: 根据 `content_strategy` 类型选择 wikitext 或 HTML 处理流程
  - **验证方式**: 集成测试运行管线 Phase B，确认 HTML 路径输出 Markdown

### Phase C 扩展（Assembly）

- [x] 2.11 实现 `CategoryPageAssembler`
  - **Spec 引用**: `category-page-generator` / "category-index-assembly"
  - **实现路径**: Phase C 中识别 ns=14 页面，组合 parse 描述和 categorymembers 列表
  - **验证方式**: 运行完整管线，确认输出目录下存在 `Category_Name/index.md`，包含描述和成员链接

### 站点策略更新

- [x] 2.12 更新 `slaythespire.wiki.gg/strategy.md`
  - **Spec 引用**: `site-strategy-slaythespire`
  - **实现路径**: 更新 `content_acquisition` 为 `html_rendered`，`namespaces` 为 `[0, 3000, 14]`，更新 taxonomy 和 output 配置
  - **验证方式**: 运行 `chrome-agent crawl` 对更新后的策略，确认管线正确解析配置

- [x] 2.13 更新 `sites/strategies/registry.json`
  - **Spec 引用**: `site-strategy-slaythespire`
  - **实现路径**: 追加/更新 slaythespire.wiki.gg 条目的能力描述
  - **验证方式**: registry.json 格式正确，与 strategy.md frontmatter 一致

## 3. 收敛与验证准备

- [x] 3.1 准备抽样验证页面清单
  - StS2 实体页：`Slay the Spire 2:Bash`（验证 infobox、图片、内链）
  - StS2 列表页：`Slay the Spire 2:Cards_List`（验证 card-box 网格、base 图片过滤）
  - StS1 实体页：`Bash`（验证 ns=0 内容完整性）
  - 分类页：`Category:Cards`（验证 index.md 描述和成员列表）
  - 跨命名空间链接页：含 StS2→StS1 链接的页面（验证相对路径）

- [x] 3.2 定义验证检查清单
  - [ ] 每个抽样页面都有对应的 Markdown 文件
  - [ ] Markdown 中包含图片（`![alt](url)`）
  - [ ] 内链为标准 Markdown 格式（`[text](path.md)`）
  - [ ] 分类页有 `index.md` 且包含成员列表
  - [ ] 列表页无 upgraded/beta 隐藏图片
  - [ ] 无空内容文件（仅 frontmatter）
  - [ ] 无断链（相对路径指向存在的文件）

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 `verification.md`
  - 覆盖 spec-to-implementation 映射
  - 记录 task-to-evidence（测试输出、抽样文件内容）

- [x] 4.2 基于 `verification.md` 结论生成或更新 `writeback.md`
  - 目标：`sites/strategies/slaythespire.wiki.gg/strategy.md`
  - 字段映射：更新 frontmatter 中的策略配置
  - 前置条件：所有核心 task 完成且验证通过

- [x] 4.3 执行 writeback
  - 更新策略文件
  - 更新 registry.json
  - 记录审计证据（提交哈希、时间、执行人）
