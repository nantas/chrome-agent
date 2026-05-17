# Proposal

## 问题定义

在 2026-05-17 对 `bindingofisaacrebirth.wiki.gg` 的两次独立验证中，发现了 **策略配置与管线执行之间的多层断层**：

### 证据 1：主 session 修复后，另一个 session 产出质量退化

主 session 经过 V1-V4 迭代 + Architecture Gate + KI Lifecycle，将 Isaac Wiki 的样本质量从 P:5 F:4 S:3 提升到 P:8 F:1 S:3，修复了 KI-5（图片链接粘连）、KI-6（Collectible ID 污染）、KI-2（S5 误报）等 6 个问题。

但另一个 session 独立运行 explore 后产出的 `outputs/20260517-eval-7samples/` 全部样本出现 KI-5、KI-6 复现，本质原因是 **agent 未能使用本 session 构建的策略驱动转换器**（`sample_converter.py` 的 `_apply_extraction()`），而是 fallback 到了裸 `markdownify`。

### 证据 2：Scrapling 优先于 API 导致 Cloudflare 阻断

虽然 Isaac Wiki 策略明确配置了 `api.platform: mediawiki` 和完整的 API 访问参数，但 `chrome-agent-cli.mjs` 的 `selectFetcher()` 函数完全缺少对 `api.platform` 的检测，导致 scrapling-get 作为默认引擎 → Cloudflare "Just a moment..." 挑战页阻断。

### 根因：三层断层

| 断层 | 位置 | 表现 |
|------|------|------|
| **引擎选择断层** | `selectFetcher()` / `runEngineFetch()` / `main.py` | 策略有 API 配置，但引擎选择只认 scrapling → Cloudflare 阻断 |
| **转换器可发现性断层** | `sample_converter.py` 无 CLI 入口、SKILL.md 无文档 | Agent 不知道用哪个工具做策略驱动转换 → fallback 到裸 markdownify |
| **工作流发现断层** | `runExplore()` 策略命中后只返元数据、SKILL.md 无转换路径 | Agent 拿到策略后不知道下一步怎么做 |

## 范围边界

### 范围内

- 修改 `selectFetcher()` 添加 `api.platform` 检测 → 返回 `"mediawiki-api"`
- 新增 `runMediawikiApiFetch()` 函数处理 API 引擎
- 为 `sample_converter.py` 添加独立 CLI 入口（`apply` / `fetch-and-apply` 子命令）
- 修改 `main.py` 的 engine 选择逻辑引用 `api_config`
- 新增 `mediawiki-api` 引擎条目到 `engine-registry.json`
- 更新 `rate-limit-api` 反爬策略的 `engine_priority`
- 在 SKILL.md 新增 "Route to sample conversion" 章节
- 在 AGENTS.md 记录 `sample_converter.py` 的用途和调用方式

### 范围外

- 不修改 `scripts/mediawiki-api-extract/pipeline/phase_b.py`（重型管线，适合全量提取，不适合样本评估）
- 不修改 Isaac Wiki 策略的 `protection_level`（独立的策略数据更新）
- 不修改 taxonomy 缺失条目（独立的策略数据更新）
- 不新增 S1-S12 检查项

## Capabilities

### New Capabilities

- `explore-strategy-pipeline-bridge`: 将策略配置（`api.platform`、`extraction.*`）下沉到管线执行层的完整桥接。包括引擎选择感知 API 平台、策略驱动的样本转换 CLI、工作流 SKILL 文档。

### Modified Capabilities

- `engine-contracts`: 引擎注册表新增 `mediawiki-api` 引擎类型，`selectFetcher()` 新增 API 平台感知的分支
- `explore-workflow`: `runExplore()` 策略命中路径扩展为支持样本转换和自检；`main.py` engine 选择引用 API 探测结果
- `site-strategy`: 策略文件的 `api.platform` 字段获得完整的管线消费链路

## Impact

- **引擎选择**: `selectFetcher()` 对 MediaWiki 平台返回 `"mediawiki-api"`，避免 scrapling 被 Cloudflare 阻断
- **样本转换**: `sample_converter.py` 成为可独立调用的工具，agent 可通过 CLI 使用策略规则转换样本
- **工作流**: SKILL.md 和 AGENTS.md 记录标准路径，agent 不再 fallback 到裸 markdownify
- **向下兼容**: 不影响非 MediaWiki 站点的 scrapling 引擎选择
- **引擎注册表**: 新增 `mediawiki-api` 作为正式引擎类型

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：见 `binding.md`
