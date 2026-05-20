# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认每个 capability spec 的实现范围与边界
  - `mw-category-aliases` (new): 策略字段定义 + page_assigner 别名匹配
  - `page-assignment` (modified): Step 2 扩展 + page_categories 接入 + alias 集成
  - `pipeline-cli-entry` (modified): parseArgs `--output` + runCrawl 透传
  - `pipeline-convert-phase` (modified): 逐页写 .md + 跳过已完成页
  - `pipeline-resume` (modified): 逐页更新 state + 批量 flush
- [x] 1.2 确认依赖前置条件
  - `fix-pipeline-quality-gaps` 已合并（Phase 统一、exclude_categories 提升）
  - BOI 策略文件已包含 `taxonomy.page_categories` 映射
  - Fetch 阶段增量缓存已就绪

## 2. 核心实现任务

### 2.1 page_assigner Step 2 扩展 (spec: page-assignment → source-category-assignment)

- [x] 2.1.1 重命名 `_apply_category_page_member_assignments` → `_apply_source_category_assignments`
  - 文件: `scripts/pipeline/pipeline/page_assigner.py`
  - 修改函数签名：移除 `cat_page_names` 参数，改用 `assignment_priority` 列表
  - 匹配逻辑：遍历 `assignment_priority`，首个在 `source_categories` 中的 name 生效
  - `assignment_method` 从 `"category_page_member"` 改为 `"source_category_match"`
  - 验证: 单元测试确认 list_page 类型 source_categories 能被匹配

- [x] 2.1.2 更新 `assign_pages()` 调用点
  - 文件: `scripts/pipeline/pipeline/page_assigner.py`
  - 将 `_apply_category_page_member_assignments(...)` 调用替换为 `_apply_source_category_assignments(...)`
  - 传入 `assignment_priority` 而非 `cat_page_names`
  - 验证: 函数调用参数正确，无遗留引用

### 2.2 mw_category_aliases 支持 (spec: mw-category-aliases → alias-priority-resolution)

- [x] 2.2.1 构建 alias 查找表
  - 文件: `scripts/pipeline/pipeline/page_assigner.py`
  - 在 `_apply_mw_category_matching()` 入口构建 `alias_map = {}`
  - 遍历 `categories_cfg`，读取 `mw_category_aliases` 字段
  - `alias_map[alias_name] = (cat_name, cat_name_to_dir[cat_name])`
  - 验证: 对 BOI 策略构建 alias_map，确认 `"Collectibles"` → `("Items", "items")`

- [x] 2.2.2 扩展 MW category 匹配逻辑
  - 文件: `scripts/pipeline/pipeline/page_assigner.py`
  - 在 `_apply_mw_category_matching` 的 priority 循环中：
    - 先检查 `priority_name in mw_cats`（name 直接匹配）
    - 再检查 `any(alias in mw_cats for alias in cat_aliases.get(priority_name, []))`（别名匹配）
  - 验证: MW category `"Collectibles"` 匹配到 homepage category `"Items"`

### 2.3 page_categories 接入 (spec: page-assignment → page-categories-fallback)

- [x] 2.3.1 读取 taxonomy.page_categories 构建补充映射
  - 文件: `scripts/pipeline/pipeline/page_assigner.py`
  - 在 `assign_pages()` 中读取 `strategy["api"]["taxonomy"]["page_categories"]`
  - 构建 `page_cat_dir_map`: 遍历 `page_categories`，取 value 的顶层 segment，映射到 `cat_name_to_dir` 中对应 category 的 dir
  - 传入 `_apply_mw_category_matching()` 作为兜底映射
  - 验证: `page_cat_dir_map["Stages"]` → `"chapters"`（因为 `"Chapters"` → `"chapters"`）

- [x] 2.3.2 在 MW category 匹配中使用 page_cat_dir_map
  - 文件: `scripts/pipeline/pipeline/page_assigner.py`
  - 在 `_apply_mw_category_matching` 的匹配循环末尾，若 `cat_name_to_dir` 和 `alias_map` 均未匹配
  - 遍历 `mw_cats`，查询 `page_cat_dir_map`
  - 首个匹配的 `page_cat_dir_map[mw_cat]` 作为 target_dir
  - `assignment_method` 为 `"mw_category_match"`
  - 验证: MW category `"Stages"` 通过 page_categories 映射到 `"chapters"` 目录

### 2.4 CLI `--output` 支持 (spec: pipeline-cli-entry → crawl-output-directory)

- [x] 2.4.1 parseArgs 添加 `--output` 解析
  - 文件: `scripts/chrome-agent-cli.mjs`
  - 在 `parseArgs()` 的 for 循环中添加 `--output` / `--output=` 解析
  - 新增 `let outputDir = null` 变量
  - 验证: `parseArgs(["crawl", "url", "--output", "/tmp/test"])` → `outputDir: "/tmp/test"`

