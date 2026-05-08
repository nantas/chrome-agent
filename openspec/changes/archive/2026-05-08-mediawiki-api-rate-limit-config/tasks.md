# Tasks

## 1. Schema 定义（必须先完成，下游依赖）

- [x] 1.1 更新 `openspec/specs/anti-crawl-schema/spec.md`
  - 新增 `rate_limit_tiers` 字段定义（含 tier 结构、`rate_limit_config` 字段、默认值语义）
  - 验证方式：对比 `specs/anti-crawl-schema/spec.md` 中 ADDED Requirements 的字段列表，确认 schema 文档完整覆盖

- [x] 1.2 更新 `openspec/specs/site-strategy-schema/spec.md`
  - 在 `api` 块下新增 `rate_limit` 字段定义（含 `tier`、`concurrency`、`batch_delay_ms`、`retry` 子结构）
  - 定义四层覆盖优先级（CLI → Site Strategy → Anti-Crawl tier → Code defaults）
  - 验证方式：对比 `specs/site-strategy-schema/spec.md` 中 ADDED Requirements 的 scenario 列表，确认所有覆盖场景被描述

- [x] 1.3 更新 `openspec/specs/mediawiki-api-extraction/spec.md`
  - 更新 Phase B rate limit 章节，移除硬编码值描述
  - 新增 Rate Limit 配置解析 requirement（四层覆盖、配置对象传递语义）
  - 更新 Concurrency and rate limiting requirement（批次延迟、429 退避、jitter 公式）
  - 验证方式：搜索原 spec 中 "200ms"、"default: 5" 等硬编码文本，确认已替换为策略驱动描述

## 2. Anti-Crawl 策略扩展

- [x] 2.1 扩展 `sites/anti-crawl/rate-limit-api.md`
  - 在 frontmatter 中新增 `rate_limit_tiers`（`default`、`strict`、`very-strict`）
  - 扩展 `detection.http.status_codes` 包含 `429`
  - body 新增 MediaWiki API HTTP 429 场景描述（区别于浏览器 `TypeError: Failed to fetch`）
  - 验证方式：`yaml.safe_load` 读取 frontmatter，确认 `rate_limit_tiers.default` 和 `rate_limit_tiers.strict` 可解析

- [x] 2.2 更新 `sites/anti-crawl/registry.json`
  - 更新 `rate-limit-api` 条目的 `detection_summary`，反映 HTTP 429 检测信号
  - 验证方式：JSON 语法校验通过

## 3. Site Strategy 应用

- [x] 3.1 更新 `sites/strategies/slaythespire.wiki.gg/strategy.md`
  - `anti_crawl_refs` 追加 `rate-limit-api`
  - 新增 `api.rate_limit` 块（`tier: strict`，本地覆盖 `batch_delay_ms: 800`、`retry.max_retries: 5`、`retry.backoff_multiplier: 2.5`）
  - 验证方式：与 `specs/site-strategy-schema/spec.md` 中 "Site strategy 引用 anti-crawl tier 并本地覆盖" scenario 逐项对比

- [x] 3.2 更新 `sites/strategies/registry.json`
  - 同步 `slaythespire.wiki.gg` 条目的 `anti_crawl_refs`
  - 验证方式：JSON 语法校验通过，条目字段与 strategy.md frontmatter 一致

## 4. Pipeline 重构（核心实现）

- [x] 4.1 重构 `scripts/mediawiki-api-extract/__main__.py`
  - `--concurrency` 默认值改为 `None`（表示"使用策略配置"）
  - 新增可选 CLI 参数：`--batch-delay-ms`、`--max-retries`、`--backoff-multiplier`、`--jitter`
  - 验证方式：`python -m scripts.mediawiki-api-extract --help` 输出包含新增参数

- [x] 4.2 重构 `scripts/mediawiki-api-extract/pipeline.py`
  - 新增 `RateLimitConfig` dataclass（或等效结构）
  - 新增 `resolve_rate_limit_config(strategy, cli_args, anti_crawl_strategies)` 函数，实现四层覆盖逻辑
  - `run_pipeline` 中调用配置解析，将结果传递给 `ApiClient` 和 `run_phase_b`
  - 移除 `args.concurrency` 的直接透传，改用解析后的配置
  - 验证方式：单元测试或最小脚本——给定模拟 strategy + CLI args，验证 resolved config 符合四层优先级

