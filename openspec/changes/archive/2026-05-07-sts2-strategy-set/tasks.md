# Tasks

## 1. 基线建立与回归准备

- [x] 1.1 运行当前脚本生成 balatro 基线
      ```bash
      python -m scripts.mediawiki-api-extract https://balatrowiki.org/w/Jokers \
        --strategy sites/strategies/balatrowiki.org/strategy.md \
        --output /tmp/mw-baseline-sts2
      ```
      **验证**：输出 ~468 页面，17 目录，与 Change 1 归档基线一致
      **spec 覆盖**：Pipeline 默认策略组合 (spec:mediawiki-api-extraction)

- [x] 1.2 生成 StS2 当前默认策略基线（用于对比改善效果）
      ```bash
      python -m scripts.mediawiki-api-extract https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Main \
        --strategy sites/strategies/slaythespire.wiki.gg/strategy.md \
        --output ./outputs/slaythespire-wiki-baseline
      ```
      **验证**：记录当前断裂链接数、模板残留数、空内容页数作为改善基准

## 2. CategoryMembersDiscoveryStrategy 实现

- [x] 2.1 在 `strategies.py` 中实现 `CategoryMembersDiscoveryStrategy` 类
      - 方法：`discover_pages()` 使用 `action=query&list=categorymembers&cmtitle=Category:...&cmnamespace={ns}`
      - 遍历 `strategy.api.taxonomy.page_categories` 中的每个分类进行发现
      - `required_capabilities = {"page_list", "category_lookup"}`
      - **spec 覆盖**：策略实现注册表扩展 — `category_members` (spec:mediawiki-api-extraction)

- [x] 2.2 支持跨 namespace 发现
      - `discover_pages()` 接收 `namespaces` 列表（如 `[0, 3000]`）
      - 对每个 namespace 独立调用 categorymembers
      - 返回的 page dict 包含 `namespace` 字段
      - **spec 覆盖**：跨 namespace 发现与输出 (spec:mediawiki-api-extraction)

- [x] 2.3 更新 `classify_page()` 支持跨 namespace 目录映射
      - ns=3000 页面映射到 `StS2/{category}/`
      - ns=0 页面映射到 `StS1/{category}/`
      - **spec 覆盖**：Dual namespace discovery scenario (spec:mediawiki-api-extraction)

- [x] 2.4 更新 `phase_a.py` 的 `run_phase_a()` 传递 namespace 信息
      - manifest 结构增加 `namespaces` 字段
      - **spec 覆盖**：Phase A manifest 作为 phase 间数据桥梁 (spec:mediawiki-api-extraction)

## 3. HybridAcquisitionStrategy 实现

- [x] 3.1 在 `strategies.py` 中实现 `HybridAcquisitionStrategy` 类
      - `fetch_page_content()` 先获取 `prop=wikitext`
      - 检测 wikitext 中的 `{{#invoke:...}}`、`{{#dpl:...}}`、`{{#...:...}}`
      - 若存在动态内容指示器，补充获取 `prop=text` 和 `prop=images`
      - 返回 `{"wikitext": ..., "rendered_html": ..., "images": [...]}`
      - `required_capabilities = {"wikitext_parse", "html_parse", "imageinfo_query"}`
      - **spec 覆盖**：策略实现注册表扩展 — `hybrid_wikitext_plus_rendered` (spec:mediawiki-api-extraction)

- [x] 3.2 更新 `phase_b.py` 的 `process_single_page()` 处理多源返回
      - 当 `rendered_html` 存在时，传递给 `HybridListPageAssembler`
      - 当 `images` 存在时，提取图片 URL 注入 frontmatter
      - **spec 覆盖**：动态内容检测 (spec:mediawiki-api-extraction)

- [x] 3.3 验证 DRUID infobox 图片获取
      - 对 `Slay_the_Spire_2:Bash` 等实体页，`prop=images` 应返回 infobox 图片
      - **spec 覆盖**：DRUID infobox with Lua-generated images scenario (spec:mediawiki-api-extraction)

## 4. ShortNameLinkResolver 实现

