# Proposal

## 问题定义

当前 `chrome-agent crawl` 命令严格执行策略门控：只有 `sites/strategies/registry.json` 中存在匹配 domain 的站点策略时才能执行 `crawl`。当遇到与已有策略共享同一后端平台（如 Weird Gloop MediaWiki）的新站点时，工作流出现以下断层：

1. `crawl` 因无精确域名匹配的策略而拒绝执行，返回 `failure`
2. `explore` 仅报告"策略缺口"，不会主动检测后端类型或推荐可复用策略
3. Agent 必须手动阅读 `docs/patterns/mediawiki-extraction.md`、分析已有策略、手写新策略文件、更新 registry.json
4. 整个过程没有 CLI 辅助的自动化路径，导致同后端站点的爬取准备时间冗长且依赖 agent 的记忆和推理

以 `balatrowiki.org` 为例：它与 `vampire.survivors.wiki` 共享 Weird Gloop MediaWiki 1.45.3 后端，DOM 结构、引擎偏好、清理规则 79% 以上可复用。但在 `balatrowiki.org` 策略创建之前，任何指向它的 crawl 请求都会因"缺少站点策略"而被拒绝，Agent 必须手动完成策略桥接。

本 change 的目标是在不改变 `crawl` 策略门控的前提下，通过增强 `explore` 的后端检测能力 + 新增 `bootstrap-strategy` CLI 命令，打通"检测后端 → 推荐模板 → 一键派生策略 → 正常 crawl"的闭环。

## 范围边界

**范围内：**
- `explore` 命令在无策略时的后端自动检测（HTML meta generator、关键 DOM selector、URL pattern）
- 后端指纹库 `configs/backend-signatures.json` 的创建与首条数据（Weird Gloop MediaWiki）
- `bootstrap-strategy` CLI 命令的实现（从已有策略派生新策略、字段适配、registry.json 更新）
- `site-strategy-schema` 新增可选 `backend` 字段
- `scripts/chrome-agent-cli.mjs` 的对应修改
- 相关文档更新（`sites/README.md`、`docs/patterns/mediawiki-extraction.md`）

**范围外：**
- 修改 `crawl` 的策略门控逻辑（crawl 仍然要求策略存在才能执行）
- 新增全自动静默策略创建（bootstrap 必须显式调用）
- 支持除 Weird Gloop MediaWiki 之外的其他后端（为后续扩展预留结构）
- 修改 `findStrategy()` 的域名精确匹配策略（保持现有行为）
- 清理脚本 `clean-mediawiki.sh` 的功能扩展

## Capabilities

### New Capabilities
- `explore-backend-detection`: Explore 在无匹配策略时抓取样本页并检测后端类型，推荐可复用的已有站点策略
- `bootstrap-strategy-cli`: CLI 新增 bootstrap-strategy 命令，从同后端已有策略自动派生新站点策略文件并同步更新 registry.json

### Modified Capabilities
- `site-strategy-schema`: 站点策略 YAML frontmatter 新增可选 `backend` 字段，用于标记后端家族关系

## Capabilities 待确认项

- [x] 能力清单已与用户确认（用户明确选择 A+C 组合方案：explore 自动检测 + bootstrap-strategy 命令）

## Impact

**对现有工作流的影响：**
- `explore` 在无策略时行为增强：除了报告策略缺口，还会尝试后端检测并给出可操作推荐
- 新增 `bootstrap-strategy` 命令，成为策略创建的新路径（与手动创建并行）
- `crawl` 本身不受影响，门控逻辑保持不变

**对 agent 工作流的影响：**
- 遇到同后端新站点时，agent 可以执行 `explore` → 接收后端检测结果 → 执行 `bootstrap-strategy` → 获得可用策略 → 执行 `crawl`
- 避免了 agent 手动阅读 pattern 文档、分析策略差异、手写 YAML 的过程

**对仓库文件的影响：**
- 新建 `configs/backend-signatures.json`
- 修改 `scripts/chrome-agent-cli.mjs`
- 更新 `sites/README.md`、`docs/patterns/mediawiki-extraction.md`
- 可选更新 `AGENTS.md` 策略库治理章节

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `repo://chrome-agent/openspec/specs/site-strategy-schema/spec.md`
  - `repo://chrome-agent/openspec/specs/strategy-guided-crawl/spec.md`
  - `repo://chrome-agent/docs/patterns/mediawiki-extraction.md`
  - `repo://chrome-agent/sites/README.md`
  - `repo://chrome-agent/scripts/chrome-agent-cli.mjs`
  - `repo://chrome-agent/AGENTS.md`
