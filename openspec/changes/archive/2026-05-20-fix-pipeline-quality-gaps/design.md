# Design

## Context

`bindingofisaacrebirth.wiki.gg` 全站爬取暴露了 MediaWiki API 提取管线的系统性质量缺口。explore 阶段诊断发现 4 类根因：Phase 命名与调度混乱、Phase 0 功能缺口、HTML→Markdown 转换器双路径分裂、策略 schema 歧义。

本 change 通过 6 个 modified + 2 个 new capability 填补所有缺口，统一管线质量。

## Goals / Non-Goals

**Goals:**
- 统一 Phase A/0 为 Discovery 阶段的两种策略实现，通过 `--discovery` CLI 参数选择
- 修复 `api.homepage` 自动检测（策略有 homepage 时默认走 homepage 发现）
- Phase 0 将分类页面本身纳入 manifest，填充 list_page_content
- `html_to_markdown.py` 修复 infobox 表格渲染、读取 extraction.infox 配置、增加空值防御
- Architecture Gate 扩展校验范围到 `html_to_markdown.py`
- `exclude_categories` 从 `api.homepage` 提升到 `api` 顶层
- 补全 BOI 策略的 `page_categories` 映射
- 删除死代码 `_pipeline_legacy.py`、`_strategies_legacy.py`
- CLI 向后兼容：`--phase homepage` 和单字母值继续可用但发 deprecation warning

**Non-Goals:**
- 不统一 `sample_converter.py` 与 `html_to_markdown.py` 为单一转换器（后续 change 评估）
- 不修改 `link_fixer.py`、`page_assigner.py` 核心逻辑
- 不修改 Phase B/C 的结构
- 不新增 discovery 策略类型（仅重构现有两种）
- 不修改 `_pipeline_legacy.py` 的功能（直接删除）

## Decisions

### D1: `--discovery` 作为独立参数，与 `--phase` 正交

**Decision**: 新增 `--discovery {auto,allpages,homepage}` 参数，默认 `auto`。`--phase` 简化为 `{all,extract,assemble}`。

**Rationale**: Discovery 策略选择与 Execute 阶段选择是正交的两个维度。将它们分离避免了 `--phase homepage` 这种混淆性命名，也消除了 `--phase all` 不含 homepage 的歧义。

**Migration**: `--phase homepage` → `--discovery homepage`（发 deprecation warning 后自动映射）。`--phase A/B/C` → 映射到 `extract/assemble` 并警告。

### D2: Phase 0 文件保留原名，内部函数加策略命名别名

**Decision**: 模块文件 `phase_0.py` 和 `phase_a.py` 保留原名。内部添加 `run_homepage_discovery()` 和 `run_allpages_discovery()` 作为面向外部的函数名。log 消息使用策略名而非 phase 编号。

**Rationale**: 修改文件名需要更新所有 import 路径、package `__init__.py`、以及外部脚本引用。风险大于收益。通过函数别名和 log 消息实现命名语义统一，最小化变更面。

### D3: Infobox 表格组装在 `_render_block()` 中通过父节点检测实现

**Decision**: 在 `_render_block()` 处理 `<aside class="portable-infobox">`（或配置的 `infobox.selector`）时，检测其子元素集合，收集所有 `div.pi-data` 字段后一次性生成完整 Markdown 表格。

**Rationale**: 当前实现将每个 `div.pi-data` 独立渲染为 `| **label** | value |`，因为 selectolax 的 `_child_nodes()` 产生的子节点被 `_render_blocks()` 逐个处理。需要让父节点（infobox container）的渲染逻辑识别自身为 infobox，批量处理子字段。

**Alternative**: 在 `convert_body()` 中预处理 HTML（提取 infobox → 替换为 table → 再转换）。更复杂但解耦更好。由于 infobox 始终是页面开头的内容块，在 `_render_block()` 中处理是最直接的。

### D4: list_page_content 在 Phase 0 中通过批量 API 获取

**Decision**: 在 `run_phase_0()` 的 Step 2 完成后，新增 Step 2.5：遍历所有 `type: list_page` 的分类页面，调用 `action=parse&prop=wikitext` 获取 wikitext，存入 `manifest["list_page_content"]`。

**Rationale**: 与 Phase A 的 `fetch_list_pages()` 行为一致，确保 Phase C 能消费相同格式的数据。单个页面获取失败不阻断整体流程。

### D5: `exclude_categories` 读取优先级链

**Decision**: 在 `orchestrate.py` 中构建统一的 exclude_categories 解析函数，优先级为：
1. 读取 `api.exclude_categories`（新顶层位置）
2. 读取 `api.homepage.exclude_categories`（legacy fallback）
3. 合并 CLI `--exclude-category` 参数
4. 结果传递给 Discovery 函数

**Rationale**: 向后兼容 + 向前统一。Phase A 和 Phase 0 都通过同一个入口获取排除列表。

### D6: Architecture Gate 双文件校验

**Decision**: `architecture_gate.py` 的 `_PIPELINE_REL` 改为 `_PIPELINE_FILES` 列表，包含 `sample_converter.py` 和 `html_to_markdown.py`。`dead_config` 仅在两个文件都未引用时触发；`partial_coverage`（仅一个文件引用）作为 warning。

**Rationale**: 反映当前两条代码路径并存的现实。warning 级别确保不会阻塞 Auto-remediation，但提醒开发者保持同步。

## Risks / Migration

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `--phase` 废弃值破坏现有调用脚本 | Medium | Low | 所有废弃值自动映射并发 warning，不报错。`chrome-agent-cli.mjs` 同步更新 |
| Infobox 表格组装影响非 wiki.gg 站点 | Low | Medium | 通过 `extraction.infox.enabled` 配置门控；默认不启用则回退到原行为 |
| Phase 0 增加分类页面入 manifest 改变 manifest 大小 | High | Low | Phase B/C 已有分页处理，额外 28 个分类页面影响可忽略 |
| 删除 legacy 文件意外影响外部引用 | Low | Low | grep 验证无任何 import 引用后再删除 |
| `api.homepage` 优先于 `discovery_strategy: allpages` 的行为变更 | Medium | Medium | 发 warning log 明确告知行为变更；`--discovery allpages` 显式覆盖 |