- [x] 4.1 在 `strategies.py` 中实现 `ShortNameLinkResolver` 类
      - `__init__(domain, manifest_pages)` 中构建 `short_title_index`
      - `short_title_index` key 为 `title.split(":")[-1]`，value 为完整 title
      - 区分同 namespace 和跨 namespace 的短名解析优先级
      - **spec 覆盖**：策略实现注册表扩展 — `short_name_with_cross_namespace` (spec:mediawiki-api-extraction)

- [x] 4.2 实现平衡括号 Markdown 链接解析器
      - 替换 `ExactTitleLinkResolver` 中的贪婪正则 `\[([^\]]+)\]\(([^)]+)\)`
      - 使用栈式深度计数处理嵌套括号
      - **spec 覆盖**：ShortNameLinkResolver selected scenario (spec:mediawiki-api-extraction)

- [x] 4.3 实现 `os.path.relpath` 相对路径计算
      - `resolve()` 方法使用 `os.path.relpath(target_path, source_dir)`
      - 支持跨 namespace 路径（如 `StS2/Cards/` → `StS1/Cards/`）
      - **spec 覆盖**：Cross-namespace link resolution scenario (spec:mediawiki-api-extraction)

- [x] 4.4 验证链接解析正确性
      - `[[Bash]]` 在 `StS2/Cards/` 中应解析到同目录 `Bash.md`
      - `[[Strike (Ironclad)]]` 应正确解析含括号的短名
      - `[[Bash]]` 在 StS1 引用上下文中应解析到 `../../StS1/Cards/Bash.md`

## 5. StructuredTemplateProcessor 实现

- [x] 5.1 在 `strategies.py` 中实现 `StructuredTemplateProcessor` 类
      - `expand_templates()` 支持位置参数 `{{Name|arg1|arg2}}`
      - `expand_templates()` 支持命名参数 `{{Name|key=val}}`
      - Lua 模块调用 `{{#invoke:...}}` 记录为 "Lua module" 警告
      - **spec 覆盖**：策略实现注册表扩展 — `structured_with_lua_fallback` (spec:mediawiki-api-extraction)

- [x] 5.2 验证多参数模板展开
      - `{{Cards|rarity:Common|color:Red|Display|2}}` 等复杂模板按规则映射
      - **spec 覆盖**：StructuredTemplateProcessor selected scenario (spec:mediawiki-api-extraction)

## 6. HybridListPageAssembler 实现

- [x] 6.1 在 `strategies.py` 中实现 `HybridListPageAssembler` 类
      - `assemble_index()` 优先检查 `rendered_html` 是否可用
      - 若可用，从渲染 HTML 中提取实际表格结构（使用 BeautifulSoup 或正则）
      - 若不可用，fallback 到 `FrontmatterDrivenListPageAssembler` 逻辑
      - **spec 覆盖**：策略实现注册表扩展 — `hybrid_frontmatter_and_rendered` (spec:mediawiki-api-extraction)

- [x] 6.2 验证列表页内容完整性
      - `Cards_List`、`Relics_List`、`Potions_List`、`Events_List` 的 index.md 应有完整表格数据
      - **spec 覆盖**：DPL list page with dynamic table scenario (spec:mediawiki-api-extraction)

## 7. L6 验证质量层实现

- [x] 7.1 在 `pipeline.py` 或新增 `validation.py` 中实现 `validate_links()`
      - 扫描所有输出 `.md` 中的 `[text](path)`
      - 验证 `path` 是否对应实际存在的文件
      - 输出 broken links 列表到 `validation_report.json`
      - **spec 覆盖**：L6 验证质量层 — Link Integrity Scanner (spec:mediawiki-api-extraction)

- [x] 7.2 实现 `validate_content_integrity()`
      - 检测文件是否为空或仅含 frontmatter
      - 输出 empty content 列表到 `validation_report.json`
      - **spec 覆盖**：L6 验证质量层 — Content Integrity Checker (spec:mediawiki-api-extraction)

- [x] 7.3 实现 `validate_images()`
      - 提取所有 `![alt](url)`，批量查询 `action=query&prop=imageinfo&titles=File:...`
      - 每批 50 个，避免 API 过载
      - 输出 unavailable images 列表到 `validation_report.json`
      - **spec 覆盖**：L6 验证质量层 — Image Availability Validator (spec:mediawiki-api-extraction)

