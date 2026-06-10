# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认六个 capability spec 文件已创建且无占位符（`cdp-page-cache`, `html-to-markdown-converter`, `markdown-link-resolver`, `cdp-image-downloader`, `explore-scaffold`）
- [x] 1.2 确认 `explore-scaffold` 的代码修复已在本 change 中提交（`strategy_scaffold_generator.py` 首行检测逻辑）
- [x] 1.3 确认 `cache.py` 无需修改——CDP 缓存直接复用现有接口

## 2. 核心实现任务

### 2.1 CDP 页面缓存 (`cdp-page-cache`)

- [x] 2.1.1 新增 `scripts/pipeline/pipeline/phases/fetch_cdp.py`
  - 输入：manifest（页面 URL 列表 + CDP tab ID）、domain、repo_root
  - 逻辑：对每个页面 `is_cached("chrome-cdp", domain, safe_path)` → 命中跳过 / 未命中 CDP `nav` + `eval` 提取 HTML → `save_page_cache()`
  - 返回：stats dict（total, fetched, skipped, failed）
  - 验证：运行 fetch 两次，第二次所有页面应显示 `skipped`

### 2.2 HTML→Markdown 转换器 (`html-to-markdown-converter`)

- [x] 2.2.1 从 `/tmp/nintendo-rebuild/rebuild_md_v2.py` 提取 `html2md()` 函数，迁移到 `scripts/lib/extraction/html_to_markdown.py`
  - 包含：`_convert_all_tables()`（嵌套深度计数）、`convert_table()`（rowspan/colspan 传播）、图片捕获/恢复、导航表格剥离
- [x] 2.2.2 新增 `scripts/pipeline/pipeline/phases/convert_html.py`
  - 逻辑：从 `.cache/` 读取 HTML → 调用 `html_to_markdown()` → 写入 `.md`
  - 条件触发：仅当 HTML 含 `<table>` 时执行表格转换（`<table` 字符串检测）
- [x] 2.2.3 验证：用 Nintendo 缓存的 HTML 文件回归测试——输出应与 `rebuild_md_v2.py` 产出一致

### 2.3 链接修复 (`markdown-link-resolver`)

- [x] 2.3.1 从 `/tmp/nintendo-rebuild/fix_links.py` 和 `rebuild_md_v2.py` 提取链接修复逻辑，迁移到 `scripts/lib/markdown_link_resolver.py`
  - 包含：`build_page_mapping()`、`resolve_link()`、`fix_all_links()`
  - 独立函数，不依赖全局状态
- [x] 2.3.2 验证：给定含 `../Pages/Page_xxx.html` 和 `../title.html` 链接的 MD 文件 + 页面映射，输出链接应正确解析为 `.md` 或完整 URL

### 2.4 图片下载 (`cdp-image-downloader`)

- [x] 2.4.1 从 `/tmp/nintendo-rebuild/download_images.py` 提取核心逻辑，迁移到 `scripts/lib/cdp_image_downloader.py`
  - 包含：`collect_image_urls()`（从 MD 提取唯一 URL）、`fetch_image_as_base64()`（CDP async fetch）、去重、跳过已存在文件
  - CDP 命令调用接口化：接受 `cdp_eval_async(url, js_code)` 回调参数，不硬编码 tab ID
- [x] 2.4.2 验证：用 Nintendo 图片 URL 列表运行下载，验证所有图片写入 `images/` 且 MD 引用已更新为相对路径

### 2.5 策略文件保护 (`explore-scaffold`)

- [x] 2.5.1 确认 `scripts/explore/strategy_scaffold_generator.py` 的 overwrite guard 修复已生效
  - 验证：对已手动编辑的策略文件运行 explore，确认返回 `skipped: true` 且文件未被修改
  - 验证：对 auto-generated 策略文件运行 explore，确认正常覆盖

### 2.6 文档回写

- [x] 2.6.1 更新 `docs/architecture/02-pipeline-flow.md`：管线图中增加 chrome-cdp fetch 路径，Cache 章节补充 `platform: "chrome-cdp"` 说明
- [x] 2.6.2 更新 `docs/architecture/07-explore-workflow.md`：Step 6 scaffold 生成章节增加 overwrite guard 行为说明
- [x] 2.6.3 确认 `AGENTS.md` §0.5 无需更新（新增代码均为 Python 3.9+ 兼容 .py 文件，无新约束）

## 3. 收敛与验证准备

- [x] 3.1 运行 `chrome-agent doctor --format json` 确认环境正常
- [x] 3.2 用 Nintendo 已有 HTML 缓存（`/tmp/nintendo-final-html/`）作为测试输入，验证全链路：fetch_cdp → convert_html → markdown_link_resolver → cdp_image_downloader
- [x] 3.3 验证 `.cache/chrome-cdp/` 目录结构符合 spec 约定
- [x] 3.4 验证 explore 对已有策略文件的保护行为

## 4. 验证与回写收敛

- [x] 4.1 基于验证结果生成 `verification.md`
- [x] 4.2 基于 verification 结论生成 `writeback.md`
- [x] 4.3 执行文档回写（见 2.6），记录回写证据
