# Handoff: darkestdungeon.wiki.gg DD2 采集 — 管线缺陷问题汇总

## Context

| Field | Value |
|-------|-------|
| Command | `crawl`（`--from-manifest`）/ `fetch` / `explore` |
| Target | https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_II_Wiki |
| Timestamp | 2026-10-03 |
| Repo ref | env:CHROME_AGENT_REPO |
| Strategy | `sites/strategies/darkestdungeon.wiki.gg/strategy.md`（本次已修订：扩展 DD2 范围 + 6 DD2 回归样本，13/13 site-samples 通过） |
| Crawl run（缺陷现场） | `outputs/20261003T105901-crawl-darkestdungeon-wiki-gg-wiki-darkest-dungeon-ii-wiki/` |
| 质量报告（crawl 管线，6/6 FAIL） | `outputs/dd2-sample-staging/quality-report.json` |
| 质量报告（策略提取管线，验证基准） | `outputs/dd2-sample-staging/quality-report-apply-pipeline.json` |
| 策略提取样本产物 | `outputs/dd2-sample-staging/converted/*.md`（6 份） |
| 采样 HTML（缓存） | `sites/strategies/darkestdungeon.wiki.gg/samples/*.html.gz`（6 份 DD2） |

## Executive Summary

DD2 采样验证确认：站点策略（extraction 选择器 / cleanup / sitemap discovery）对 DD2 页面**完全可用**——策略提取管线下 6 样本章节全对齐、图像 multiset 全等、链接零缺失、表格结构校验全过，用户已确认质量达标。

但过程中暴露 **1 个 P0 管线缺陷**：`crawl --from-manifest` 的 markdown 转换**不消费已匹配策略的 extraction 规则**，产出全页转换（含皮肤 chrome）且复杂嵌套表格结构损坏。另有 3 个 self_check 检查器缺陷（S1 输入契约错配、S9 词表硬编码、S5 无源文比对）在 HTML 采集路线下产生系统性误报。本次 DD2 正式采集已按策略提取管线执行绕开 P-1；P-1 未修复前，**所有已注册策略站点使用 crawl 命令的产出质量都不可信**。

---

## Issue Catalog

### P-1: crawl 管线 markdown 转换不消费策略 extraction（P0）

**分类**: P-line (pipeline) — `crawl` 命令的 `markdown_conversion` 阶段与策略库脱节

**现象**:

对已注册策略站点（`sites/strategies/darkestdungeon.wiki.gg/strategy.md`，含 `extraction.selectors.content: .mw-parser-output`）执行：

```bash
chrome-agent crawl https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_II_Wiki \
  --from-manifest outputs/dd2-sample-staging/sample-manifest.json
```

产出 md 为**全页转换**：

1. 含皮肤 chrome：wiki.gg header logo、indie.io 广告 banner、`Special:CreateAccount` / `Special:UserLogin` 导航链接、CC/MediaWiki/Network footer badge（Tokens.md 中 `Create account` ×2）
2. 复杂嵌套表格结构损坏：`Plague Doctor (Darkest Dungeon II)` 技能卡表格拍平后单行最多 **600 列**（`assert_valid_md_tables` FAIL：block 5 列数 [7, 7, 55, 450, 159, 466, 291, 416, 309, 416, 600, …]）
3. S1-S12 自检 6/6 FAIL（S2/S9/S11 导航泄漏、S6 行偏差 81.3%、S8 章节丢失）

同一批 HTML 经策略提取路径（`sample_converter._apply_extraction` / `convert_page_full`，消费同一策略的 extraction 规则）转换：章节 7/7…45/45 全对齐、图像 multiset 全等、链接零缺失、表格校验全过（除下述检查器误报项）。

**根因**:

`scripts/lib/crawl_scrapling.mjs` 的 markdown_conversion 路径将抓取到的 `${pageSlug}.html.raw.html` 整页转 Markdown，未读取已匹配策略的 `extraction.selectors` / `cleanup` 规则。而 explore 采样管线（`scripts/explore/sample_converter.py` → `scripts/lib/extraction/converter.py convert_page_full`）消费策略。两条路径行为分叉：explore 走"策略提取"，crawl 走"通用转换"。

对比 DD1 正式产出（`outputs/dd1-final-staging/`，440 页，零 chrome 噪音、带 frontmatter）——当时产出走的也是策略提取管线而非 crawl 的通用转换，所以该缺陷一直未在正式产出中暴露，直到本次 DD2 用 `crawl --from-manifest` 首次走 crawl 管线。

**影响范围**:

所有已注册策略站点（`sites/strategies/`）使用 `chrome-agent crawl` 命令的产出。不限 darkestdungeon.wiki.gg。

