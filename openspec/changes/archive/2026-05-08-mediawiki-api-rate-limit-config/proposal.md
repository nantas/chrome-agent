# Proposal

## 问题定义

MediaWiki API extraction pipeline（`scripts/mediawiki-api-extract/`）的请求频率控制参数（concurrency、batch delay、retry backoff）全部是硬编码常量，无法通过 site strategy 或 anti-crawl 策略配置。这导致：

1. 每次遇到不同 rate limit 阈值的站点时，必须临时 patch 代码才能执行（如 `slaythespire.wiki.gg` 被迫将 concurrency 从 5 改为 1、delay 从 40ms 改为 800ms、max_retries 从 3 改为 5）。
2. `sites/anti-crawl/rate-limit-api.md` 存在但完全不被 pipeline 利用，anti-crawl 策略体系中积累的经验无法自动生效。
3. `openspec/specs/site-strategy-schema/spec.md` 的 `api` 块缺少 `rate_limit` 配置字段，策略文件无法声明站点级别的请求频率参数。

## 范围边界

**范围内：**
- `openspec/specs/anti-crawl-schema/spec.md`：扩展可选 `rate_limit_tiers` 字段定义（模板化参数分级）
- `openspec/specs/site-strategy-schema/spec.md`：在 `api` 块下新增 `rate_limit` 字段（本地覆盖 + tier 选择）
- `openspec/specs/mediawiki-api-extraction/spec.md`：更新 Phase B rate limit 章节，定义四层配置覆盖语义
- `scripts/mediawiki-api-extract/`：重构 `__main__.py`、`pipeline.py`、`client.py`、`phase_b.py`，将硬编码参数改为策略驱动
- `sites/anti-crawl/rate-limit-api.md`：扩展为跨站点通用策略，添加 HTTP 429 检测信号和 `rate_limit_tiers`
- `sites/strategies/slaythespire.wiki.gg/strategy.md`：应用新 schema，配置实测 rate limit 参数

**范围外：**
- 不涉及 Scrapling fetch 路径的 rate limit（仅 MediaWiki API pipeline）
- 不涉及 engine-registry.json 或 engine-contracts 变更
- 不涉及 `crawl` / `fetch` / `scrape` CLI 的顶层路由逻辑

## Capabilities

### New Capabilities
（无新增能力）

### Modified Capabilities
- `site-strategy-schema`: 在 `api` 块下新增 `rate_limit` 字段（含 `tier` 引用、本地数值覆盖、retry 子结构），使站点策略能够声明 MediaWiki API 请求频率参数。
- `anti-crawl-schema`: 在 frontmatter 中新增可选 `rate_limit_tiers` 字段，支持按保护机制定义分级化的通用请求频率模板（default / strict / very_strict）。
- `mediawiki-api-extraction`: 更新 Phase B rate limit 章节，将"可配置 concurrency / delay / retry"的承诺映射到 `api.rate_limit` schema，并定义四层覆盖优先级（CLI → Site Strategy → Anti-Crawl tier → 代码安全默认值）。

## Capabilities 待确认项

- [x] 能力清单已与用户确认（模型 C：Anti-Crawl 参数模板 + Site Strategy 引用并本地覆盖）

## Impact

- **代码影响面**：4 个 pipeline 文件重构（`__main__.py`、`pipeline.py`、`client.py`、`phase_b.py`），硬编码常量全部移除。
- **策略影响面**：2 个策略文件更新（`sites/anti-crawl/rate-limit-api.md`、`sites/strategies/slaythespire.wiki.gg/strategy.md`），1 个 registry 更新。
- **规范影响面**：3 个 spec 文件扩展（anti-crawl-schema、site-strategy-schema、mediawiki-api-extraction）。
- **风险**：pipeline 重构后需在新站点爬取时验证（用户已声明会自行测试，不做回归）。

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: repo://orbitos/openspec/specs/orbitos-change-v1/spec.md
  - `project_page_ref`: repo://chrome-agent/docs/plans/2026-05-08-rate-limit-config-gap-problem-report.md
  - 回写目标详见 `binding.md` 中的 `writeback_targets`
