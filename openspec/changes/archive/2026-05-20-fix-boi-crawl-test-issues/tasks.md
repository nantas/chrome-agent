# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 4 个 capability spec 的实现范围与边界
  - `homepage-driven-discovery`: list page 目录分配 + exclude 标题匹配增强
  - `mediawiki-api-extraction-pipeline`: assembly 孤儿 index 跳过 + 防覆盖保护
  - `pipeline-converters`: 括号文件名 URL-encode + YouTube 残留清理 + frontmatter 图片过滤
  - `pipeline-registry`: taxonomy.list_pages 与 manifest 对齐检测
- [x] 1.2 确认依赖前置条件
  - 基线测试 `tests/e2e/boi-100-baseline.sh` 已就绪
  - 缓存已有 98 个页面可用（无需重复 fetch）
  - 基线 validation 已保存为 `tests/fixtures/boi-crawl-100-validation-baseline.json`

## 2. 核心实现任务

### 2.1 `homepage-driven-discovery` — List page 目录分配修复

- [x] 2.1.1 修复 `_build_homepage_manifest()` 中 list page 目录分配
  - 文件: `scripts/pipeline/pipeline/phases/discovery_homepage.py`
  - 在 `_build_homepage_manifest()` 中构建 `category_dir_map = {cat["name"]: cat.get("dir", "") for cat in parsed_categories}`
  - 为每个 list page 条目使用 `category_dir_map[cat_name]` 而非 `cat.get("dir")`
  - 验证: 测试 manifest 中 `Bosses` → `target_directory: "bosses"`、`Characters` → `target_directory: "characters"`

### 2.2 `homepage-driven-discovery` — Exclude 过滤标题匹配增强

- [x] 2.2.1 增强 orchestrator 的 exclude_categories 过滤逻辑
  - 文件: `scripts/pipeline/pipeline/orchestrator.py`
  - 在 manifest 过滤段增加 `p["title"] in exclude_set` 检查
  - 与现有 `source_categories`+`assigned_category` 检查形成 OR 关系
  - 验证: Version History 页面在 manifest 中被排除（即使其 `assigned_category` 为 "Items"）

### 2.3 `mediawiki-api-extraction-pipeline` — Assembly 孤儿 index 修复

- [x] 2.3.1 Assembly 跳过 manifest 中不存在的 list_page
  - 文件: `scripts/pipeline/pipeline/phases/assemble.py`
  - 在 `run_assemble()` 的 list_page 循环开始处，检查 `manifest["pages"]` 中是否存在该 `page_title` 且 `is_list_page: true`
  - 不存在则跳过，日志输出 `"Skipping list page '<title>': not found in manifest"`
  - 验证: Mechanics、Cards 等不在 manifest 中的条目不生成 `Mechanics/index.md`、`Cards/index.md`

### 2.4 `mediawiki-api-extraction-pipeline` — Assembly 防覆盖保护

- [x] 2.4.1 Assembly 只处理 `is_list_page` 页面的 index 生成
  - 文件: `scripts/pipeline/pipeline/phases/assemble.py`
  - 在 list_page 循环中，通过 `results.get(page_title)` 获取 content 前，先验证 manifest 中该页面有 `is_list_page: true`
  - 如果该 `page_title` 在 manifest 中 but 没有 `is_list_page` 标记，跳过
  - 验证: Version History 不覆盖 `items/index.md`，Items 内容保留

### 2.5 `pipeline-converters` — 括号文件名 URL-encode

- [x] 2.5.1 `_to_markdown_link()` 中对括号编码
  - 文件: `scripts/lib/extraction/converter.py`
  - 在生成 Markdown 链接时，对文件名中的 `(` → `%28`、`)` → `%29`
  - 不重复编码已包含 `%28`/`%29` 的链接
  - 验证: 链接 `[text](V1.06.0192_%28Re-release%29.md)` 正确生成

- [x] 2.5.2 `fix_links_in_dir()` 中对已存在的未编码括号修复
  - 文件: `scripts/pipeline/converters/link_fixer.py`
  - 在 `_fix_links_in_content()` 中增加模式匹配，将未编码的 `(`/`)` 在 markdown 链接 URL 部分替换为 `%28`/`%29`
  - 验证: validation 报告中括号未闭合 broken links 从 106 降至接近 0

### 2.6 `pipeline-converters` — YouTube 残留清理

- [x] 2.6.1 `clean_html()` 中移除 YouTube fallback 文本
  - 文件: `scripts/lib/extraction/converter.py`
  - 在 `clean_html()` 中增加正则或节点匹配，移除包含 "Load video" 的父容器
  - 验证: The Sad Onion 输出中不包含 "Load video"、"YouTube might collect"、"Privacy Policy"、"Continue Dismiss"

### 2.7 `pipeline-converters` — Frontmatter 图片过滤

- [x] 2.7.1 `_process_html_page()` 中过滤 frontmatter image
  - 文件: `scripts/pipeline/pipeline/phases/convert.py`
  - 在 `_process_html_page()` 中，从 `raw.get("images", [])` 获取图片列表后，先过滤匹配 `image_filtering.skip_patterns` 的条目
  - 从过滤后的列表中取第一张作为 `frontmatter["image"]`
  - 全部被过滤时省略 `image` 字段
  - 验证: The Sad Onion 的 frontmatter image 为 `Collectible_The_Sad_Onion_icon.png` 而非 `Font_TeamMeat_T.png`

### 2.8 `pipeline-registry` — Manifest 对齐检测

- [x] 2.8.1 提供 manifest 与 taxonomy.list_pages 的间隙检测
  - 文件: `scripts/pipeline/pipeline/registry.py`（新增方法）或 `scripts/pipeline/pipeline/phases/assemble.py`（内联检查）
  - 选择: 内联在 assemble.py 中检查（最简单，无需新增 registry 方法）
  - 验证: discovery summary 或 assemble log 中报告哪些 list_page 条目在 manifest 中缺失

## 3. 收敛与验证准备

- [x] 3.1 运行 `tests/e2e/boi-100-baseline.sh` 验证全部修复
  - 检查点:
    - broken links ≤ 20（剩余的应为真正的断链，非括号文件名引起）
    - orphan index 目录（Mechanics、Cards 等）不存在
    - `items/index.md` 内容为 Items 页面
    - The Sad Onion 的 frontmatter image 正确
    - The Sad Onion 输出中无 "Load video" 残留
    - Version History 不在 manifest 中

- [x] 3.2 标记需要进入 writeback 的摘要与状态变更
  - Known Issues 表中更新 P0-P5 状态
  - handoff 文档 Issue 状态更新

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成 verification.md
- [x] 4.2 基于 verification.md 结论生成 writeback.md
- [x] 4.3 执行 writeback