- [x] 4.3 重构 `scripts/mediawiki-api-extract/client.py`
  - `ApiClient.__init__` 接受 `rate_limit_config` 对象
  - `_request` 使用配置中的 `retry` 参数替代硬编码值
  - 补全 jitter 实现：`delay = delay * (1 + random.uniform(-0.2, 0.2))`
  - 统一 429 处理：不再硬编码 `delay *= 2.5`，而是使用配置的 `backoff_multiplier`
  - 验证方式：模拟 HTTP 429 响应，验证重试次数、退避延迟、jitter 范围符合配置

- [x] 4.4 重构 `scripts/mediawiki-api-extract/phase_b.py`
  - `run_phase_b` 签名新增 `rate_limit_config` 参数
  - `ThreadPoolExecutor(max_workers=concurrency)` 使用配置中的 `concurrency`
  - 批次延迟使用配置中的 `batch_delay_ms`（毫秒转秒：`batch_delay_ms / 1000.0`）
  - **移除硬编码 `time.sleep(0.8)`**
  - 验证方式：代码审查确认 `phase_b.py` 中无字面量 `0.8`、`0.04`、`5`（除注释外）

## 5. 决策记录与文档

- [x] 5.1 新建 `docs/decisions/2026-05-08-rate-limit-config-architecture.md`
  - Context：硬编码参数导致运行时 patch，anti-crawl 策略闲置
  - Decision：采用模型 C（Anti-Crawl 模板 + Site Strategy 引用并本地覆盖）+ 四层覆盖优先级
  - Consequences：架构统一，新增 schema 字段，pipeline 行为变更
  - 验证方式：文件存在，包含 Context/Decision/Consequences 三要素

## 6. 验证准备

- [x] 6.1 整理 spec-to-implementation 映射表

| Spec Requirement | 实现文件 | 函数/类 | 状态 |
|------------------|----------|---------|------|
| `anti-crawl-schema`: Rate Limit Tiers 参数模板 | `sites/anti-crawl/rate-limit-api.md` | frontmatter `rate_limit_tiers` | ✅ 已实现 |
| `site-strategy-schema`: API Rate Limit 配置 | `sites/strategies/slaythespire.wiki.gg/strategy.md` | frontmatter `api.rate_limit` | ✅ 已实现 |
| `site-strategy-schema`: 四层覆盖优先级 | `scripts/mediawiki-api-extract/pipeline.py` | `resolve_rate_limit_config()` | ✅ 已实现 |
| `mediawiki-api-extraction`: Rate Limit 配置解析 | `scripts/mediawiki-api-extract/pipeline.py` | `resolve_rate_limit_config()` | ✅ 已实现 |
| `mediawiki-api-extraction`: Phase B 并发控制 | `scripts/mediawiki-api-extract/phase_b.py` | `run_phase_b()` — `ThreadPoolExecutor` | ✅ 已实现 |
| `mediawiki-api-extraction`: 批次延迟 | `scripts/mediawiki-api-extract/phase_b.py` | `run_phase_b()` — `time.sleep(batch_delay_sec)` | ✅ 已实现 |
| `mediawiki-api-extraction`: 429 退避 + jitter | `scripts/mediawiki-api-extract/client.py` | `ApiClient._request()` | ✅ 已实现 |
| `mediawiki-api-extraction`: CLI 覆盖 | `scripts/mediawiki-api-extract/__main__.py` | argparse `--concurrency`, `--batch-delay-ms`, etc. | ✅ 已实现 |

- [x] 6.2 标记 writeback 目标
  - `sites/anti-crawl/rate-limit-api.md` ✅ 已更新（新增 `rate_limit_tiers` 和 HTTP 429 检测）
  - `sites/anti-crawl/registry.json` ✅ 已更新（同步 `detection_summary` 和 `sites`）
  - `sites/strategies/slaythespire.wiki.gg/strategy.md` ✅ 已更新（新增 `api.rate_limit` 配置）
  - `sites/strategies/registry.json` ✅ 已更新（同步 `anti_crawl_refs`）
  - `docs/decisions/2026-05-08-rate-limit-config-architecture.md` ✅ 已新建
