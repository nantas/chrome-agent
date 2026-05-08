# MediaWiki API Pipeline 请求频率控制配置缺口

**日期**: 2026-05-08
**作者**: Pi agent（slaythespire.wiki.gg 爬取 session）
**状态**: 待处理（另 session 修复）
**关联**: `sts2-strategy-set-quality-review.md` 问题 3（API 调用量相关）

---

## 问题概述

MediaWiki API extraction pipeline 的请求频率控制（concurrency、batch delay、retry backoff）全部是硬编码常量，**无法通过 site strategy 或 anti-crawl 策略配置**。每次遇到不同 rate limit 阈值的站点时，必须临时 patch 代码才能执行。

在 `slaythespire.wiki.gg` 爬取过程中，硬编码默认值（concurrency=5, batch delay=40ms, retries=3）导致大面积 HTTP 429 rate limit 失败，被迫在运行时临时修改代码。

---

## 影响范围

- **当前影响**: slaythespire.wiki.gg 爬取被迫中断两次，1298 页中 7 页因 rate limit 失败，其余 1291 页通过临时 patch（concurrency→1, delay→800ms, retries→5）才完成
- **长期影响**: 任何 MediaWiki 站点的 API pipeline 都无法通过策略配置自适应调整请求频率，只能硬编码或运行时 patch
- **架构债务**: anti-crawl 策略体系中存在 `rate-limit-api.md`，但 MediaWiki API pipeline 完全不读取 anti-crawl 策略

---

## 根因分析（三层缺口）

### 第一层：Site Strategy Schema 缺少配置字段

`openspec/specs/site-strategy-schema/spec.md` 和实际策略文件中，`api` 块只有：

```yaml
api:
  platform: mediawiki
  base_url: "..."
  capabilities: [...]
  namespaces: [...]
  content_profile: {...}
  output: {...}
```

**缺少字段**（应新增）：
```yaml
  rate_limit:
    concurrency: 1                    # 覆盖默认 5
    batch_delay_ms: 800               # 覆盖默认 200
    retry:
      max_retries: 5                  # 覆盖默认 3
      initial_delay_sec: 1.0
      backoff_multiplier: 2.5
      max_delay_sec: 60
      jitter: true
```

### 第二层：Pipeline 实现全部硬编码

| 参数 | Spec 要求 | 实际硬编码值 | 位置 |
|------|-----------|-------------|------|
| concurrency | 默认 5，CLI 可覆盖 | `__main__.py` argparse 默认 5 | `scripts/mediawiki-api-extract/__main__.py:29` |
| batch delay | 200ms | `time.sleep(0.04)` → 运行时 patch 为 `0.8` | `scripts/mediawiki-api-extract/phase_b.py:211` |
| retry max | 3 | `max_retries=3` → 运行时 patch 为 `5` | `scripts/mediawiki-api-extract/client.py:18` |
| initial delay | 1s | `delay = 1.0` | `scripts/mediawiki-api-extract/client.py` |
| backoff | 1→2→4s | `delay *= 2` → 运行时 patch 为 `2.5` | `scripts/mediawiki-api-extract/client.py` |
| jitter | "with jitter" | **完全未实现** | — |

关键问题：**MediaWiki API pipeline 代码中没有任何地方读取 site strategy 或 anti-crawl 策略来覆盖这些值**。

### 第三层：Anti-Crawl 策略存在但未被利用

`sites/anti-crawl/rate-limit-api.md` 存在且定义了：
- `protection_type: rate_limit`
- 缓解措施（3s delay、checkpoint progress 等）

但：
1. 只绑定了 `fanbox.cc`，未被 slaythespire 引用
2. 描述的是浏览器 `fetch()` rate limit（`TypeError: Failed to fetch`），不是 MediaWiki API 的 HTTP 429
3. `scripts/mediawiki-api-extract/` 代码完全不读取 `sites/anti-crawl/` 目录

---

## 现场证据

### 第一次执行（硬编码默认值）

```
--concurrency 4（CLI 传入）
time.sleep(0.04)  # batch delay
max_retries=3
```

结果：大量 HTTP 429，150 页中 failure=59，timeout 后 pipeline 退出。

### 第二次执行（临时 patch 后）

```
--concurrency 1（手动改为 CLI 传入）
time.sleep(0.8)  # 临时 patch
delay *= 2.5     # 临时 patch
max_retries=5    # 临时 patch
```

结果：1291/1298 成功，0.5% failure rate，但耗时 ~40 分钟。

### 对比：如果策略能配置

```yaml
# slaythespire.wiki.gg/strategy.md
api:
  rate_limit:
    concurrency: 1
    batch_delay_ms: 800
    retry:
      max_retries: 5
      backoff_multiplier: 2.5
```

不需要修改任何 pipeline 代码，策略文件即定义行为。

---

## 涉及的文件

| 文件 | 角色 | 需要改动 |
|------|------|---------|
| `openspec/specs/site-strategy-schema/spec.md` | 策略 schema 真源 | 新增 `api.rate_limit` 字段定义 |
| `openspec/specs/mediawiki-api-extraction/spec.md` | pipeline 规范 | 更新 Phase B concurrency/delay/backoff 章节，说明策略覆盖机制 |
| `sites/strategies/slaythespire.wiki.gg/strategy.md` | 站点策略 | 新增 `api.rate_limit` 配置 |
| `scripts/mediawiki-api-extract/__main__.py` | CLI 入口 | 传递策略中的 rate_limit 配置到 pipeline |
| `scripts/mediawiki-api-extract/client.py` | API 客户端 | 从策略读取 retry/backoff 参数，替代硬编码 |
| `scripts/mediawiki-api-extract/phase_b.py` | Phase B 执行 | 从策略读取 concurrency/batch_delay，替代硬编码 |
| `sites/anti-crawl/rate-limit-api.md` | 反爬策略 | 扩展以覆盖 MediaWiki API 场景，或新增 `mediawiki-api-rate-limit.md` |

---

## 修复方向（待讨论）

### 方案 A：最小改动 — 仅扩展 Site Strategy api 块

在 `strategy.api` 下新增 `rate_limit` 字段，pipeline 代码中读取策略值覆盖硬编码默认值。

优点：改动范围小，不触及 anti-crawl 体系。
缺点：rate limit 逻辑仍分散在 pipeline 实现中，anti-crawl 策略仍未被利用。

### 方案 B：统一化 — Anti-Crawl 策略驱动 + Site Strategy 补充

1. 扩展 `anti-crawl-schema` 支持 API rate limit 类型
2. `mediawiki-api-extract` pipeline 启动时读取匹配的 anti-crawl 策略
3. Site strategy 的 `api.rate_limit` 作为最高优先级覆盖

优点：架构统一，anti-crawl 策略不再闲置。
缺点：改动范围大，涉及 schema、registry、pipeline 多个层面。

### 方案 C：中间路线 — 先方案 A，后方案 B

1. 先实施方案 A（site strategy 扩展），解决当前爬取阻塞
2. 在 openspec 中立项做方案 B 的标准化设计

---

## 关联问题

- `sts2-strategy-set-quality-review.md` 问题 3（图片检测策略过窄）中提到"需要评估 API 调用量增加的影响"——如果 rate limit 可配置，评估会更准确
- `docs/decisions/` 中可能需要新增一个 ADR，记录"为何将 rate limit 控制放在 site strategy 而非 anti-crawl"