- [x] 2.4.2 runCrawl 接收并使用 outputDir
  - 文件: `scripts/chrome-agent-cli.mjs`
  - `runCrawl()` opts 解构中添加 `outputDir = null`
  - 当 `outputDir` 有值时：`runDir = path.resolve(outputDir)`，跳过 `buildRunPaths` 的 runDir
  - `ensureDir(runDir)` 确保目录存在
  - reportPath 仍用 `buildRunPaths` 生成（report 与 output 目录分离）
  - 验证: `chrome-agent crawl <url> --output /tmp/test` → 文件写到 `/tmp/test/`

- [x] 2.4.3 runCrawlMediawikiApi 透传 outputDir
  - 文件: `scripts/chrome-agent-cli.mjs`
  - `runCrawlMediawikiApi()` 中当 runDir 来自自定义 outputDir 时
  - 确保 `--output runDir` 仍正确传递给 Python pipeline
  - 验证: `--output` 指定的目录被 Python pipeline 使用

- [x] 2.4.4 main() 传递 outputDir 到 runCrawl
  - 文件: `scripts/chrome-agent-cli.mjs`
  - `case "crawl"` 调用中添加 `outputDir: parsed.outputDir`
  - 验证: 端到端 `--output` 传递链完整

### 2.5 Convert 阶段增量落盘 (spec: pipeline-convert-phase → incremental-page-write, pipeline-resume → incremental-state-update)

- [x] 2.5.1 逐页写 .md 文件
  - 文件: `scripts/pipeline/pipeline/phases/convert.py`
  - 在 `run_convert()` 的 per-page 循环中，成功转换后立即写文件：
    ```python
    if result["status"] == "ok":
        filepath = os.path.join(output_dir, page["target_directory"], page["target_filename"])
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result["content"])
    ```
  - 验证: 转换 10 页后中断，确认 10 个 .md 文件存在

- [x] 2.5.2 批量 flush state（每 50 页）
  - 文件: `scripts/pipeline/pipeline/phases/convert.py`
  - 在循环中维护 `flush_counter`，每 50 页调用 `save_state()`
  - 添加 `completed_pages_set.add(title)` 跟踪
  - 循环结束后最终 flush
  - 验证: 转换 120 页后中断，state 包含约 100-120 个 completed titles

- [x] 2.5.3 Resume 跳过已转换页面
  - 文件: `scripts/pipeline/pipeline/phases/convert.py`
  - 在 per-page 循环开头检查 resume 状态：
    ```python
    if resume_enabled and completed_pages_set and title in completed_pages_set:
        filepath = os.path.join(output_dir, page["target_directory"], page["target_filename"])
        if os.path.exists(filepath):
            results[title] = {"title": title, "status": "ok", "content": None, "skipped": True}
            continue
    ```
  - 验证: resume 时已有 .md 文件的页面被跳过，不重新从 cache 加载和转换

### 2.6 BOI 策略补全 (spec: mw-category-aliases → mw-category-aliases-field)

- [x] 2.6.1 添加 mw_category_aliases 到 Items 等关键 category
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 修改 `api.homepage.categories` 条目：
    ```yaml
    - {name: "Items", dir: "items", mw_category_aliases: ["Collectibles", "Activated Collectibles", "Passive Collectibles"]}
    - {name: "Bosses", dir: "bosses", mw_category_aliases: ["Bosses"]}
    - {name: "Chapters", dir: "chapters", mw_category_aliases: ["Stages"]}
    - {name: "Achievements", dir: "achievements", mw_category_aliases: ["Achievements"]}
    ```
  - 验证: YAML 语法正确，`mw_category_aliases` 字段存在

## 3. 收敛与验证准备

- [ ] 3.1 准备 S-1 验证证据
  - 检查点: 用 BOI 策略运行 homepage discovery → manifest 中 Items 目录 page_count > 700（而非 0）
  - 检查点: `assignment_method` 分布中 `"source_category_match"` 占比 > 50%
  - 检查点: misc 目录页面数 < 100（原 1126）

- [ ] 3.2 准备 S-2 验证证据
  - 检查点: `page_cat_dir_map` 中 `"Stages"` → `"chapters"` 映射存在
  - 检查点: MW category `"Stages"` 的页面被分配到 `chapters/` 目录

- [ ] 3.3 准备 P-1 验证证据
  - 检查点: `chrome-agent crawl <url> --output /tmp/test-output` → 文件在指定目录
  - 检查点: `--output` 缺失时行为不变

- [ ] 3.4 准备 P-2 验证证据
  - 检查点: Convert 中断后 `.pipeline_state.json` 包含已完成页面
  - 检查点: Resume 跳过已转换页面，日志显示 `"skipped (already converted)"`

- [ ] 3.5 标记需要回写的目标
  - `handoffs/20260519-crawl-bindingofisaacrebirth-wiki-gg/handoff.md` — S-1/S-2/P-1/P-2 状态更新
  - `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — `mw_category_aliases` 字段

## 4. 验证与回写收敛

- [ ] 4.1 基于验证结果生成 verification.md
- [ ] 4.2 基于 verification.md 结论生成 writeback.md
- [ ] 4.3 执行回写:
  - 更新 handoff 文档 Issue 状态（S-1: fixed, S-2: fixed, P-1: fixed, P-2: fixed）
  - 更新 BOI 策略 `mw_category_aliases` 字段
