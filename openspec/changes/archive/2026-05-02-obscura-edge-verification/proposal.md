# Proposal

## 问题定义

`add-obscura-engine` change（2026-05-02）已完成核心实现，但对比测试阶段的两个关键维度未覆盖，导致 `obscura-fetch` 引擎仍为 `draft` 状态而无法升级为 `frozen`：

**缺口 1：并行抓取能力未验证**
- `obscura scrape` 命令依赖 `obscura-worker` 独立二进制，预编译 release 仅包含主二进制
- 需要构建 worker binary 并测试并行抓取的正确性、性能和资源隔离

**缺口 2：Stealth 模式反检测深度未充分对比**
- 初始 benchmark 仅测试了 `scrapingbee.com/blog`（含 Cloudflare 但非强挑战）
- 未针对已知强反爬站点（Cloudflare Turnstile、DataDome、PerimeterX）进行 Obscura stealth vs Scrapling stealthy-fetch 的对比
- Obscura stealth 的实际保护深度仍为 medium 置信度，阻碍 engine status 升级

## 范围边界

**范围内：**

- 构建 `obscura-worker` 二进制（通过 `cargo build --release`）
- 在 2-3 个测试 URL 上运行 `obscura scrape` 验证并行抓取功能、性能、正确性
- 选择 2-3 个已知含反爬机制的站点（含 Cloudflare Turnstile 或其他 WAF），执行 Obscura stealth vs Scrapling stealthy-fetch 的 A/B 对比
- 产出两份验证报告：`reports/2026-05-02-obscura-parallel-test.md` 和 `reports/2026-05-02-obscura-stealth-comparison.md`
- 根据验证结论，可能更新 `obscura-fetch-contract` spec 中 stealth 相关的描述边界
- 产出结论性决策记录：是否应将 `obscura-fetch` 升级为 `frozen`

**范围外：**

- 不创建新的引擎 capability
- 不修改 `engine-registry` 或 `engine-contracts` 的 spec（除非 stealth 测试暴露需要修正的边界）
- 不修改任何站点策略或反爬策略的 engine_priority
- 不修改 `chrome-agent` workflow skill 的路由逻辑

## Capabilities

本 change 为 pure verification change，不新增也不修改任何 capability。

- New Capabilities: 无（验证专用 change）
- Modified Capabilities: 无（验证专用 change）

若验证结论表明 `obscura-fetch-contract` spec 中的 stealth 或性能描述边界需要修正，将由实现 session 独立产出 spec delta。

## Capabilities 待确认项

- [x] 能力清单已与用户确认 — 本 change 为验证专用，无能力变更
- [x] 验证通过后状态：若两项验证均通过且无重大限制，可考虑将 `obscura-fetch` 的状态从 `draft` 升级为 `frozen`

## Impact

**正面影响：**

- 并行抓取验证消除 worker binary 的不确定性，为后续 batch 操作场景铺路
- Stealth 深度对比提升对 Obscura 反检测能力的信心，使 engine status 升级有据可依
- 若验证通过，可直接产出决策记录并触发 status 升级

**风险：**

- 构建 `obscura-worker` 需 Rust 工具链和 V8 编译（~5 分钟首次构建）
- Stealth 测试网站可能随时变更反爬策略，测试可重复性有限
- 若 stealth 验证发现 Obscura 在强反爬场景下性能不佳，需在 spec 中明确边界并保留 `draft` 状态

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `spec_standard_ref`: `repo://orbitos/99_系统/Harness/OpenSpec_Schema_Source/orbitos-change-v1`
  - `project_page_ref`: `repo://chrome-agent/AGENTS.md`
  - `writeback_targets`: `reports/`, `docs/decisions/`, `openspec/specs/obscura-fetch-contract/spec.md`（视验证结果）
