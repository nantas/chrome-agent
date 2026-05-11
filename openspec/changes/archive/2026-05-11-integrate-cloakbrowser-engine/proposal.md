# Proposal

## 问题定义

当前引擎管线在高保护页面场景存在覆盖缺口：obscura-fetch 的 stealth 模式不可用（pre-built binary 不含 stealth 特性），TLS 指纹被检测（scrapingbee.com 返回空 body），V8 在重 JS 场景超时（nowsecure.nl）。scrapling-stealthy-fetch 依赖 Playwright JS 注入 patch，检测站点可绕过且维护成本高。

CloakBrowser（CloakHQ/CloakBrowser）提供了 57 个 C++ 源码级 Chromium patch，编译到二进制中，实测通过 Cloudflare Turnstile（6-8s 自动解析）、reCAPTCHA v3（评分 0.9，服务器端验证）、TLS 指纹检测（scrapingbee.com 全量内容 140 links）等关键场景。

本 change 的目标是将 CloakBrowser 作为新的 `playwright_stealth` 类型引擎接入，替换 `scrapling-stealthy-fetch`（supersede），在 escalation chain 中定位为 rank 4，专门处理需要高级 stealth 的高保护页面。

## 范围边界

**范围内：**
- 新增 `cloakbrowser-fetch` 引擎契约（`cloakbrowser-fetch-contract` spec）
- 注册引擎到 `configs/engine-registry.json`，初始状态 `draft`
- 更新 `engine-contracts` spec 中的 escalation chain 和错误矩阵
- 更新 `fallback-escalation` playbook
- 更新 `AGENTS.md` 中的引擎选择规则
- 将 `scrapling-stealthy-fetch` 标记为 `superseded`
- 保持 `obscura-fetch`（rank 2, cdp_lightweight）不变，不替换

**范围外（v1）：**
- CloakBrowser `humanize` 模式的集成（作为后续优化）
- `cloakserve` CDP 多路复用器模式
- Docker sidecar 部署模式
- 二进制自动更新管理（由 cloakbrowser wrapper 自身处理）
- Linux Chromium 146 与 macOS Chromium 145 的差异验证（在 tasks 阶段标记为注意事项）

## Capabilities

### New Capabilities
- `cloakbrowser-fetch-contract`: CloakBrowser 引擎的行为契约，定义输入参数、输出格式、stealth 能力和已知限制

### Modified Capabilities
- `engine-registry`: 新增 `cloakbrowser-fetch` 引擎条目（`playwright_stealth` 类型），调整 `scrapling-stealthy-fetch` 状态为 `superseded`
- `engine-contracts`: 更新 escalation chain 以包含 CloakBrowser（rank 4），更新错误矩阵和选择映射
- `scrapling-stealthy-fetch-contract`: 标记为 `superseded`，引用 CloakBrowser 作为替代方案

## Capabilities 待确认项

- [x] 能力清单已确认：所有 capability ID 已确定，无待确认项

## Impact

### 正面影响

- **Cloudflare Turnstile 绕过**：当前所有引擎均无法处理的场景，CloakBrowser 可在 headless 模式下 6-8s 自动解析
- **reCAPTCHA v3 评分 0.9**：服务器端验证通过，适合高要求的反爬场景
- **TLS 指纹检测绕过**：真实 Chrome 网络栈，无 TLS 泄漏
- **源码级 stealth**：57 个 C++ patch 编译到二进制，非 JS 注入，更稳定
- **人类行为模拟**：humanize 模式对只读内容提取无影响，可安全在需要时启用
- **Playwright API 兼容**：drop-in replacement，集成成本低

### 风险

- **二进制许可证限制**：CloakBrowser binary 使用专有许可证，不可重新分发。用户需自行 `pip install cloakbrowser`
- **二进制大小**：~200MB 下载，影响首次启动和 CI/CD 管道
- **macOS Chromium 145**：macOS 平台二进制版本落后于 Linux/Windows（Chromium 146），可能有指纹差异
- **内存占用**：~443 MB（含 Playwright node 进程），远高于 obscura（~50 MB）和 scrapling-get（~0 MB）
- **nowsecure.nl 未验证**：Turnstile + GSAP 重 JS 组合在 macOS headless 模式下未自动解析，可能在 Linux Chromium 146 或 headed 模式下表现不同

### 引擎定位决策

```
管线形态（不变部分）                           新增部分
═══════════════════════                    ═══════════════════
scrapling-get (rank 1, http)
    │
obscura-fetch (rank 2, cdp_lightweight)   ← 保留，不替换
    │
scrapling-fetch (rank 3, playwright)
    │
scrapling-stealthy-fetch (rank 4)          → superseded 由 CloakBrowser 替代
    │
CloakBrowser (rank 4, playwright_stealth)  ← 新增
    │
chrome-devtools-mcp (rank 5, cdp_managed)
chrome-cdp (rank 6, cdp_live)
```

Obscura 的并行多 worker 模式（`obscura scrape` + `obscura-worker`）在 add-obscura-engine change 中明确排除了集成（"不实现 `obscura scrape` 并行模式的 CLI 集成"），当前工作流仅使用 obscura-fetch 的单页面模式。obscura-fetch 保留 rank 2 位置，凭借其轻量级（8-50 MB）和快速启动（1-2s）优势服务轻度动态页面。CloakBrowser 仅在需要 stealth 时启用，不替代 obscura 的轻量角色。

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - `openspec/specs/cloakbrowser-fetch-contract/spec.md`（新建）
  - `openspec/specs/engine-registry/spec.md`（修改）
  - `openspec/specs/engine-contracts/spec.md`（修改）
  - `openspec/specs/scrapling-stealthy-fetch-contract/spec.md`（标记 superseded）
  - `docs/playbooks/fallback-escalation.md`（修改）
  - `configs/engine-registry.json`（修改）
  - `AGENTS.md`（修改）
