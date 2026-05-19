# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认六个 capability spec 的实现边界，无遗漏
- [x] 1.2 确认 `.cache/` 已加入 `.gitignore`

## 2. 缓存层实现（`page-content-cache`）

- [x] 2.1 新建 `scripts/mediawiki-api-extract/pipeline/cache.py`
  - 实现 `get_cache_root(repo_root) -> Path`（`<repo_root>/.cache/`）
  - 实现 `get_domain_cache_dir(repo_root, platform, domain) -> Path`（`.cache/<platform>/<domain>/`）
  - 实现 `raw_to_cache_filename(title) -> str`（空格→`_`，作为 JSON 文件名）
  - 实现 `save_page_cache(repo_root, platform, domain, raw_data) -> Path`（原子写入 JSON）
  - 实现 `load_page_cache(repo_root, platform, domain, title) -> dict | None`
  - 实现 `is_cached(repo_root, platform, domain, title) -> bool`
  - 实现 `list_cached_pages(repo_root, platform, domain) -> set[str]`
  - 自动创建目录（`os.makedirs`）
  - **验证**：单元测试检查文件写入/读取/存在性判断

- [x] 2.2 确定 Scrapling 路径的缓存读写逻辑位置
  - 在 `scripts/chrome-agent-cli.mjs` 中实现 HTML 缓存读写函数
  - `saveScraplingCache(domain, slug, html, meta)`
  - `loadScraplingCache(domain, slug) -> {html, meta} | null`
  - `isScraplingCached(domain, slug) -> bool`
  - `listScraplingCached(domain) -> string[]`
  - **验证**：单元测试

## 3. Python Pipeline 重构（`mediawiki-api-extraction-pipeline`, `pipeline-fetch-phase`, `pipeline-convert-phase`）

- [x] 3.1 重构 `phase_b.py`：拆分 `process_single_page()`
  - 提取 `fetch_single_page(client, page_info, domain, content_strategy) -> raw_dict`
    - 调用 `content_strategy.fetch_page_content()`
    - 返回 raw dict（不转换）
    - **不在此函数中写缓存**（缓存写入由上层 orchestrate 控制）
  - 提取 `convert_single_page(raw, page_info, manifest_pages, domain, frontmatter_fields, template_map, link_resolver, template_processor, extraction_config) -> result_dict`
    - 从 raw dict 提取 `html`/`wikitext`/`images`
    - 调用现有转换逻辑（`HtmlToMarkdownConverter.convert_body()` / `convert_wikitext_to_markdown()`）
    - 返回 `{title, status, content, warnings, frontmatter, rendered_html}`
  - 保留 `process_single_page()` 作为包装函数（内部调用 fetch + convert）
  - **验证**：`python3 -m scripts.mediawiki-api-extract` 对已有 strategy 执行全流程，结果与重构前一致

- [x] 3.2 新增 `run_phase_fetch()` 到 `orchestrate.py`
  - 加载 manifest
  - 遍历页面：检查缓存 → 跳过或 API 获取 → 写入缓存
  - 使用 `ThreadPoolExecutor` + `RateLimitConfig`
  - 输出 fetch 摘要日志
  - **验证**：对 Isaac wiki 选取 ~10 页面执行 `--phase fetch`，检查 `.cache/` 文件生成

- [x] 3.3 新增 `run_phase_convert()` 到 `orchestrate.py`
  - 加载 manifest（需要 `--from-manifest`）
  - 遍历页面：从缓存读取 → `convert_single_page()` → 收集结果
  - 更新 `extraction_results.json`（含 `content` 和 `rendered_html`）
  - 调用 `run_phase_c()` 执行 assembly
  - 所有操作纯本地，无网络请求
  - **验证**：对已有缓存的 ~10 页面执行 `--phase convert`，生成 .md 文件

- [x] 3.4 修改 `run_pipeline()` 流控逻辑
  - 新增 `"fetch" in phases` 分支 → `run_phase_fetch()`
  - 新增 `"convert" in phases` 分支 → `run_phase_convert()`
  - `"all" in phases` 行为：discover → fetch（跳过缓存）→ convert
  - 移除 `"extract"` 分支
  - **验证**：`--phase fetch` / `--phase convert` / `--phase all` 三种路径均正确执行

- [x] 3.5 修复 `extraction_results.json` 保存逻辑
  - `run_phase_convert()` 保存 `content` 和 `rendered_html` 到 JSON
  - `run_phase_c()` 加载结果时完整重建 results dict
  - **验证**：检查 JSON 文件内容，确认含 `content` 和 `rendered_html` 字段

