# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认所有 6 个 capability spec 已覆盖 proposal 中的问题（P-1/P-3 bugfix, Phase 0, page-assignment, resume, auto-link-fix, strategy schema）
- [x] 1.2 确认 `HtmlToMarkdownConverter._to_markdown_link` 现有测试覆盖（如有），确保 URL 解码修改不破坏现有行为
- [x] 1.3 确认 `standalone.py` 调用链中 `client.parse()` 是否支持 `redirects` 参数传递

## 2. 核心实现任务

### 2.1 Bugfix Layer

- [x] 2.1.1 `standalone.py` — `fetch_and_convert()` 中 `client.parse(page=title, prop="text")` 改为 `client.parse(page=title, prop="text", redirects=True)`
  - 验证：对 BOI `Main_Page`（重定向页）调用 `fetch_and_convert`，确认返回非空内容
- [x] 2.1.2 `scripts/explore/main.py` — `_fetch_wikitext()` 中 API URL 增加 `&redirects=true` 参数
  - 验证：对重定向页调用 `_fetch_wikitext`，确认返回 wikitext 内容
- [x] 2.1.3 `converters/html_to_markdown.py` — `_to_markdown_link()` 方法增加 `from urllib.parse import unquote`，在 `title.replace("_", " ")` 前调用 `unquote()`
  - 验证：构造 `href="https://domain/wiki/Mom%27s_Knife"`，manifest 含 `"Mom's Knife"`，确认匹配成功 → `[Mom's Knife](Mom's_Knife.md)`
- [x] 2.1.4 `standalone.py` — `fetch_and_convert()` 中 title 提取增加 `unquote()` 解码
  - 验证：对 `Mom's Knife` (`%27`) URL 调用 `fetch_and_convert`，确认传给 API 的是解码后的 `Mom's Knife`
- [x] 2.1.5 Python 3.9 兼容性 — `html_to_markdown.py`、`pipeline/phase_b.py`、`phase_b.py` 增加 `from __future__ import annotations`
  - 验证：`python3` (3.9.6) 能正常导入所有模块

### 2.2 Pipeline Extension — Phase 0

- [x] 2.2.1 新建 `pipeline/homepage_parser.py`
  - `parse_homepage(client, strategy) -> list[dict]`：获取首页 HTML，按 `category_sections` 选择器提取分类链接列表
  - 每个分类返回 `{name, page_title, type}`
  - API 调用使用 `redirects=true`
- [x] 2.2.2 新建 `pipeline/page_assigner.py`
  - `assign_pages(pages, categories, strategy, client) -> list[dict]`：批量查询 MW 分类标签，按优先级链分配目录
  - 支持手动覆盖（`manual_assignments`）、category_page 特殊成员、MW 分类标签匹配
  - 输出包含 `target_directory`、`target_filename`、`assigned_category`、`mw_categories`、`assignment_method`
- [x] 2.2.3 新建 `pipeline/phase_0.py`
  - `run_phase_0(client, strategy, origin, platform_variant) -> dict`：编排 homepage_parser → 分类型发现 → page_assigner → manifest 输出
  - 对 `list_page` 类型分类使用 `prop=links` 发现，对 `category_page` 类型使用 `categorymembers` 发现
  - 输出 manifest JSON 与 Phase A 格式兼容
- [x] 2.2.4 `homepage_parser.py` — `_extract_links_from_element()` 解除 `Category:` 命名空间链接过滤
  - 验证：BOI 首页 gallery 中的 `Category:Modes`、`Category:Objects` 链接被提取
- [x] 2.2.5 `homepage_parser.py` — `parse_homepage()` 增加 Category: 页面自动类型识别
  - `page_title` 以 `Category:` 开头时自动设为 `category_page` 类型
  - 验证：Modes 和 Objects 被标记为 `category_page`，使用 `categorymembers` 发现

### 2.3 Pipeline Integration

- [x] 2.3.1 `orchestrate.py` — `run_pipeline()` 增加 `"homepage"` phase 调度分支
  - 解析 `--phase homepage` 时调用 `run_phase_0()`
  - Phase 0 输出的 manifest 写入 `page_manifest.json`，供 Phase B 消费
  - `api.homepage` 缺失时返回错误
- [x] 2.3.2 `orchestrate.py` — pipeline 结束时自动调用 `fix_links_in_dir(output_dir, domain, manifest_pages)`
  - 插入位置：Phase C 完成后（或 Phase B 后如果无 Phase C）
  - 失败时 log.warning，不改变 exit code
- [x] 2.3.3 `cli.py` — `_add_pipeline_args()` 中 `--phase` choices 增加 `"homepage"`
  - 更新 `choices=["A", "B", "C", "homepage", "all"]`
- [x] 2.3.4 `orchestrate.py` — `run_pipeline()` 增加 `api.homepage` 自动 Phase 检测
  - 策略含 `api.homepage` 且未显式传 `--phase` 时，默认 phases 从 `["A","B","C"]` 切换为 `["homepage","B","C"]`
  - 验证：用含 `api.homepage` 的策略运行不传 `--phase` 的 pipeline，确认走 Phase 0

### 2.4 Resume Support

- [x] 2.4.1 新建 pipeline state 管理（`pipeline/state.py`）
  - `load_state(output_dir) -> dict`：加载 `.pipeline_state.json`
  - `save_state(output_dir, state)`：原子写入状态文件
  - `mark_completed(output_dir, page_title)`：追加 completed_pages
- [x] 2.4.2 Phase B — `run_phase_b()` 在逐页处理前检查 completed_pages，跳过已完成页面
  - 同时验证输出文件存在性（文件缺失则重新提取）
- [x] 2.4.3 `cli.py` — 增加 `--resume` / `--no-resume` 标志
  - `--resume` 默认启用
  - 增加 `--resume-flush-interval` 参数（默认 100）
- [x] 2.4.4 `orchestrate.py` — `run_pipeline()` 在启动时初始化/加载状态文件

### 2.5 Strategy File Update

- [x] 2.5.1 更新 `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 添加 `api.homepage` 配置块（18 个分类 + 目录映射 + 优先级）
  - 添加 `structure.pages` 中的 `category_page` 类型定义
  - 添加 KI-7: 链接索引构建与注入验证

## 3. 收敛与验证准备

- [x] 3.1 整理需要进入 verification 的证据：
  - Bugfix 验证：P-1（重定向首页 fetch 返回非空）、P-3（URL 编码标题正确匹配）
  - Phase 0 验证：BOI 首页 18 分类发现 + 页面分配，manifest 格式兼容 Phase B
  - Resume 验证：中断后恢复，completed_pages 跳过正确
  - Auto link fix 验证：pipeline 结束后 `fix_links_in_dir` 统计日志
- [x] 3.2 标记需要进入 writeback 的摘要：
  - 项目页面 P-1~P-6 状态更新
  - 项目页面 S-1~S-4 状态更新
  - 策略文件 `api.homepage` 配置生效

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成或更新 verification.md（覆盖 spec-to-implementation 与 task-to-evidence）
- [x] 4.2 基于 verification.md 结论生成或更新 writeback.md（目标、字段映射、前置条件）
- [x] 4.3 执行 writeback.md 中定义的回写目标，并记录可审计证据（链接、时间、执行人、结果）
