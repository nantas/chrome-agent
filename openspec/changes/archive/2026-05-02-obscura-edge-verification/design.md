# Design

## Context

`add-obscura-engine` change 完成核心实现（registry/spec/playbook/decision/smoke-check）后，两个关键验证领域未覆盖：

1. **并行抓取**：`obscura scrape` 依赖独立 `obscura-worker` 二进制，预编译 release 不包含。初始 benchmark 中尝试并失败（`Error: Worker binary not found`），需手动构建后验证。
2. **Stealth 深度对比**：初始 benchmark 仅测试了 `scrapingbee.com/blog`（含 Cloudflare JS 挑战但非强 Turnstile）。初始测试显示 Obscura 117KB vs Scrapling 215KB，差异原因（tracker 加载 vs 内容截断）未确认。需要更严格的对照测试。

两份 spec 定义了参考边界：
- `obscura-fetch-contract`: Performance characteristics（≤50% of scrapling-fetch wall time）和 Stealth mode（明确限定 TLS 层伪装，不保证高级别反爬绕过）
- `engine-registry`: 现有引擎 rank 已后移，status `draft` 等待验证升级

## Goals / Non-Goals

**Goals:**

- 构建 `obscura-worker` 二进制并验证 `obscura scrape` 在 2-3 个 URL 上的并行抓取功能
- 在 2-3 个已知含反爬机制的站点上执行 Obscura stealth vs Scrapling stealthy-fetch A/B 对比
- 产出两份结构化验证报告：`reports/2026-05-02-obscura-parallel-test.md` + `reports/2026-05-02-obscura-stealth-comparison.md`
- 根据验证结论，决定是否更新 `obscura-fetch-contract` spec 中的 stealth 边界描述
- 产出决策记录，明确是否将 `obscura-fetch` 升级为 `frozen`

**Non-Goals:**

- 不修改 `engine-registry.json` 中的 rank 或 score（除非验证发现严重偏差）
- 不修改 `engine-contracts/spec.md` 中的 escalation chain
- 不修改任何站点策略或反爬策略
- 不修改 `chrome-agent` workflow skill 的路由逻辑
- 不修改 `AGENTS.md`

## Decisions

### Decision 1: Worker 构建策略

从本地克隆的 Obscura 源码构建 worker binary。仓库已克隆到 `/Volumes/Shuttle/projects/agentic/obscura`。

**构建命令**：
```bash
cd /Volumes/Shuttle/projects/agentic/obscura && cargo build --release --features stealth
```

构建产物：`target/release/obscura-worker`。将 worker binary 放到与主二进制相同目录（`$HOME/.cache/chrome-agent-obscura/bin/`）。

**时间预期**：首次 ~5 分钟（V8 快照编译），增量 ~30 秒。

### Decision 2: 并行抓取测试设计

测试 3 个不同场景的 URL，覆盖静态、动态、混合：

| URL | 类型 | 预期 |
|-----|------|------|
| `httpbin.org/html`, `quotes.toscrape.com`, `news.ycombinator.com` | 混合 | 3 URL 并行，正确 title，时间 < 最慢单次 |

**验证指标**：
- 所有 URL 成功返回（exit code 0）
- 每个 URL 的 title 正确提取
- 总时间 < 串行之和（体现并行优势）
- 无 worker 进程泄露（所有子进程正常退出）

### Decision 3: Stealth 对比测试选择

从以下已知反爬站点中选择：
- `nowsecure.nl` — 经典的 Cloudflare 挑战检测页（判断 browser agent）
- `scrapingpass.com` — 含反爬检测的测试页
- `wiki.supercombo.gg/w/Street_Fighter_6/A.K.I.` — Cloudflare 挑战页面
- `video.dmm.co.jp/av/content/?id=mkmp00718` — 重度 JS 动态页面

若以上站点不可达或行为异常，fallback 到 `scrapingbee.com/blog`（已测试过但增加深度分析）。

**优先级**：`wiki.supercombo.gg`（CF challenge）和 `video.dmm.co.jp`（JS 动态）为必测项；`nowsecure.nl` 和 `scrapingpass.com` 为补充项。

**对比矩阵**（每个站点 x 两种引擎）：

| 引擎 | 命令 |
|------|------|
| Obscura stealth | `obscura fetch <URL> --dump html --stealth` |
| Scrapling stealthy-fetch | `scrapling extract stealthy-fetch <URL> <out.html>` |

**验证指标**：
- 是否成功获取内容（vs 被挑战页截断）
- 内容完整度（字节数，预期内容是否出现）
- 执行时间
- 错误/警告日志

### Decision 4: 结论流转

验证结论决定下一步：

| 验证结果 | 动作 |
|----------|------|
| 两项验证均通过 | 产出决策记录 → 升级 `obscura-fetch` 为 `frozen` → 更新 AGENTS.md 状态 |
| 其中一项失败但有明确边界 | 更新 `obscura-fetch-contract` spec 修正描述边界 → 维持 `draft` |
| 两项均失败或发现严重限制 | 维持 `draft`，记录为已知限制，作为下一个 change 的输入 |

## Risks / Migration

### Risks

1. **Worker 构建需要 V8 编译**：首次编译 ~5 分钟，可能因依赖版本不兼容失败。
   - 缓解：使用与主二进制匹配的 tag 版本；若失败，在当前 session 中尝试 `cargo update`。

2. **反爬站点行为不稳定**：Cloudflare 挑战策略、站点内容、IP 限流可能随时间变化。
   - 缓解：在同一 session 内顺序执行 Obscura 和 Scrapling 测试，减少时间差影响；记录测试时间戳。

3. **Obscura v0.1.0 worker 可能有 bug**：并行模式未充分测试。
   - 缓解：仅测试 3 个 URL 的小规模并行，不依赖长时间运行。

### Migration

- 无数据迁移
- 无 spec 破坏性变更
- 若验证通过，仅 `configs/engine-registry.json` 中 `obscura-fetch` 的 `status` 从 `draft` → `frozen`