## 4. CLI 层变更（`pipeline-cli-entry`, `strategy-guided-crawl`）

- [x] 4.1 更新 `scripts/mediawiki-api-extract/cli.py`
  - `--phase` choices: `["all", "discover", "fetch", "convert", "assemble"]`
  - 移除 deprecated 值映射逻辑（`A→extract`, `B→extract`, `C→assemble`, `homepage→all+discovery` 的转换代码全部删除）
  - 新增 `--re-fetch` flag（`store_true`）
  - **验证**：`python3 -m scripts.mediawiki-api-extract --help` 显示新 choices

- [x] 4.2 更新 `scripts/chrome-agent-cli.mjs` 的 `runCrawl()`
  - JS CLI 将 `--phase` 参数传递给 Python pipeline（`apiArgs.push("--phase", phase)`）
  - JS CLI 将 `--re-fetch` 参数传递给 Python pipeline
  - **验证**：`chrome-agent crawl <url> --phase fetch` 启动 Python pipeline 时 `ps` 可见 `--phase fetch` 参数

- [x] 4.3 Scrapling 路径适配 `--phase fetch`
  - 在 `runCrawl()` 的 Scrapling 分支中：当 `--phase fetch` 时
    - 下载 HTML 到 `.cache/scrapling/<domain>/`（非 runDir）
    - 写入 `<slug>.meta.json`
    - 跳过 Markdown 转换
  - **验证**：`chrome-agent crawl <non-api-url> --phase fetch` 缓存 HTML 文件

- [x] 4.4 Scrapling 路径适配 `--phase convert`
  - 在 `runCrawl()` 的 Scrapling 分支中：当 `--phase convert` 时
    - 从缓存读取 HTML（`loadScraplingCache`）
    - 通过 `--ai-targeted file://` 或 `htmlToMarkdown()` fallback 转换
    - 写入 .md 到 runDir
    - 不发起 HTTP 请求
  - **验证**：有缓存时 `--phase convert` 离线执行成功

- [x] 4.5 弃用标记：`--keep-html` 和 `--no-markdown`
  - `--keep-html` 使用时输出 warning 引导到 `--phase fetch`
  - `--no-markdown` 使用时输出 tip 引导到 `--phase fetch`
  - 行为不变（向后兼容），仅新增日志提示
  - **验证**：带 flag 执行，stderr 输出弃用提示

## 5. 收敛与验证准备

- [x] 5.1 准备验证环境
  - 确认 `.gitignore` 已排除 `.cache/`
  - 确认 Isaac wiki strategy 文件可正常解析
  - 选取 10 个测试页面（覆盖 entity_page / list_page / disambiguation / infobox 页面）：
    - `The Lamb`（entity_page，有 infobox）
    - `Isaac`（entity_page，角色页面）
    - `Brimstone`（entity_page，道具页面）
    - `Items`（list_page，列表页）
    - `Cards`（list_page，列表页）
    - `Shovel (Disambiguation)`（disambiguation 页面）
    - `The Lost`（entity_page，角色页面）
    - `D6`（entity_page，道具页面）
    - `Mom`（entity_page，boss 页面）
    - `Magic Mushroom`（entity_page，有特殊模板）

- [x] 5.2 编写验证脚本或手动验证清单
  - 步骤 1：`--phase discover` 获取完整 manifest，手动裁剪为 10 页
  - 步骤 2：`--phase fetch --from-manifest <10-page-manifest>` → 校验缓存文件生成
  - 步骤 3：`--phase convert --from-manifest <10-page-manifest>` → 校验 .md 输出质量
  - 步骤 4：修改 strategy extraction 配置（如增删 cleanup_selector）→ `--phase convert` → 校验输出变化
  - 步骤 5：`--phase fetch` 再次执行 → 校验所有 10 页被跳过（日志 `"skipping X cached"`）
  - 步骤 6：删除 1 个缓存文件 → `--phase fetch` → 校验仅该页被重新 fetch
  - 步骤 7：`--phase fetch --re-fetch` → 校验所有 10 页被重新 fetch 并覆盖缓存
  - 步骤 8：断网测试 `--phase convert` → 校验成功执行

## 6. 验证与回写收敛

- [x] 6.1 执行 verification 清单，生成 `verification.md`
  - 记录每步的实际 output、缓存文件截图/内容、日志摘要
  - 标注 pass/fail 结论
- [x] 6.2 基于 verification 结论生成 `writeback.md`
- [x] 6.3 执行 writeback：更新 AGENTS.md 能力描述、README.md（如需要）
