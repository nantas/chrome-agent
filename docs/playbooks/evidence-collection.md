# 证据收集方法

## 概述

根据工作流类型收集不同深度的证据。Content Retrieval 轻量验证，Platform/Page Analysis 完整收集。

## 内容提取

### 文章式提取（DOM 保序）

- Walk article body in DOM order, not innerText
- Keep real image source URLs at their original positions
- Use Markdown image syntax: `![alt](url)`
- Do not replace images with generic placeholders

## Platform/Page Analysis 证据基线

### 基本信息
- 页面标题
- 最终 URL
- 关键内容摘要
- Scrapling fetcher 路径或 fallback 路径

### 截图
- `chrome-devtools-mcp`: `take_screenshot`
- `chrome-cdp`: `scrapling_screenshot`

### 结构线索
- DOM 快照或 Accessibility tree snapshot
- 交互结果记录

## 验证基线

### Content Retrieval

最低证据要求：
- Page title and URL
- Scrapling fetcher path or explicit fallback path
- Extracted main content or precise failure reason
- One lightweight evidence point when needed

### Platform/Page Analysis（公开页面）

最低证据要求：
- Page title and URL
- One key content excerpt
- One screenshot
- One structure clue (DOM or accessibility snapshot)
- One interaction outcome if applicable

### Platform/Page Analysis（实时/认证会话）

最低证据要求：
- Explicit user-approved target page or tab
- Read-only boundary by default (unless user broadens scope)
- One authentication or session-state clue
- First-connection vs follow-up notes
- Confirmation of no unexpected reset, logout, redirect, or write-action risk
