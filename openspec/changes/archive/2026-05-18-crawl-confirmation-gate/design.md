# Design

## Context

`fix-pipeline-quality-gaps` 统一了 discovery 阶段（Phase A/0 正交于 `--discovery` 参数），修复了 `api.homepage` 自动检测和管线断裂问题。但爬取工作流仍然是原子化的：discovery → extraction → assembly 一气呵成，没有用户确认点。

本 change 在 `fix-pipeline-quality-gaps` 的基础上，将爬取工作流拆分为两阶段：discovery-only（产出 manifest + summary）→ 用户确认 → extraction-from-manifest。闸门逻辑在 SKILL 层，CLI 提供必要的两阶段执行能力。

## Goals / Non-Goals

**Goals:**
- CLI `crawl` 新增 `--discovery-only` 参数，仅执行 discovery 并产出 `discovery_summary.json`
- CLI `crawl` 新增 `--from-manifest` 参数，从已有 manifest 恢复 extraction + assembly
- CLI `crawl` 新增 `--yes` / `--exclude-category` 参数
- Python 管线 `--phase discover` 值，discovery 完成后生成 `discovery_summary.json`
- Scrapling 路径 `--discovery-only` 模式下执行首页链接发现，产出 summary（含 caveats）
- SKILL.md 新增 Crawl Confirmation Gate 章节：discovery → tree → ask_user → proceed
- AGENTS.md 新增治理规则段

**Non-Goals:**
- 不修改 `scrape` 命令
- 不修改策略文件 schema
- 不统一 `sample_converter.py` 与 `html_to_markdown.py`
- 不修改 Phase B/C 核心逻辑

## Decisions

### D1: 两阶段执行模型

**Decision**: 将 crawl 拆分为 `--discovery-only`（Phase 1）和 `--from-manifest`（Phase 2）两种模式，由 SKILL 编排两阶段之间的确认闸门。正常 `crawl <url>`（不带任何新参数）行为完全不变。

**Rationale**: 保持向后兼容。自动化场景（`--yes`）或直接 CLI 调用不受闸门影响。闸门是 SKILL 层行为，不是 CLI 强制行为。

### D2: 共享 run directory

**Decision**: Phase 1（discovery-only）和 Phase 2（from-manifest）共享同一个 `outputs/crawl-<timestamp>-<domain>/` 目录。Phase 1 写入 `page_manifest.json` + `discovery_summary.json`，Phase 2 从同一目录读取。

**Rationale**: 简化参数传递 —— `--from-manifest` 只需传 manifest 路径，不需要传 output 目录。与现有 `--phase extract` + `--phase assemble` 分步执行的目录共享模式一致。

### D3: `--yes` 是 CLI 透传参数，闸门是 SKILL 层行为

**Decision**: CLI 接受 `--yes` 并将其写入 result JSON（`confirmation_bypassed: true`），但不改变 CLI 自身行为。SKILL 读取 `confirmation_bypassed` 决定是否触发闸门。

**Rationale**: 分离关注点。CLI 的职责是执行爬取，SKILL 的职责是编排工作流。`--yes` 是工作流层面的决策，不应影响 CLI 执行路径。

### D4: `--exclude-category` 是运行时参数，不修改策略文件

**Decision**: `--exclude-category` 仅在当前运行中过滤分类，不写回策略文件。过滤发生在 extraction 前，对 manifest 做内存过滤。

**Rationale**: 用户可能临时排除某个分类（如"今天只爬 Items"），不应污染策略文件。持久化排除应通过 strategy 编辑流程（explore → strategy update），不应通过 crawl 命令副作用实现。

### D5: Scrapling 路径的首页链接发现模式

**Decision**: `--discovery-only` 在 Scrapling 路径下执行有限发现：fetch 主页面 HTML，提取所有匹配 `links_to` selector 的链接，按 `structure.pages[].url_pattern` 分组统计。不执行递归遍历。summary 中标注 `discovery_method: "first_level_links"` 和相应 caveats。

**Rationale**: Scrapling 路径没有 API manifest 概念，无法提前知道精确页面数。首页链接发现提供最低限度的范围预估，足以支持用户确认"方向对不对"的决策。caveats 确保用户不会被不精确的数字误导。

### D6: `--max-pages` 在 extraction 阶段生效

**Decision**: `--max-pages` 仅限制 extraction 阶段提取的页面数，不影响 discovery（discovery 始终发现全量）。用户可以在确认阶段指定 `--max-pages` 来限制提取量。

**Rationale**: Discovery 需要全量数据才能呈现准确的树状图。限制应在 extraction 阶段（用户看到完整范围后决定"先爬 200 页试试"），而不是在 discovery 阶段。

### D7: `--phase discover` 集成到现有参数体系

**Decision**: `--phase` 新增 `discover` 值，与现有 `all`、`extract`、`assemble` 并列。`--discovery` 参数（`auto`|`allpages`|`homepage`）控制发现策略，与 `--phase` 正交。

**Rationale**: 与 `fix-pipeline-quality-gaps` 建立的 `--discovery` vs `--phase` 正交拆分一致。`--phase discover --discovery homepage` 语义清晰：只做发现，用首页策略。

### D8: `build_discovery_summary()` 在 orchestrator 中实现

**Decision**: 在 `orchestrate.py` 中新增 `build_discovery_summary(manifest, strategy)` 函数，discovery 完成后调用，产出 `discovery_summary.json`。

**Rationale**: orchestrator 已经拥有 manifest、strategy、rate_limit_config 等全部输入，自然是最适合生成 summary 的位置。不需要新增模块。

### D9: 树状图生成在 SKILL 层

**Decision**: CLI 产出机器可读的 `discovery_summary.json`（结构化数据），SKILL 负责将它渲染为用户可读的树状图（ASCII/emoji/Markdown）。

**Rationale**: 树状图的呈现格式（emoji、缩进、详细程度）是 agent 的呈现层决策，不应硬编码在 CLI 中。CLI 提供结构化数据，SKILL 做呈现适配。

## Risks / Migration

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `--phase discover` 值破坏现有调用脚本 | Low | Low | 新增值，不影响现有 `all`/`extract`/`assemble` 行为 |
| Scrapling 首页链接发现不准确（数量偏差大） | Medium | Low | caveats 明确标注"仅首页层级"；用户可跳过闸门直接爬取 |
| discovery 和 extraction 之间 manifest 过时 | Low | Low | 闸门确认后立即执行 extraction，间隔 < 1 分钟 |
| `--exclude-category` 与 strategy-level exclude 合并逻辑冲突 | Low | Low | 取并集（union），不会丢失任何排除项 |
| SKILL 闸门增加一次 ask_user 交互 | High | Low | `--yes` 完全绕过；这是预期行为，用户选择进入闸门即接受交互成本 |
| `build_discovery_summary()` 对 allpages 发现的分类准确性 | Medium | Medium | allpages 发现用 `target_directory` 分组，可能产生较多 misc 页面；summary 如实反映，不美化数据 |
