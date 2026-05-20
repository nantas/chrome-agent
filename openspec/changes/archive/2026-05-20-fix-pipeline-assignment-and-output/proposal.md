# Proposal

## 问题定义

对 `bindingofisaacrebirth.wiki.gg` 的全站爬取（1756 页面，100% 提取成功）暴露了 **5 个管线缺陷**，导致 64% 的页面被错误归入 `misc` 目录。前一次 change（`fix-pipeline-quality-gaps`）修复了 Phase 统一、infobox 转换、exclude_categories 提升等问题，但 **page_assigner 的核心分配逻辑** 和 **CLI 输出路径** 未涉及。

详细诊断结果：

1. **S-1 (P0) — MW category 映射断裂**：`page_assigner._apply_mw_category_matching()` 用 `assignment_priority` 中的名字（如 `"Items"`）匹配页面的 MW category tags（实际为 `"Collectibles"`），名称不匹配导致 1126 页落入 `misc`。虽然重构后新增了 Step 2（`_apply_category_page_member_assignments`），但它只匹配 `category_page` 类型，不匹配 `list_page` 类型的 `source_categories`（Items/Bosses 等全是 list_page）。

2. **S-2 (P1) — `page_categories` 死配置**：策略中 `taxonomy.page_categories` 定义了 `"Collectibles": "Collectibles"` 等映射，但 `page_assigner` 只读 `homepage.categories`，不读 `taxonomy.page_categories`，使其成为死配置。

3. **S-3 (P2) — Exclude 不覆盖列表页本身**：**已在前次 change 中修复**。`discovery_homepage.py` 整体移除 excluded category，列表页本身不进入 manifest。

4. **P-1 (P1) — CLI `--output` 缺失**：`chrome-agent crawl` 命令将输出硬编码到 `outputs/<timestamp>-crawl-<slug>/`，`parseArgs()` 不解析 `--output` 参数，用户无法指定输出目录，必须绕过 CLI 直接调用内部管线。

5. **P-2 (P2) — Convert 阶段中间结果不落盘**：Fetch 阶段已实现增量缓存（每页写 cache），但 Convert 阶段的结果全在内存 `results` dict 中，仅在结束后批量写 `extraction_results.json`。Assembly 阶段读此 JSON 写 .md 文件，中断后已转换内容丢失，需要重跑。

## 范围边界

**范围内：**
- S-1 修复：扩展 `page_assigner` Step 2 匹配 list_page 类型 source_categories；添加 `mw_category_aliases` 策略字段支持
- S-2 修复：接入 `taxonomy.page_categories` 作为 MW category fallback 的补充映射源
- P-1 修复：CLI `parseArgs` 添加 `--output` 解析，`runCrawl` 支持自定义输出目录
- P-2 修复：Convert 阶段逐页增量写 .md 文件并更新 pipeline state
- BOI 策略补全：为 `homepage.categories` 条目添加 `mw_category_aliases`

**范围外：**
- S-3 已修复，不涉及
- 不修改 Fetch 阶段逻辑（已有增量缓存）
- 不修改 Assembly 阶段的 index.md 生成逻辑
- 不新增 discovery 策略类型
- 不修改 `link_fixer.py`

## Capabilities

### New Capabilities

- `mw-category-aliases`: 策略侧 `mw_category_aliases` 字段支持——允许一个 homepage category 映射多个 MW category 名（如 `"Items"` → `["Collectibles", "Activated Collectibles"]`）

### Modified Capabilities

- `page-assignment`: page_assigner 优先级链扩展——Step 2 同时匹配 list_page 和 category_page 的 source_categories；Step 3 读取 `mw_category_aliases` 和 `taxonomy.page_categories` 作为补充映射源
- `pipeline-cli-entry`: CLI 添加 `--output <dir>` 参数，crawl 命令支持自定义输出目录
- `pipeline-convert-phase`: Convert 阶段逐页增量写 .md 文件到 output 目录，同步更新 pipeline state
- `pipeline-resume`: `mark_completed()` 在 Convert 阶段逐页调用，支持中断后跳过已转换页面

## Capabilities 待确认项

- [x] 能力清单已基于 handoff 诊断确认：S-1/S-2/P-1/P-2 四个问题的修复范围已明确

## Impact

| 影响维度 | 详情 |
|---------|------|
| page_assigner 行为 | Step 2 从仅匹配 category_page 扩展为匹配所有类型的 source_categories（按 assignment_priority 顺序） |
| 策略 schema | `homepage.categories` 条目新增可选 `mw_category_aliases` 字段 |
| CLI 接口 | 新增 `--output <dir>` 参数，crawl 命令输出目录可自定义 |
| Convert 阶段 | 逐页写 .md + 逐页更新 state，行为从"批量写"变为"流式写" |
| Resume 行为 | Convert 阶段中断后恢复时，已写的 .md 文件不再需要重跑 |
| 向后兼容 | 无 `mw_category_aliases` 的策略不受影响；无 `--output` 时行为不变 |
| 文件变更 | 修改 3 个 pipeline 文件 + 1 个 CLI 文件 + 1 个策略文件 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页：`openspec/specs/page-assignment/`、`openspec/specs/pipeline-cli-entry/`、`openspec/specs/pipeline-convert-phase/`、`openspec/specs/pipeline-resume/`
- 已确认项目页：`handoffs/20260519-crawl-bindingofisaacrebirth-wiki-gg/handoff.md`、`sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
- 回写目标：handoff 文档 Issue 状态更新、BOI 策略 `mw_category_aliases` 字段添加
