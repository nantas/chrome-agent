# Design

## Context

100 页端到端测试（`tests/e2e/boi-100-baseline.sh`）在 `fix-pipeline-quality-gaps` change 的修复基础上，发现了 6 个遗留问题。这些问题的根因分布在 4 个管线阶段中：

```
Discovery (_build_homepage_manifest)
  ├─ P0: list page 全部分配到 items/ 目录
  └─ P1(partial): exclude 过滤只查 source_categories，漏掉标题匹配

Assembly (run_assemble)
  ├─ P1(main): taxonomy.list_pages 为排除/不存在的页面写入 index
  └─ P2: 为 manifest 中不存在的 list_page 生成孤儿 index

Conversion (HtmlToMarkdownConverter)
  ├─ P3: 括号文件名未 URL-encode
  ├─ P4: YouTube 残留文本未清理
  └─ P5: frontmatter image 未应用 skip_patterns
```

## Goals / Non-Goals

**Goals:**
- 修复 4 个能力的所有 spec-defined 缺陷
- 使 `tests/e2e/boi-100-baseline.sh` 的 broken links 从 123 降至 ≤20（剩余为真正的断链）
- 使 orphan index 从 4 个降至 0
- 使 items/index.md 内容正确反映 Items 页面
- 使 frontmatter image 不包含装饰性图片

**Non-Goals:**
- 不重写 `/opsx-propose` 的整体架构
- 不修改 page_assigner 的分类算法
- 不处理 Unavailable images（wiki 服务端资源问题）
- 不修改 sample_converter.py（explore 路径）

## Decisions

### D1: `_build_homepage_manifest` 目录映射修复

**方案**：在 `_build_homepage_manifest()` 中，通过 `parse_homepage()` 返回的 category dict 的 `dir` 字段直接分配目录。

当前的 `parse_homepage()` 返回 categories 列表时，每个 category 的 `dir` 字段来源于策略配置中的 `api.homepage.categories[n].dir`。如果 `dir` 字段在返回时丢失或被覆盖，则改为在 `_build_homepage_manifest()` 中通过维护一个 `category_name → dir` 查找表来决定目录。

**选择**：显式构建 `category_dir_map = {cat["name"]: cat.get("dir", "") for cat in strategy_categories}`，在 `_build_homepage_manifest()` 中通过 `cat_name` 查表。

### D2: Exclude 过滤增强

**方案**：在 orchestrator 的 `merged_excludes` 过滤逻辑中，增加一条 `p["title"] in exclude_set` 检查，与现有的 `source_categories`+`assigned_category` 检查形成 OR 关系。

**位置**：`orchestrator.py` 中 manifest 过滤段。

### D3: Assembly orphan index 保护

**方案**：在 `run_assemble()` 的 list_page 循环中：

1. 先检查 `manifest["pages"]` 中是否存在该 `page_title` 且为 `is_list_page: true`
2. 不存在则跳过（log warning）
3. 存在但 `results[page_title]` 为空或 status 不是 ok，则跳过（log warning）
4. 对于防范覆盖：检查 results 中要写入目标 dir 的是否是 `is_list_page` 页面——如果不是，跳过

**额外保护**：只在 entity pages write step 之后执行 index.md 生成，且只写一次（不接收被非 list_page 覆盖）。

### D4: 括号文件名 URL-encode

**方案**：在 `HtmlToMarkdownConverter._to_markdown_link()` 中，对 `title` 转为文件路径后进行 `%28`/`%29` 替换。

在 `link_fixer._fix_links_in_content()` 中，对已存在的 Markdown 链接中的未编码括号也做同样替换。

**注意**：不需要对整个 URL 做全面 `urllib.parse.quote()`——只需替换 `(` 和 `)`。

### D5: YouTube 残留清理

**方案**：在 `HtmlToMarkdownConverter.clean_html()` 中，添加针对 YouTube fallback 容器的移除逻辑。wiki.gg 的 YouTube embed 会产生类似 `<div>Load video</div><div>YouTube...</div>` 的文本节点。使用 selectolax CSS 选择器或正则匹配包含 "Load video" 的父容器并 decompose。

### D6: Frontmatter 图片过滤

**方案**：在 `_process_html_page()` 中，从 `raw.get("images", [])` 获取列表后，先过滤掉匹配 `skip_patterns` 的图片，再从过滤后的列表中取第一张。如果全部被过滤掉，则不设 `image` 字段。

## Risks / Migration

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| URL-encode 括号导致已存在的正确链接被双编码 | 低 | 链接断裂 | 修复前检查链接是否已包含 `%28`，避免重复编码 |
| list_page 存在性检查过严 | 低 | 部分正确的 list_page 被跳过 | 使用 `manifest["pages"]` 中有 `is_list_page=true` 的为通过条件 |
| exclude 按标题匹配过宽 | 低 | 误排除不应排除的页面 | 仅当标题完全匹配 exclude 列表中的条目时才排除 |
| 无迁移影响 | - | - | 所有修复向后兼容，不涉及格式迁移或数据迁移 |
