# Proposal

## 问题定义

`scripts/mediawiki-api-extract/` 管线当前存在以下已验证问题（详见 `reports/2026-05-08-follow-up-issues.md`）：

1. **模块不可独立使用**：`HtmlToMarkdownConverter`、`convert_wikitext_to_markdown` 等核心转换器被锁在 85KB 的 `strategies.py` 中，通过相对导入依赖 `ApiClient` 等管线内部模块，无法被外部脚本或补救流程直接 import 调用。
2. **无单页面/增量操作能力**：管线仅支持 Phase A→B→C 全量运行，对 rate-limit 失败的 7 个页面无法增量补救，只能用正则脚本临时处理，导致格式不一致。
3. **CLI 入口损坏**：`chrome-agent-cli.mjs` 使用 `spawnSync("python3", [目录路径, ...])` 而非 `-m` 模式调用，导致 `ImportError`，MediaWiki API 路径从未通过 CLI 成功运行。
4. **链接修复逻辑分散**：链接转换散布在 `strategies.py` 的多个 resolver、`phase_b.py`、`phase_c.py` 及多次独立脚本中，无法统一复用。

## 范围边界

**范围内：**
- 将 `strategies.py` 拆分为独立模块（converters/ + strategies/）
- 新增独立操作入口（单页面 fetch/convert、增量 reprocess、链接修复）
- 修复 `__main__.py` 的独立运行能力
- 修复 `chrome-agent-cli.mjs` 的调用方式
- 用已知站点（slaythespire.wiki.gg）的有限范围页面做最小回归验证

**范围外：**
- 不改变 MediaWiki API 的调用协议或返回格式
- 不新增引擎注册条目（仍是 `mediawiki-api-extract`）
- 不重构 `client.py` 的重试逻辑
- 不改变 `phase_a.py` 的 discovery 逻辑
- 不改动 `configs/engine-registry.json`

## Capabilities

### New Capabilities

- `standalone-extraction`: 独立于全量管线运行的单页面获取与转换能力，支持 HTML 和 wikitext 两种输入模式
- `incremental-reprocess`: 对指定页面列表执行增量补救处理，跳过 Phase A discovery，复用已有 manifest
- `unified-link-fixer`: 统一的输出目录链接修复能力，处理 /wiki/ 链接、双重后缀、fragment 保留等

### Modified Capabilities

- `pipeline-converters`: 将转换器（HtmlToMarkdownConverter、wikitext-to-markdown、card-stats）从 strategies.py 拆为独立可导入的 converters 子包，保持原有管线行为不变
- `pipeline-cli-entry`: 修复 __main__.py 独立运行与 chrome-agent-cli.mjs 调用方式，新增子命令路由

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

- **`scripts/mediawiki-api-extract/`**：目录结构从扁平变为 converters/ + strategies/ + pipeline/ 三层，import 路径变更
- **`scripts/chrome-agent-cli.mjs`**：L1146 附近的 API 调用方式修改
- **外部补救脚本**：可直接 `from scripts.mediawiki_api_extract.converters import HtmlToMarkdownConverter`，不再需要正则 workaround
- **既有爬取结果**：不受影响，本变更仅改变代码组织与入口，不改变输出格式

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准页：`openspec/specs/agents-governance/spec.md`、`openspec/specs/capability-contracts/spec.md`、`openspec/specs/engine-registry/spec.md`
  - 项目页：`AGENTS.md` Section 8、`docs/governance-and-capability-plan.md`
  - 回写目标：`AGENTS.md` 引擎概览表、`README.md` 能力描述
