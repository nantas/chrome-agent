# Verification

## 验证结论

所有 14 个实现任务已完成。Schema、策略文件、Pipeline 代码均已按 specs 实现。因用户声明不做回归测试，将在新站点爬取时进行运行时验证。

## Spec-to-Implementation Coverage

| Spec Requirement | 实现文件 | 验证方式 | 状态 |
|------------------|----------|----------|------|
| `anti-crawl-schema`: Rate Limit Tiers 字段定义 | `openspec/specs/anti-crawl-schema/spec.md` | 新增 ADDED Requirements 章节，含 tier 结构、默认值语义、3 个 scenario | ✅ |
| `site-strategy-schema`: API Rate Limit 配置 | `openspec/specs/site-strategy-schema/spec.md` | 新增 `api.rate_limit` 字段定义，含四层覆盖优先级、5 个 scenario | ✅ |
| `mediawiki-api-extraction`: Rate Limit 配置解析 | `openspec/specs/mediawiki-api-extraction/spec.md` | 新增 requirement，含配置对象传递语义、2 个 scenario | ✅ |
| `mediawiki-api-extraction`: Phase B 并发与延迟 | `openspec/specs/mediawiki-api-extraction/spec.md` | 更新 Phase B 章节，移除硬编码值；新增独立 Concurrency and rate limiting requirement | ✅ |
| Anti-Crawl 策略: `rate_limit_tiers` 模板 | `sites/anti-crawl/rate-limit-api.md` | `python3 -c "yaml.safe_load(...)"` 验证 frontmatter 可解析 | ✅ |
| Anti-Crawl 策略: HTTP 429 检测 | `sites/anti-crawl/rate-limit-api.md` | `detection.http.status_codes` 包含 `429` | ✅ |
| Site Strategy: tier 引用 + 本地覆盖 | `sites/strategies/slaythespire.wiki.gg/strategy.md` | `yaml.safe_load` 验证 frontmatter 可解析；字段与 spec scenario 逐项匹配 | ✅ |
| Pipeline: CLI 参数扩展 | `scripts/mediawiki-api-extract/__main__.py` | `python3 -m scripts.mediawiki-api-extract --help` 输出确认新增 4 个参数 | ✅ |
| Pipeline: 四层覆盖逻辑 | `scripts/mediawiki-api-extract/pipeline.py` | `py_compile` 语法通过；代码审查确认覆盖顺序正确 | ✅ |
| Pipeline: `RateLimitConfig` dataclass | `scripts/mediawiki-api-extract/pipeline.py` | 代码审查确认字段完整、默认值保守 | ✅ |
| Client: 配置驱动重试 | `scripts/mediawiki-api-extract/client.py` | `py_compile` 语法通过；`_request` 使用配置参数替代硬编码 | ✅ |
| Client: jitter 实现 | `scripts/mediawiki-api-extract/client.py` | `random.uniform(-0.2, 0.2)` 已添加 | ✅ |
| Phase B: 配置驱动并发/延迟 | `scripts/mediawiki-api-extract/phase_b.py` | `py_compile` 语法通过；无硬编码 `0.8`/`0.04` 字面量 | ✅ |

## Task-to-Evidence Coverage

| Task | 证据 | 状态 |
|------|------|------|
| 1.1 更新 anti-crawl-schema spec | `openspec/specs/anti-crawl-schema/spec.md` diff | ✅ |
| 1.2 更新 site-strategy-schema spec | `openspec/specs/site-strategy-schema/spec.md` diff | ✅ |
| 1.3 更新 mediawiki-api-extraction spec | `openspec/specs/mediawiki-api-extraction/spec.md` diff | ✅ |
| 2.1 扩展 rate-limit-api.md | `sites/anti-crawl/rate-limit-api.md` diff + YAML 解析验证 | ✅ |
| 2.2 更新 anti-crawl registry.json | `sites/anti-crawl/registry.json` diff + JSON 语法校验 | ✅ |
| 3.1 更新 slaythespire strategy.md | `sites/strategies/slaythespire.wiki.gg/strategy.md` diff + YAML 解析验证 | ✅ |
| 3.2 更新 strategies registry.json | `sites/strategies/registry.json` diff + JSON 语法校验 | ✅ |
| 4.1 重构 __main__.py | `--help` 输出截图 + `py_compile` | ✅ |
| 4.2 重构 pipeline.py | `py_compile` + 代码审查 | ✅ |
| 4.3 重构 client.py | `py_compile` + 代码审查 | ✅ |
| 4.4 重构 phase_b.py | `py_compile` + `grep` 确认无硬编码 | ✅ |
| 5.1 新建 ADR | `docs/decisions/2026-05-08-rate-limit-config-architecture.md` | ✅ |
| 6.1 spec-to-implementation 映射 | 本文件 + tasks.md 映射表 | ✅ |
| 6.2 writeback 目标标记 | 本文件 writeback 清单 | ✅ |

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| Schema 变更 | `openspec/specs/anti-crawl-schema/spec.md` | 1.1, anti-crawl-schema spec |
| Schema 变更 | `openspec/specs/site-strategy-schema/spec.md` | 1.2, site-strategy-schema spec |
| Schema 变更 | `openspec/specs/mediawiki-api-extraction/spec.md` | 1.3, mediawiki-api-extraction spec |
| Anti-Crawl 策略 | `sites/anti-crawl/rate-limit-api.md` | 2.1, 2.2 |
| Site Strategy | `sites/strategies/slaythespire.wiki.gg/strategy.md` | 3.1, 3.2 |
| Pipeline CLI | `scripts/mediawiki-api-extract/__main__.py` | 4.1 |
| Pipeline 核心 | `scripts/mediawiki-api-extract/pipeline.py` | 4.2 |
| API 客户端 | `scripts/mediawiki-api-extract/client.py` | 4.3 |
| Phase B | `scripts/mediawiki-api-extract/phase_b.py` | 4.4 |
| 架构决策 | `docs/decisions/2026-05-08-rate-limit-config-architecture.md` | 5.1 |

## 缺口与阻塞项

- **运行时验证缺口**：未执行端到端 pipeline 爬取验证。用户声明将在新站点爬取时测试，本次 change 不阻塞。
- `balatrowiki.org` 等现有站点策略未添加 `api.rate_limit`，但代码安全默认值（`concurrency=1`, `batch_delay_ms=1000`）确保不会触发 rate limit，仅执行速度变慢。
