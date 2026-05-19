# Handoff: crawl bindingofisaacrebirth.wiki.gg — 工作流问题汇总

## Context

| Field | Value |
|-------|-------|
| Command | `crawl` (via direct `python3 -m scripts.mediawiki-api-extract`) |
| Target | https://bindingofisaacrebirth.wiki.gg/ |
| Timestamp | 2026-05-19 |
| Repo ref | env:CHROME_AGENT_REPO |
| Strategy | `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` |
| Output dir | `raw/external/binding-of-issac-wiki/` (my-wiki 仓库) |
| Pipeline run log | `/tmp/isaac-crawl-resume.log` |
| Manifest | `raw/external/binding-of-issac-wiki/page_manifest.json` |
| Discovery summary | `raw/external/binding-of-issac-wiki/discovery_summary.json` |

## Executive Summary

本次爬取成功提取了 1756 页面（100% 成功率），但暴露了 **3 个 S-line 问题** 和 **2 个 P-line 问题**，其中 S-1（MW category 映射断裂）导致 64% 的页面（1126/1756）被错误归入 `misc` 目录。需要人工后处理脚本重新组织后才达到可用状态。

---

## Issue Catalog

### S-1: MW category → directory 映射断裂（P0）

**分类**: S-line (strategy) — `homepage.categories` 的 name 与 `assignment_priority` 不匹配 MediaWiki 实际 category 名

**现象**: Phase 0 homepage discovery 成功发现了 Items 列表页有 944 个链接页面，但 page_assigner 的 MW category fallback 匹配失败，718 个 item 页面被归入 `misc`。

**根因**:

`page_assigner._apply_mw_category_matching()` 使用 `assignment_priority` 列表中的名字去匹配页面的 MW category tags：

```python
for priority_name in assignment_priority:  # ["Items", "Bosses", "Monsters", ...]
    if priority_name in mw_cats:            # 页面实际 MW category 是 "Collectibles"
        target_dir = cat_name_to_dir.get(priority_name)
```

但策略中：
- `homepage.categories` 定义 `{name: "Items", dir: "items"}` → `cat_name_to_dir["Items"] = "items"`
- `assignment_priority` 列表值为 `["Items", "Bosses", ...]`
- 页面的实际 MW category 是 `"Collectibles"`，不是 `"Items"`

所以 `"Items" in ["Collectibles", "Activated collectibles", ...]` → `False` → 未匹配 → 落入 misc。

同理，`Achievements`, `Chapters`, `Effects`, `Curses`, `Seeds`, `Endings` 等分类也存在类似问题：它们作为 list_page 被成功发现（discovery log 显示 `Achievements: 747 sub-pages`, `Chapters: 57 sub-pages` 等），但 MW category fallback 的名字对不上。

**影响范围**:
- 1126 页面被错误归入 `misc`（占总页面 64%）
- 后处理脚本修复了 810 页（基于 MW category 手动映射），但仍有 300+ 页面留在 misc
- discovery_summary 中 Items/Achievements/Chapters 等 7 个分类的 `page_count: 0`

**证据**:
```
discovery_summary.json: Items page_count=0, Achievements page_count=0, ...
pipeline log: "Page assignment complete: 1755 pages, methods: {'default': 1126, ...}"
pipeline log: "Category 'Items' (list_page): discovered 944 sub-pages" ← 发现成功
pipeline log: "Page 'The Sad Onion' assigned to 'misc' (no matching category)" ← 分配失败
```

**建议修复方案**:
1. **策略侧**（推荐）: 在 `homepage.categories` 中增加 `mw_category_alias` 字段，允许一个 homepage category 映射多个 MW category 名：
   ```yaml
   - {name: "Items", dir: "items", mw_category_aliases: ["Collectibles", "Activated Collectibles", "Passive Collectibles"]}
   ```
2. **管线侧**: `page_assigner._apply_mw_category_matching()` 查询时同时检查 `mw_category_aliases`
3. **备选方案**: 利用 Phase 0 已发现的 list_page 链接信息，在 page_assigner 中增加一步"list_page member assignment"——如果页面是某个 list_page 的链接目标，直接继承该 list_page 的目录

---

### S-2: `page_categories` 映射未被 page_assigner 使用（P1）

**分类**: S-line (strategy) — `taxonomy.page_categories` 字段存在但未接入分配管线

**现象**: 策略中定义了详细的 `page_categories` 映射（如 `Collectibles: "Collectibles"`, `Bosses: "Bosses"`），但这些映射未被 `page_assigner` 使用。

**根因**: `page_assigner.assign_pages()` 只使用 `homepage.categories` 构建 `cat_name_to_dir`，不读取 `taxonomy.page_categories`。`page_categories` 仅在 Phase C 的 list_page 分割逻辑中使用。

**影响**: 策略中的 `page_categories` 成为死配置——定义了但未产生分配效果。

**建议修复**: 让 `page_assigner` 也读取 `page_categories` 作为 MW category fallback 的映射源。

---

### S-3: Exclude categories 不覆盖 Music 列表页本身（P2）

**分类**: S-line (strategy) — exclude 规则不排除列表页入口

**现象**: `Music` 目录中有 1 个文件，是 Music 列表页本身。`exclude_categories` 排除了 Music 分类的子页面发现，但没有排除 Music 列表页本身。

**证据**: 输出目录中 `Music/index.md` 存在（1 file, 0 content pages）。

