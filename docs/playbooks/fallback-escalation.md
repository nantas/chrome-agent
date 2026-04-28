# Fallback 切换逻辑

## 触发条件

### Scrapling → chrome-devtools-mcp（诊断路径）

当 Scrapling 输出满足以下任一条件时，升到 chrome-devtools-mcp：
- **不完整**: 内容缺失关键部分，或页面渲染不完整
- **被阻断**: 返回验证页面、空白页、错误信息
- **视觉存疑**: 内容与预期差异大，需要视觉确认
- **需要诊断证据**: 需要 DOM 快照、Accessibility tree、网络请求记录、控制台日志、截图、性能分析或交互调试

### Scrapling → chrome-cdp（实时会话路径）

当以下条件满足时，切换到 repo-local chrome-cdp：
- 当前 agent session 必须在已打开的 Chrome 标签页上**立即继续操作**
- 认证状态无法通过 Scrapling 会话复用安全保持（如被重定向到登录页）
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
Scrapling 执行
  ↓ 成功 → 停止
  ↓ 失败/不完整
  ↓ 需要哪种 fallback？
  ↓
  诊断证据需要？ → chrome-devtools-mcp
  会话延续需要？ → chrome-cdp
  两者都需要？  → chrome-devtools-mcp --autoConnect
```
