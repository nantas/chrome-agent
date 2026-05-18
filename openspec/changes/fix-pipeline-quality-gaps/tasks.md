# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认所有 8 个 capability spec 覆盖范围完整
  - `discovery-phase-unification` / `homepage-discovery-category-extraction` (new)
  - `homepage-driven-discovery` / `mediawiki-api-extraction-pipeline` / `pipeline-converters` / `explore-architecture-gate` / `pipeline-strategy-schema` / `pipeline-cli-entry` (modified)
- [x] 1.2 确认 `bindingofisaacrebirth.wiki.gg` 策略文件可访问，API key 可用

## 2. 核心实现任务

### 2.1 Phase 命名统一与 CLI 重构 (specs: discovery-phase-unification, pipeline-cli-entry)

- [x] 2.1.1 删除死代码
  - 验证: `grep -r "_pipeline_legacy\|_strategies_legacy" scripts/` 零匹配
  - 删除 `_pipeline_legacy.py` 和 `_strategies_legacy.py`
  - 重新运行 `python3 -m scripts.mediawiki-api-extract --help` 确认功能正常

- [x] 2.1.2 CLI 新增 `--discovery` 参数
  - 文件: `scripts/mediawiki-api-extract/cli.py`
  - 添加 `--discovery {auto,allpages,homepage}` 默认 `auto`
  - 旧值映射: `homepage` → `--discovery homepage`, `A` → extract, `B` → extract, `C` → assemble
  - 废弃值发 `DEPRECATED:` warning
  - 验证: `--help` 显示新参数，`--phase homepage` 发 warning 但继续执行

- [x] 2.1.3 `chrome-agent-cli.mjs` 传递 `--discovery`
  - 文件: `scripts/chrome-agent-cli.mjs` (crawl 命令 MediaWiki API 路径)
  - 策略有 `api.homepage` 时传 `--discovery homepage`，否则不传（auto 默认）
  - 验证: 对 BOI 策略执行 crawl，日志显示 `--discovery homepage`

### 2.2 Orchestrator 修复 (specs: mediawiki-api-extraction-pipeline)

- [x] 2.2.1 统一 discovery dispatch 逻辑
  - 文件: `scripts/mediawiki-api-extract/pipeline/orchestrate.py`
  - 移除 `if not args.phase and strategy.get("api", {}).get("homepage")` 自动检测
  - 替换为基于 `args.discovery` + strategy config 的 dispatch:
    - `args.discovery == "homepage"` → 强制 homepage
    - `args.discovery == "allpages"` → 强制 allpages
    - `args.discovery == "auto"` + strategy 有 `api.homepage` → homepage
    - `args.discovery == "auto"` + strategy 无 `api.homepage` → allpages
  - homepage 无 api.homepage 配置时返回 `EXIT_STRATEGY_ERROR`
  - 验证: 用 BOI 策略无 `--discovery` 运行 → 默认走 homepage

- [x] 2.2.2 exclude_categories 优先级链实现
  - 文件: `scripts/mediawiki-api-extract/pipeline/orchestrate.py`
  - 新增 `_resolve_exclude_categories(strategy, args)` 函数
  - 优先级: `api.exclude_categories` → `api.homepage.exclude_categories` (fallback) → CLI `--exclude-category` → 合并并集
  - Phase A 新增排除逻辑: 在 classify_page 阶段, wiki category 匹配排除列表时跳过
  - 验证: 策略设 `api.exclude_categories: [Music]`, 运行 Phase A → Music 类别页面不在 manifest

- [x] 2.2.3 Log 消息统一
  - Phase A 和 Phase 0 的 log 消息统一使用 `"allpages discovery"` / `"homepage discovery"` 等描述性命名
  - 验证: 运行任意 crawl → log 中无裸 `"Phase 0"` 或 `"Phase A"` 字样

### 2.3 Phase 0 功能缺口填补 (specs: homepage-discovery-category-extraction, homepage-driven-discovery)

- [x] 2.3.1 分类页面入 manifest
  - 文件: `scripts/mediawiki-api-extract/pipeline/phase_0.py`
  - `_discover_category_pages()` 完成后, 遍历 categories 列表
  - 对每个 `type: list_page` 的 category, 将 `page_title` 作为页面加入 `all_pages`
  - 标记 `is_list_page: true`
  - 去重: 若 category page 已被 discovered, 仅更新 `is_list_page` 标记
  - 验证: homepage 发现后, manifest 的 pages 包含 "Items", "Bosses" 等分类页

- [x] 2.3.2 list_page_content 填充
  - 文件: `scripts/mediawiki-api-extract/pipeline/phase_0.py`
  - 在 Step 2 发现完成后, Step 3 分配前, 新增获取步骤
  - 遍历 `type: list_page` 的 categories, 调用 `action=parse&prop=wikitext`
  - 存入 `manifest["list_page_content"]`, key 为 page_title, value 为 wikitext
  - 单个页面失败时 log warning 并继续
  - 验证: manifest 的 `list_page_content` 包含 "Items" 等 key, value 为非空 wikitext

- [x] 2.3.3 分类页面目录分配
  - 文件: `scripts/mediawiki-api-extract/pipeline/phase_0.py`
  - 分类页面在 `assign_pages()` 中按 `api.homepage.categories[].dir` 分配目录
  - 分类页面的 `target_filename` 设为 `index.md`
  - `assignment_method` 设为 `"homepage_category"`
  - 验证: manifest 中 "Items" 页面的 `target_directory` 为 `items`, `target_filename` 为 `index.md`