**建议修复**: Phase 0 在构建 manifest 时，如果 category 在 `exclude_categories` 中，跳过列表页本身的添加。

---

### P-1: `chrome-agent crawl` 不支持自定义输出目录（P1）

**分类**: P-line (pipeline) — CLI 缺少 `--output` 透传

**现象**: 用户需要将爬取结果输出到 my-wiki 仓库的 `raw/external/binding-of-issac-wiki/`，但 `chrome-agent crawl` 命令将输出硬编码到 `outputs/<timestamp>-crawl-<slug>/`，不支持 `--output` 参数。

**根因**: `chrome-agent-cli.mjs` 中 `buildRunPaths()` 硬编码 `runDir`：
```javascript
const runDir = path.join(repoRoot, "outputs", `${stamp}-${command}-${slug}`);
```
内部管线 `mediawiki-api-extract` 的 CLI 支持 `--output`，但外层 `chrome-agent-cli.mjs` 的 crawl 路径不透传。

**影响**: 用户必须绕过 `chrome-agent crawl` CLI，直接调用内部管线 `python3 -m scripts.mediawiki-api-extract`。

**建议修复**: 为 `chrome-agent crawl` 增加 `--output <dir>` 参数，透传到内部管线的 `--output`。当指定时跳过 `buildRunPaths` 的默认路径逻辑。

---

### P-2: Phase B/C 大任务时 bash timeout 导致管线中断（P2）

**分类**: P-line (pipeline) — 长时间运行的管线缺少 daemon 模式

**现象**: 首次执行 Phase B（1756 页面，~40 分钟）超出 bash 工具 1800s timeout，管线被 SIGTERM 杀死。Phase B 的中间状态保存在 `.pipeline_state.json` 中，但 Phase B 的提取结果存储在内存中（不落盘），导致 resume 时发现输出文件缺失，重新提取全部 1756 页面。

**根因**:
1. Phase B 的提取结果是 Python dict（内存），只通过 `extraction_results.json` 在 Phase B 结束时落盘
2. Phase C 依赖 Phase B 的完整结果（内存 dict）来写文件
3. 如果 Phase B 被中断且 Phase C 未执行，即使 `.pipeline_state.json` 标记了 1200 页 completed，对应的输出文件不存在
4. Resume 逻辑检查 `is_page_completed()` 时既看 state 又看文件存在性，发现文件缺失后 re-extract

**时间损失**:
- 首次运行: 1200/1756 页后 timeout（~30 分钟）
- 二次运行（`--no-resume` 误用）: 又被 timeout（~30 分钟）
- 第三次运行（nohup resume）: 成功完成（~40 分钟）
- 总计: ~100 分钟 vs 正常 ~40 分钟

**建议修复**:
1. **增量落盘**: Phase B 每完成 N 页即写入中间结果文件，而非等全部完成后一次性落盘
2. **CLI `--daemon` 模式**: 支持将管线放入后台运行，通过 manifest/status 文件查询进度
3. **Resume 数据完整性**: Phase B 每页提取完成后立即写对应 .md 文件（当前是 Phase C 统一写），使 resume 可增量恢复

---

## Classification Summary

| ID | Line | Priority | Issue | Status |
|----|------|----------|-------|--------|
| S-1 | Strategy | P0 | MW category 名与 homepage categories name 不匹配，导致 64% 页面归入 misc | Open |
| S-2 | Strategy | P1 | `page_categories` 映射未接入 page_assigner（死配置） | Open |
| S-3 | Strategy | P2 | Exclude 不覆盖列表页本身 | Open |
| P-1 | Pipeline | P1 | `chrome-agent crawl` 不支持 `--output` 自定义输出目录 | Open |
| P-2 | Pipeline | P2 | Phase B 中间结果不落盘，timeout 后无法增量 resume | Open |

## Recommended Fix Order

1. **S-1** (P0): 修复 MW category → directory 映射。方案选择：
   - 方案 A: 策略侧增加 `mw_category_aliases` 字段 + 管线侧读取
   - 方案 B: 管线侧利用 Phase 0 list_page 链接结果做直接分配
2. **P-1** (P1): 为 `chrome-agent crawl` 增加 `--output` 参数
3. **S-2** (P1): 接入 `page_categories` 到 page_assigner
4. **P-2** (P2): Phase B 增量落盘
5. **S-3** (P2): Exclude 规则覆盖列表页入口

## Workaround Applied

本次爬取通过以下后处理脚本修复了 S-1 的影响：

1. 解析 `page_manifest.json`，读取每页的 `mw_categories`
2. 按优先级链（Characters > Bosses > Trinkets > Cards > ... > Items）匹配 MW category
3. 补充手动映射（Chapters 楼层名、game-versions DLC 名等）
4. 执行文件移动 + 更新 manifest
5. 重新生成目录索引

修复结果：810 页从 misc 移到正确目录，最终目录分布：

| 目录 | 页面 |
|------|------|
| items/ | 718 |
| misc/ | 300 |
| trinkets/ | 189 |
| bosses/ | 117 |
| monsters/ | 104 |
| cards/ | 64 |
| challenges/ | 45 |
| mechanics/ | 40 |
| characters/ | 35 |
| chapters/ | 32 |
| rooms/ | 22 |
| objects/ | 20 |
| transformations/ | 16 |
| modes/ | 7 |
| pickups/ | 4 |
| game-versions/ | 4 |
| meta/ | 1 |