**证据**:

```
outputs/dd2-sample-staging/quality-report.json                 # crawl 管线自检：6/6 overall FAIL
outputs/dd2-sample-staging/quality-report-apply-pipeline.json  # 策略提取管线：audit 全对齐
outputs/20261003T105901-crawl-.../wiki/Tokens.md               # 头部即 'Create account' 导航
outputs/20261003T105901-crawl-.../wiki/*/.md.raw.html          # 原始 HTML 伴文件（可用于修复验证）
```

**修复建议**:

crawl 的 markdown_conversion 阶段接入 `strategy_loader`：按目标域名匹配 `sites/strategies/<domain>/strategy.md`，命中且有 `extraction` 规则时改走 `convert_page_full(html, extraction)`（Python 侧共享内核已有，见 AGENTS.md §2 能力表 convert 行）。未命中策略的站点保持现有通用转换。修复后用本 handoff 附带的 6 份 `.raw.html` 作为回归输入，预期产出与 `outputs/dd2-sample-staging/converted/*.md` 一致。

---

### P-2: self_check S1 图像计数输入契约错配（P1）

**分类**: P-line (pipeline) — `scripts/explore/self_check.py` S1 检查器

**现象**:

无 MediaWiki API 输入（robots Disallow `/api.php`，wikitext 只能传空串）、HTML 来自 `/wiki/` 正文页抓取时，S1 以**全页 HTML img 计数**为期望值。wiki.gg 皮肤恒定注入 11 张 chrome 图（header logo ×1、indie.io 广告 ×3、footer badge ×7），导致 6/6 样本 S1 恒 FAIL，偏差恰好恒为 -11。

**根因**:

API 时代 `run_checks` 的 html 输入是 `action=parse` 返回的 `.mw-parser-output` 片段（天然无 chrome），S1 直接计数无偏。HTML 路线下 html 输入是整页文档，S1 未先用策略 `extraction.selectors.content` 限定范围再计数。检查器输入契约（"html = 正文片段"）在 HTML 路线下被静默打破。

**影响范围**:

所有走正文 HTML 采集路线（robots 禁 API 或站点无 API）的站点自检。S1 恒 FAIL 污染 KI 记录，掩盖真实丢图缺陷。

**证据**:

```
quality-report-apply-pipeline.json: 6 样本 S1 全部 "Expected N, found N-11"
Tokens.md.raw.html: all img=168, .mw-parser-output img=157, outside=11（全部 commons.wiki.gg/cdn.indie.io chrome）
```

**修复建议**:

S1 计数前应用策略 content 选择器限定 body；或 `run_checks` 增加 `body_html` 参数与全页 html 区分。修复后本批样本 S1 应 pass（audit `image_multiset_equal: true` 已证明零丢图）。

---

### P-3: S9 导航泄漏词表硬编码 DD1 站点语义（P2）

**分类**: P-line (pipeline) — `scripts/explore/self_check.py` `_NAV_KEYWORDS`

**现象**:

`Trinkets (Darkest Dungeon II)` 页面正文合法的相关条目链接行（第 6-8 行：`Combat Items` / `Stagecoach Items` / `Inn Items`）连续 3 行命中词表 → 误报 "navigation leakage"。

**根因**:

`_NAV_KEYWORDS = ["Achievements", "Challenges", "Characters", "Bosses", "Trinkets", "Items", "Modes", "Curses", "Objects", "Seeds", "Effects", "Endings", "Collection", "Version History", "Modding", "Music"]` 是为 DD1 站点侧边栏定制的**内容词**，不是导航结构特征。任何游戏 wiki 的正文都会高频出现 "Items"/"Bosses"/"Trinkets"。

**影响范围**:

所有游戏 wiki 站点的 S9 检查（跨站误报风险）。

**修复建议**:

词表移入策略配置（per-site `extraction.cleanup` 或独立字段），或 S9 改为检测导航结构特征（链接 href 集中指向 `Special:` / `action=` / 皮肤容器残留 class）而非正文词汇。

---

### P-4: S5 重复文本检测无源文比对（P3）

**分类**: P-line (pipeline) — `scripts/explore/self_check.py` S5 检查器

**现象**:

`Combat Mechanics (Darkest Dungeon II)` 被报 "Repeated link text"，实际命中 `of of`（"hits both of of its ranks"）、`over over`（"stress on a hero over over time"）——两处在**源 HTML 原文中逐字存在**，是 wiki 编辑笔误，转换器忠实保留。

**根因**:

S5 的重复文本正则只扫 md，未对照源 HTML。源文已有的重复（应为 note）与转换引入的重复（应为 fail）不可区分。

