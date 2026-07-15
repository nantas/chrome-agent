---
domain: maker.taptap.cn
description: "TapTap 制造 — 游戏开发 IDE 文档站（React SPA + RESTful 内容 API）"
protection_level: medium
requires_authentication: true
anti_crawl_refs:
  - default
backend: cdp-api-bridge

structure:
  platform: react-spa
  rendering: client-side

api:
  platform: rest
  capabilities:
    - api_list
    - api_content
  auth:
    source: localStorage
    key: taptap_access_token
    header_format: "Bearer {token}"
  endpoints:
    list:
      url: /api/v1/docs/list
      method: GET
    content:
      url: /api/v1/docs/content
      method: GET

samples: []
---

# maker.taptap.cn — Strategy

> TapTap 制造（游戏开发 IDE）
> 更新：2026-07-15

## 站点概览

- **类型**：React SPA，客户端渲染
- **认证**：OAuth2 → localStorage `taptap_access_token` (JWT Bearer)
- **内容**：项目文档（Markdown），通过 RESTful JSON API 提供
- **反爬特征**：无（Scrapling 空 body 是 SPA 渲染特征，非反爬措施）

## 后端

```yaml
backend: cdp-api-bridge
```

Scrapling 直取返回 HTTP 200 但 body 为空（SPA）。必须通过 CDP 在浏览器页面上下文调用 API。

## API 端点

| 端点 | 方法 | 参数 | 返回 |
|------|------|------|------|
| `/api/v1/docs/list` | GET | `project_id`, `type=docs` | `{data: [{name, size, type, uri}]}` |
| `/api/v1/docs/content` | GET | `project_id`, `name`（文件路径） | 文件 Markdown 正文 |

## 提取流程

```
1. CDP Runtime.evaluate → localStorage → token
2. fetch(list API) → 文件清单
3. 过滤目标路径
4. for each file: fetch(content API) → 保存 Markdown
```

## 已知限制

- 每次 `Runtime.evaluate` 后需 `sleep(0.3s)` 避免触发限流
- Token 脱离浏览器上下文不可用（不能做独立 HTTP 请求）
- 虚拟化树组件不支持 CDP Input 点击导航

## 相关文档

- `docs/playbooks/api-backed-spa-cdp-bridge.md` — 完整实战记录
- `docs/playbooks/authenticated-sessions.md` — 已登录会话规则
