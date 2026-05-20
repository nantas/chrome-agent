# Design

## Context

前次 change（`fix-pipeline-quality-gaps`）修复了 Phase 统一、infobox 转换、exclude_categories 提升等结构性问题，使 1756 页全站爬取达到了 100% 提取成功率。但 page_assigner 的核心分配逻辑未被触及——64% 的页面仍落入 `misc` 目录。CLI `--output` 缺失和 Convert 阶段批量落盘问题也未涉及。

本次 change 聚焦于 page_assigner 分配逻辑修复（S-1/S-2）、CLI 输出目录自定义（P-1）、Convert 增量落盘（P-2），不涉及 Phase 结构或转换器变更。

## Goals / Non-Goals

**Goals:**
- 扩展 `page_assigner` Step 2 匹配所有类型的 `source_categories`（解决 S-1 核心问题）
- 支持 `mw_category_aliases` 策略字段（解决 S-1 边缘 case）
- 接入 `taxonomy.page_categories` 作为 MW category fallback 补充映射（解决 S-2）
- CLI `crawl` 命令添加 `--output` 参数（解决 P-1）
- Convert 阶段逐页写 `.md` 文件 + 逐页更新 state（解决 P-2）
- BOI 策略补全 `mw_category_aliases` 字段

**Non-Goals:**
- 不修改 Fetch 阶段逻辑
- 不修改 Assembly 阶段 index.md 生成逻辑
- 不修改 `link_fixer.py`
- 不新增 discovery 策略类型
- 不统一两条转换器路径（后续 change 评估）
- 不修改 `homepage_parser.py`

## Decisions

### D1: Step 2 重命名为 source_category_match，匹配所有类型

**Decision**: 将 `_apply_category_page_member_assignments` 重命名为 `_apply_source_category_assignments`。匹配条件从 `cat_name in cat_page_names`（仅 category_page）改为 `cat_name in assignment_priority`（所有类型），按 priority 顺序首个匹配生效。

**Rationale**: Phase 0 homepage discovery 已成功为每个页面标记 `source_categories`（如 `"Items"`），这个信息比 MW category tags 更可靠——它是基于 homepage 的 list_page 链接直接确定的。只需让 Step 2 不限制类型即可解决 64% 页面归入 misc 的核心问题。

**Alternative**: 新增独立 Step 2.5 专门处理 list_page source_categories。被否决——与 Step 2 逻辑完全重复，增加维护成本。

### D2: mw_category_aliases 构建别名查找表

**Decision**: 在 `_apply_mw_category_matching` 中构建 `alias_map: {mw_cat_name → (homepage_cat_name, target_dir)}`。MW category 匹配时同时检查 `cat_name_to_dir`（name 直接匹配）和 `alias_map`（别名匹配）。

**Rationale**: 最小侵入性修改——只在 Step 3 的匹配循环中扩展检查范围，不影响 Step 1/Step 2 的逻辑。别名继承 homepage category 的 priority 位置。

### D3: page_categories 作为 MW category → dir 补充映射

**Decision**: 在 `assign_pages()` 入口读取 `taxonomy.page_categories`，构建 `page_cat_dir_map: {mw_cat_name → target_dir}`。Step 3 在 `cat_name_to_dir` 和 `alias_map` 均未匹配时，查询 `page_cat_dir_map` 作为最后兜底。

**Rationale**: `page_categories` 已存在于策略中且已定义完整映射（如 `"Stages": "Chapters"`），复用现有配置避免重复定义。path 取顶层 segment 映射到 homepage category dir。

**Alternative**: 删除 `page_categories` 配置，统一到 `mw_category_aliases`。被否决——`page_categories` 在 Phase C list_page 分割逻辑中仍有使用。

### D4: CLI `--output` 通过 opts 透传到 runCrawl

**Decision**: `parseArgs()` 新增 `outputDir` 解析。`main()` 将 `parsed.outputDir` 传入 `runCrawl()` 的 opts。`runCrawl()` 中当 `outputDir` 有值时，`runDir = path.resolve(outputDir)`，跳过 `buildRunPaths`。`runCrawlMediawikiApi()` 同步接收并透传到 Python pipeline 的 `--output`。

**Rationale**: 最小修改——`buildRunPaths` 不变（report 路径等仍可生成），仅在 `runCrawl` 入口做路径替换。`batch` 命令已有类似模式可参考。

### D5: Convert 逐页写 .md 并批量 flush state

**Decision**: 在 `run_convert()` 的 per-page 循环中，成功转换后立即写 `.md` 文件到 `<output_dir>/<target_dir>/<target_filename>`。State 更新采用批量 flush（每 50 页调一次 `save_state()`），避免每页都做 JSON 序列化。

**Rationale**: 每页写 `.md` 文件是轻量 I/O（单个文件写入），但每页 `save_state()` 需要序列化整个 completed_pages 列表（1756 个 title）。批量 flush 在恢复粒度（最多丢 50 页进度）和 I/O 开销间取得平衡。

**Alternative**: 每页 flush state。在 1756 页场景下每页序列化 ~100KB JSON 是可接受的，但无必要。

### D6: Assembly 阶段跳过已写 .md 文件

**Decision**: Assembly 阶段写单个页面文件时，如果文件已存在（由 Convert 增量写入），覆盖写入（确保最终一致性）。index.md 等聚合文件始终重新生成。

**Rationale**: 保持 Assembly 的幂等性——无论 Convert 是否增量写入，Assembly 结果不变。

## Risks / Migration

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Step 2 扩展匹配范围导致过度匹配 | Low | Medium | 按 `assignment_priority` 顺序首个匹配生效，与 Step 3 行为一致 |
| `mw_category_aliases` 引入策略 schema 变更 | Low | Low | 字段为 optional，缺失时行为不变 |
| Convert 增量写 .md 改变 Assembly 语义 | Low | Low | Assembly 仍覆盖写入，幂等性不变 |
| `--output` 路径不存在时崩溃 | Medium | Low | `os.makedirs(output_dir, exist_ok=True)` 在 runCrawl 入口调用 |
| Resume state 与实际文件不一致（手动删除 .md 后 state 仍标记完成） | Low | Medium | `is_page_completed()` 已验证文件存在性，不存在时重新转换 |
| BOI 策略 `mw_category_aliases` 不完整（遗漏某些 MW category） | Medium | Low | 先用最核心的 `"Items" → ["Collectibles"]` 覆盖 718 页，其余留作后续迭代 |