**影响范围**:

低频，但所有站点都可能因源文笔误产生不可消除的 FAIL。

**修复建议**:

S5 命中后对照源 HTML 文本：源文已含该重复则降级为 note/skip；仅转换引入的重复报 fail。wikitext 不可用时以 body HTML get_text 为对照源。

---

## W-line

无（本次工作流本身符合 Crawl Gate：discovery-only → 用户确认 → 采样 → 用户确认质量后才进入正式采集）。

## 2026-10-03 DD2 全量后续：新增转换器缺陷 3 项（已修复合入）

DD2 全量转换过程中发现并修复（均已带单测、样本回归 13/13、能力注册同步）：

| ID | 现场与根因 | 修复 |
|----|-----------|------|
| P-5 | `ul > big > li` 错误嵌套（wiki 源码容错渲染）导致 markdownify 丢弃整块列表：Shambler (DD2) 奖励图标 4 张丢失 | 新增 cleanup op `unwrap_list_item_wrappers`（preprocessor） |
| P-6 | 空 inline（空 a/span）与空段落（`<p><br/></p>`）打断 markdownify 块级换行状态机 | 新增 `strip_empty_inline_tags`、`strip_empty_paragraphs` |
| P-7 | `span.nowrap` 含 img 时块级元素与前文粘连成行：Fallen Templar "## Skills" 与表格首行粘连；unwrap 修复顺带恢复多页被吞行（DD2 样本 golden diff +34 行） | 新增 `unwrap_nowrap_spans` |

另为 P-2/P-3/P-4 补充新证据：全量 209 页中 S5×17/S9×21 误报在 P-7 修复后降为 S5×1/S9×0；S6 新增 colspan 表头展开口径偏差案例（Inn 页，逐表验证无内容丢失）；S8 新增列表页分组标题语义降级案例（Enemies 列表页）。

## 修复验证基准

| 资源 | 用途 |
|------|------|
| `sites/strategies/darkestdungeon.wiki.gg/samples/*.html.gz`（6 DD2） | P-1/P-2/P-3/P-4 修复的现成回归输入 |
| `outputs/dd2-sample-staging/converted/*.md` | P-1 修复后 crawl 产出的期望等价物 |
| `outputs/dd2-sample-staging/quality-report-apply-pipeline.json` | audit 通过基线（章节/图像/链接指标） |
| `python3 scripts/test_runner.py site-samples --domain darkestdungeon.wiki.gg` | 13 样本回归入口（当前全绿） |

## Suggested Next Steps

1. 在 chrome-agent 仓库按 P-line 流程为 P-1 创建 openspec change（`crawl` 消费策略 extraction），P-2/P-3/P-4 可并入同一 change 或独立小 change。
2. P-1 修复验证：对 6 份 DD2 `.raw.html` 重跑 crawl 转换，diff `outputs/dd2-sample-staging/converted/*.md`。
3. P-2 修复验证：重跑 `quality-report-apply-pipeline` 等价脚本，S1 应全部转 pass 且不引入新 FAIL。

## 2026-10-04 实施状态与归因校正

P-1～P-4 已随 `4c781e3` 归档。后续 change `fix-conversion-structure-and-audit-fidelity` 已实施并验证，当前未提交、未归档；此前“P-5～P-7 已修复合入”仅表示当时工作区已有补丁，不表示 Git 已合入。

- P-5 根因在自有共享转换器只遍历直接 li，非 markdownify；列表解包已支持深层包装并保留子列表。
- P-7 根因是 merge_tooltip_links 全局删 span 闭标签导致 DOM 失衡；已改结构操作。P-6 没有独立标题修复证据，三项 workaround 退出 DD2 策略，保留兼容实现及锚点保护。
- Inn 的 S6 差额来自 15 条短横线数据行被当成分隔线，非 colspan 缺失；现已 94/94。
- Enemies 14/3 个分组通过配置配对恢复；用户批准四项精确名称别名，保留源 id 和可见标签，不做模糊匹配。
- Lair 的 Config2fc 已按源标识记 note；批量审计显式提供来源上下文，不再把 S9 全 skip 当作验证通过。
- Python 287、Node 152、站点 13/13 通过。209 页图片 multiset 与旧产物一致，逐表网格在统一既有包装/忽略空白后 209/209 等价，未覆盖正式采集目录。
- 仍明确保留 Crypt Keeper 的合并单元格图标去重引起的 S5 重复候选，及来源/锚点映射缺口；不宣称 collection 全检查通过。细节见下列 verification。

实施与证据：[verification](../../openspec/changes/fix-conversion-structure-and-audit-fidelity/verification.md)。