### 2.4 Infobox 转换修复 (specs: pipeline-converters)

- [x] 2.4.1 Infobox 表格组装
  - 文件: `scripts/mediawiki-api-extract/converters/html_to_markdown.py`
  - 在 `_render_block()` 中, 当 node 匹配 infobox selector 时:
    1. 收集所有子元素（field_selector）
    2. 对每个 field, 提取 label_selector 和 value_selector
    3. 应用 infobox_field_handlers
    4. 组装为完整 Markdown 表格: `## Infobox\n\n| Field | Value |\n| --- | --- |\n...`
  - 通过 `extraction.infox.enabled` 门控
  - 验证: BOI 页面 (The Sad Onion) 输出含 `|---|---|` 分隔行的 `## Infobox` 表格

- [x] 2.4.2 读取 extraction.infox 配置
  - 文件: `scripts/mediawiki-api-extract/converters/html_to_markdown.py`
  - Converter 初始化时读取 `extraction_config.get("infobox", {})`
  - 使用配置的 selector/field_selector/label_selector/value_selector
  - 无配置时回退到硬编码默认值 (aside.portable-infobox, div.pi-data 等)
  - 验证: 修改策略 infobox.selector 后重新转换, 使用自定义 selector

- [x] 2.4.3 NoneType 空值防御
  - 文件: `scripts/mediawiki-api-extract/converters/html_to_markdown.py`
  - `_render_block()` 中 `node.text()` / `node.attributes.get()` 返回 None 时使用空字符串
  - `_render_inline_children()` 同处理
  - 验证: 对 BOI 首页 (Binding of Isaac: Rebirth Wiki) 执行转换 → 不崩溃, 产生部分内容

### 2.5 Architecture Gate 扩展 (specs: explore-architecture-gate)

- [x] 2.5.1 双文件校验
  - 文件: `scripts/explore/architecture_gate.py`
  - `_PIPELINE_REL` 改为 `_PIPELINE_FILES = ["scripts/explore/sample_converter.py", "scripts/mediawiki-api-extract/converters/html_to_markdown.py"]`
  - `_detect_dead_config()` 遍历所有文件, 字段在任一文件中被引用即为 `covered`
  - 仅一个文件引用的字段标记为 `partial_coverage` (severity: warning)
  - 验证: 运行 explore → Architecture Gate 报告包含 html_to_markdown.py 的校验结果

### 2.6 策略文件修正 (specs: pipeline-strategy-schema)

- [x] 2.6.1 BOI 策略补全 page_categories
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 添加缺失映射: `Stages: "Chapters"`, `Runes: "Runes"`, `Item pools: "Item_pools"`, `Disambiguations: "Disambiguations"`, `Versions: "Versions"`, `Objects: "Objects"`, `Bugs: "Bugs"`, `Item tags: "Item_tags"`
  - 验证: Phase A 运行后, Misc 目录页面数显著减少

- [x] 2.6.2 exclude_categories 提升到顶层
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 在 `api` 顶层添加 `exclude_categories: [Music, Modding, Version History]`
  - 保留 `api.homepage.exclude_categories` 作为别名
  - 验证: `api.exclude_categories` 在 YAML 顶层存在

- [x] 2.6.3 标注 discovery_strategy 关系
  - 文件: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
  - 在 `api.content_profile.discovery_strategy` 旁添加注释说明与 `api.homepage` 的关系
  - 可选: 移除 `discovery_strategy: "allpages"` 以使用 homepage auto-detect

## 3. 收敛与验证准备

- [ ] 3.1 对 BOI 站点执行完整 crawl 验证
  - `python3 -m scripts.mediawiki-api-extract https://bindingofisaacrebirth.wiki.gg/ --strategy sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md --output outputs/<run-dir> --discovery homepage --concurrency 1 --batch-delay-ms 3000`
  - 检查点:
    - [ ] Infobox 表格含 `|---|---|` 分隔行
    - [ ] 首页不崩溃 (NoneType 修复)
    - [ ] items/index.md 含 Items 分类页实际内容 (非仅链接列表)
    - [ ] Music/Modding/Version History 目录不存在 (exclude 生效)
    - [ ] 337 页不再全落根目录 (page_categories 补全)
    - [ ] 分类页面在 manifest 中 (Items, Bosses 等)

- [ ] 3.2 验证 Architecture Gate 新校验
  - 运行 explore 流程 → Architecture Gate 报告含两个文件的校验结果
  - html_to_markdown.py 无 dead_config 或只有 partial_coverage

- [x] 3.3 验证向后兼容性
  - `--phase homepage` → emits DEPRECATED warning, maps to `--discovery homepage` ✓
  - `--phase A` → emits DEPRECATED warning, maps to `extract` ✓
  - `--phase B` → emits DEPRECATED warning, maps to `extract` ✓
  - `--phase C` → emits DEPRECATED warning, maps to `assemble` ✓
  - `--phase all --discovery homepage` → no warning ✓
  - CLI help shows both new and legacy options ✓
  - Old strategy with only `api.homepage.exclude_categories` → legacy fallback works

## 4. 验证与回写收敛

- [ ] 4.1 基于验证结果生成 verification.md
- [ ] 4.2 基于 verification.md 结论生成 writeback.md
- [ ] 4.3 执行回写:
  - 更新 handoff 文档 Issue 状态
  - 更新 BOI 策略文件 Known Issues 状态
  - 追加 Architecture Gate spec 更新
