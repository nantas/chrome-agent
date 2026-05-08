# ADR: Rate Limit 配置架构 — Anti-Crawl 模板 + Site Strategy 覆盖

**日期**: 2026-05-08
**作者**: Pi agent
**状态**: 已采纳
**关联**: `mediawiki-api-rate-limit-config` openspec change

## Context

MediaWiki API extraction pipeline（`scripts/mediawiki-api-extract/`）的请求频率控制参数全部是硬编码常量：

- `concurrency=5`（后 patch 为 1）
- `batch_delay=40ms`（后 patch 为 800ms）
- `max_retries=3`（后 patch 为 5）
- `backoff_multiplier=2`（后 patch 为 2.5）
- `jitter` 完全未实现

在 `slaythespire.wiki.gg` 爬取过程中，硬编码默认值导致大面积 HTTP 429 失败，被迫在运行时临时修改代码。同时，`sites/anti-crawl/rate-limit-api.md` 策略存在但完全不被 pipeline 利用，anti-crawl 策略体系中积累的经验无法自动生效。

问题报告提出了三种方案：
- **方案 A**（最小改动）：仅扩展 Site Strategy `api` 块
- **方案 B**（统一化）：Anti-Crawl 策略驱动 + Site Strategy 补充
- **方案 C**（中间路线）：先 A 后 B

## Decision

采纳**模型 C 的变体**：Anti-Crawl 策略定义分级参数模板（`rate_limit_tiers`），Site Strategy 引用 tier 并提供本地数值覆盖，CLI 参数作为最高优先级运行时覆盖。

### 四层覆盖优先级

```
CLI 参数（最高）
    ↓
Site Strategy api.rate_limit 本地覆盖
    ↓
Anti-Crawl 策略 rate_limit_tiers[tier]
    ↓
代码安全默认值（最低）
```

### 关键设计点

1. **Anti-Crawl 策略保持按保护机制命名**：`rate-limit-api.md` 不绑定特定站点，而是描述 `rate_limit` 这一类保护机制的通用应对参数。
2. **Tier 分级提供经验默认值**：`default`（保守）、`strict`（严格）、`very-strict`（极严格），使新增站点可以快速选择合适档位。
3. **Site Strategy 只做局部覆盖**：不需要复制整个 tier，只需覆盖实测需要调整的值（如 `slaythespire.wiki.gg` 只覆盖 `batch_delay_ms` 和 `retry.backoff_multiplier`）。
4. **代码默认值改为保守值**：`concurrency=1`, `batch_delay_ms=1000`，确保未配置策略时不会触发 rate limit。

## Consequences

### 正面

- **消除运行时 patch**：所有 MediaWiki 站点的 rate limit 参数均可通过策略文件配置。
- **Anti-Crawl 策略不再闲置**：`rate_limit_tiers` 使 anti-crawl 策略从纯文档变为可执行配置源。
- **跨站点经验可复用**：同一保护机制类型的站点可以共享 tier 模板。
- **CLI 保留调试能力**：运行时仍可通过 `--concurrency` 等参数快速调整。

### 负面 / 迁移成本

- **现有 pipeline 调用行为变更**：未传递 `--concurrency` 时默认值从 `5` 变为 `1`，未配置策略的站点爬取会变慢。需要在策略文件中显式配置高吞吐量参数。
- **新增 schema 字段增加维护负担**：3 个 spec 文件需要同步更新。
- **Tier 分级可能不够精细**：未来如果遇到介于 `strict` 和 `very-strict` 之间的站点，可能需要新增 tier 或通过 site strategy 覆盖。

### 架构债务

- 当前 `resolve_rate_limit_config` 直接从文件系统读取 anti-crawl 策略文件（通过相对路径 `../../sites/anti-crawl/`）。未来如果 anti-crawl 策略的存储或索引方式变更，需要同步更新 pipeline 的读取逻辑。
- `registry.json` 目前不索引 `rate_limit_tiers`，运行时无法通过 registry 快速判断哪些 anti-crawl 策略提供 rate limit 配置。
