# Fallback 切换逻辑

## 引擎 escalation chain（rank 顺序）

```
scrapling-get (rank 1)  ─────────────────┐
    │  静态页面 → 成功，返回              │
    │  需要 JS 渲染 → 升到 obscura-fetch  │
    ▼                                     │
obscura-fetch (rank 2)  ────────────────┤
    │  轻度动态页 → 成功，返回            │
    │  复杂 JS/SPA 失败 → 升到 fetch      │
    ▼                                     │
scrapling-fetch (rank 3)  ──────────────┤
    │  SPA/动态页 → 成功，返回             │
    │  被阻拦/challenge → 升到 stealthy   │
    ▼                                     │
scrapling-stealthy-fetch (rank 4)  ────┤
    │  高保护页面 → 成功，返回             │
    │  诊断需要 → 升到 devtools-mcp       │
    ▼                                     │
chrome-devtools-mcp (rank 5)  ──────────┤
    │  诊断证据 → 成功，返回               │
    │  需要实时会话 → 升到 chrome-cdp     │
    ▼                                     │
chrome-cdp (rank 6)  ───────────────────┘
    实时认证会话
```

## Eskalation preflight 前置条件

- 使用 `scrapling-get` / `scrapling-fetch` / `scrapling-stealthy-fetch` 前：执行 Scrapling CLI preflight。
- 使用 `obscura-fetch` 前：执行 Obscura CLI preflight。
- 使用 `chrome-devtools-mcp` 前：MCP server 需已启动（不在 preflight 范围）。
- 使用 `chrome-cdp` 前：用户需已打开 Chrome 标签页并授权。

## 触发条件

### Obscura → Scrapling fetch（JS 复杂度升级）

当 obscura-fetch 输出满足以下任一条件时，升到 scrapling-fetch：
- **超时/死锁**: V8 事件循环超时，页面未完成渲染（常见于 GSAP 等重 JS 动画库）
- **空 body**: 返回的 `<body>` 为空或仅含 skeleton 元素（TLS 检测或异步水合失败）
- **JS 错误**: 控制台出现未处理的 `TypeError` / `ReferenceError` 阻断渲染
- **内容不完整**: 缺失关键部分（如动态列表只渲染了前 N 条）

### Scrapling → chrome-devtools-mcp（诊断路径）

当 Scrapling 输出满足以下任一条件时，升到 chrome-devtools-mcp：
- **不完整**: 内容缺失关键部分，或页面渲染不完整
- **被阻断**: 返回验证页面、空白页、错误信息
- **视觉存疑**: 内容与预期差异大，需要视觉确认
- **需要诊断证据**: 需要 DOM 快照、Accessibility tree、网络请求记录、控制台日志、截图、性能分析或交互调试

### Scrapling → Obscura（在 escalation chain 中不需要显式切换）

Obscura 位于 `scrapling-get` 和 `scrapling-fetch` 之间，由 rank 2 的默认路由自动处理，不需额外切换逻辑。

### Obscura → Scrapling、chrome-devtools-mcp（实时会话路径）

当以下条件满足时，切换到 repo-local chrome-cdp：
- 当前 agent session 必须在已打开的 Chrome 标签页上**立即继续操作**
- 认证状态无法通过 Obscura 或 Scrapling 会话复用安全保持（如被重定向到登录页）
- 用户已明确批准使用当前打开的实时 Chrome 会话

### chrome-devtools-mcp ←→ chrome-cdp

不因两个工具都可用就随意切换。按需求选择：
- 需要结构化诊断（DOM/网络/性能）→ chrome-devtools-mcp
- 需要实时会话延续 → chrome-cdp

### chrome-devtools-mcp live-attach 模式

当以下条件**同时满足**时，使用 `--autoConnect` 或 `--wsEndpoint` 启动：
- 任务一开始就知道需要实时 Chrome 会话
- 仍然需要 MCP 原生的诊断能力（snapshot、DOM 检查、网络、console）

## 切换流程

```
Scrapling CLI preflight / Obscura CLI preflight
  ↓
  按 rank 选择引擎：
  rank 1: scrapling-get（成功→返回，需 JS→升 rank 2）
  rank 2: obscura-fetch（成功→返回，失败→升 rank 3）
  rank 3: scrapling-fetch（成功→返回，被拦→升 rank 4）
  rank 4: scrapling-stealthy-fetch（成功→返回，诊→升 rank 5）
  rank 5: chrome-devtools-mcp（诊断证据）
  rank 6: chrome-cdp（实时会话延续）
  ↓
  preflight 失败 → 先安装保障；仍失败则停止并报告
```