- [x] 7.4 集成 L6 到管线流程
      - Phase C 结束后自动运行 L6 扫描器
      - 支持 `--validate` flag 独立运行（跳过 A/B/C）
      - Soft fail：记录警告，不中断管线
      - **spec 覆盖**：Full pipeline with automatic L6 validation / Independent validation run (spec:mediawiki-api-extraction)

## 8. Pipeline 与策略组装更新

- [x] 8.1 更新 `pipeline.py` 的 `DEFAULT_STRATEGIES` 映射
      - 追加 5 个新策略 ID 到 class 映射
      - 更新 `build_pipeline()` 处理新 ID
      - **spec 覆盖**：Pipeline 策略注入 — StS2 strategy composition (spec:mediawiki-api-extraction)

- [x] 8.2 更新 `pipeline.py` 的 `run_pipeline()` 集成 L6
      - 在 Phase C 后调用 L6 扫描器
      - 处理 `--validate` CLI flag
      - **spec 覆盖**：L6 验证质量层 (spec:mediawiki-api-extraction)

## 9. 策略文件更新

- [x] 9.1 更新 `sites/strategies/slaythespire.wiki.gg/strategy.md`
      - 配置 `api.content_profile` 使用全部 5 个新策略
      - 扩展 `template_map` 覆盖高频模板（基于样本采样）
      - 更新 `api.capabilities` 包含 `html_parse` 和 `imageinfo_query`
      - **spec 覆盖**：content_profile fully specified with StS2 strategies (spec:mediawiki-site-strategy)

- [x] 9.2 可选：为 `sites/strategies/balatrowiki.org/strategy.md` 追加 `cross_namespace_discovery: false`
      - 显式声明不支持跨 namespace（文档性质，不影响行为）

## 10. 回归验证

- [x] 10.1 balatro 回归验证
      ```bash
      python -m scripts.mediawiki-api-extract https://balatrowiki.org/w/Jokers \
        --strategy sites/strategies/balatrowiki.org/strategy.md \
        --output /tmp/mw-refactored-sts2
      ```
      **验证**：`diff -r /tmp/mw-baseline-sts2 /tmp/mw-refactored-sts2 --exclude='*.json'` 零差异
      **spec 覆盖**：Default strategy composition scenario (spec:mediawiki-api-extraction)

## 11. StS2 爬取质量验收

- [x] 11.1 运行 StS2 完整爬取，输出到 `./outputs/slaythespire-wiki`
      ```bash
      python -m scripts.mediawiki-api-extract https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Main \
        --strategy sites/strategies/slaythespire.wiki.gg/strategy.md \
        --output ./outputs/slaythespire-wiki
      ```
      **说明**：该目录为本次 Change 2 的最终验证输出。若质量达标，可直接迁移到其他仓库使用。

- [x] 11.2 链接质量验收
      - 失效内部链接数 = 0
      - 括号类目标链接错误 = 0
      - 跨目录链接路径正确率 = 100%
      - **spec 覆盖**：Link integrity validation scenario (spec:mediawiki-api-extraction)

- [x] 11.3 内容完整性验收
      - 列表页（Cards/Relics/Potions/Events）主要数据完整
      - 页面非空率（排除 frontmatter 后仍有正文）= 100%
      - 模板语法残留（`{{...}}` 未展开）= 0
      - **spec 覆盖**：Content integrity validation scenario (spec:mediawiki-api-extraction)

- [x] 11.4 图片质量验收
      - 实体页主图（DRUID infobox 图片）获取率 > 95%
      - 图片链接有效性（通过 imageinfo 预检）= 100%
      - **spec 覆盖**：Image availability validation scenario (spec:mediawiki-api-extraction)

- [x] 11.5 L6 扫描器通过验收
      - `validation_report.json` 中无 broken links
      - 无 empty content 文件
      - 无 unavailable images
      - **spec 覆盖**：L6 验证质量层 (spec:mediawiki-api-extraction)

## 12. 清理与收尾

- [x] 12.1 清理临时基线目录
- [x] 12.2 验证 `--help` 输出包含 `--validate` 说明
- [x] 12.3 确认 `scripts/mediawiki-api-extract/` 无语法错误
      ```bash
      python -m py_compile scripts/mediawiki-api-extract/*.py
      ```
