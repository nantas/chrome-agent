# Proposal

## 问题定义

`fix-pipeline-quality-gaps` 修复了 `api.homepage` 配置与管线断裂的技术问题，但爬取工作流仍存在一个结构性缺陷：**agent 通过 SKILL 调用 `crawl` 时，管线从 discovery 到 extraction 到 assembly 一气呵成，中间没有任何用户可见的确认点**。

实际影响：
- 对首页发现（homepage-driven）的站点，agent 在发现 18 个分类后直接进入提取阶段，用户不知道：哪些分类被发现了？各有多少页？输出目录结构长什么样？哪些被排除了？为什么有些页面落入了 `misc/`？
- 提取阶段可能耗时 20-30 分钟（如 bindingofisaacrebirth.wiki.gg 的 1,337 页）。如果用户事后发现范围或分类不对，整个抓取需要重跑。
- 对 Scrapling 管线的站点，用户对首页链接的真实分布完全没有预期，只能信任策略选择器的准确性。

需要的不是另一个技术修复，而是一个 **工作流级别的确认闸门**：在 discovery 完成后、extraction 开始前，agent 生成输出结构的树状图，让用户确认或调整范围后再执行。

## 范围边界

**范围内：**
- SKILL.md 新增 Crawl Confirmation Gate：discovery → 生成树状图 → ask_user 确认 → 执行
- CLI (`chrome-agent crawl`) 新增 `--discovery-only` 参数：仅执行 discovery，输出 manifest + discovery_summary.json
- CLI 新增 `--from-manifest <path>` 参数：跳过 discovery，从已有 manifest 恢复 extraction + assembly
- CLI 新增 `--yes` / `--no-confirm` 参数：完全绕过确认闸门（自动化场景）
- CLI 新增 `--exclude-category <name>`（可重复）参数：在 extraction 阶段过滤指定分类
- Python 管线 `--phase` 新增 `discover` 值：仅执行 discovery phase
- Python 管线在 discovery 完成后输出 `discovery_summary.json`（新 schema）
- Scrapling 管线在 `--discovery-only` 模式下执行首页链接提取，输出 `discovery_summary.json`（含 caveats 标记）
- AGENTS.md 新增「Crawl Confirmation Gate」治理规则段

**范围外：**
- 不修改 `scrape` 命令（策略无关递归爬取）
- 不修改策略文件 schema（`--exclude-category` 仅作为运行时参数，不写入策略文件）
- 不统一 `sample_converter.py` 与 `html_to_markdown.py`（后续 change 评估）
- 不修改 Phase B（extraction）和 Phase C（assembly）核心逻辑

## Capabilities

### New Capabilities

- `crawl-confirmation-gate`: SKILL 层确认闸门 —— 在 discovery 完成后生成输出结构树状图，通过 ask_user 让用户确认或调整爬取范围后，再进入 extraction + assembly
- `discovery-summary-schema`: 机器可读的 JSON schema，描述 discovery 产生的输出结构。由 CLI 的 discovery-only 模式生成，由 SKILL 消费以构建树状图。同时支持 API 管线（精确 manifest）和 Scrapling 管线（首页链接推测 + caveats）

### Modified Capabilities

- `strategy-guided-crawl`: CLI `crawl` 命令新增 `--discovery-only`、`--from-manifest`、`--yes`、`--exclude-category` 参数；Scrapling 路径新增首页链接发现模式以支持 discovery-only
- `pipeline-cli-entry`: Python 管线 `--phase` 新增 `discover` 值，对应 discovery-only 执行路径；discovery 完成后生成 `discovery_summary.json`
- `global-workflow-skill`: SKILL.md 新增 Crawl Confirmation Gate 章节，定义 discovery → tree → ask_user → proceed/adjust/cancel 工作流

## Capabilities 待确认项

- [x] 能力清单已与用户确认：explore 阶段详细讨论了范围、参数语义、两阶段执行模型，用户确认推进

## Impact

| 影响维度 | 详情 |
|---------|------|
| CLI 接口 | `crawl` 新增 4 个可选参数：`--discovery-only`、`--from-manifest`、`--yes`、`--exclude-category` |
| Python 管线 | `--phase` 新增 `discover` 值；`orchestrate.py` 新增 discovery_summary 生成逻辑 |
| Scrapling 管线 | `--discovery-only` 模式下执行首页链接提取（非全量 crawl），输出 summary 含 caveats |
| SKILL.md | 新增 Crawl Confirmation Gate 章节（~60 行），不影响现有 Agent Gate |
| AGENTS.md | 新增 Crawl Confirmation Gate 治理规则段 |
| 行为变更 | 通过 SKILL 调用 `crawl` 时默认触发确认闸门（`--yes` 可跳过）；直接 CLI 调用不受闸门影响（闸门是 SKILL 层行为） |
| 向后兼容 | `crawl <url>` 不传新参数时行为完全不变；`--phase all` 继续可用 |
| 验证目标 | `bindingofisaacrebirth.wiki.gg` homepage discovery → summary 生成 → confirmation gate 完整流程 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页：
  - `openspec/specs/global-workflow-skill/spec.md`
  - `openspec/specs/strategy-guided-crawl/spec.md`
  - `openspec/specs/pipeline-cli-entry/spec.md`
  - `openspec/specs/mediawiki-api-extraction-pipeline/spec.md`
  - `openspec/specs/homepage-driven-discovery/spec.md`
  - `openspec/specs/explore-skill-gates/spec.md`（模式参考，不修改）
- 已确认项目页：
  - `AGENTS.md`
  - `~/.agents/skills/chrome-agent/SKILL.md`
  - `skills/chrome-agent/SKILL.md`
  - `scripts/chrome-agent-cli.mjs`
  - `scripts/mediawiki-api-extract/cli.py`
  - `scripts/mediawiki-api-extract/pipeline/orchestrate.py`
