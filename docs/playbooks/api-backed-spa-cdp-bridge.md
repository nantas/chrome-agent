# API-backed SPA with Auth — CDP-to-API Bridge 实战

> 站点：maker.taptap.cn（TapTap 制造 / 游戏开发 IDE）
> 日期：2026-07-15
> 分类：playbook / site pattern
> 相关：`docs/playbooks/authenticated-sessions.md`、`docs/patterns/mediawiki-extraction.md`

## 站点特征

| 维度 | 特征 |
|------|------|
| 框架 | React SPA（`#root`，无 SSR） |
| 认证 | OAuth2 → localStorage `taptap_access_token` (JWT Bearer) |
| 内容渲染 | 客户端 JS 渲染，Scrapling 直取返回空 body |
| 文件树 | 虚拟化树组件（Radix UI + React），懒加载子节点 |
| 文档预览 | Monaco/Codex 编辑器 + Markdown 预览面板 |
| API 形态 | RESTful JSON API，Bearer 认证，CORS 受控 |

## 失败路径（已验证不可行）

### 1. Scrapling basic fetch

```bash
chrome-agent fetch <url> --format json
```

- 结果：HTTP 200，`content.md` 为 0 字节
- 原因：页面完全由 JS 渲染，Scrapling HTTP 客户端拿不到 DOM
- 即使 `--fetcher stealthy-fetch` 也被 CLI 忽略（`runFetch` 未接收 `fetcherOverride`）

### 2. CDP Input.dispatchMouseEvent 导航

- 点击虚拟化树节点的 chevron 箭头展开文件夹 → WebSocket 超时
- 原因：CDP Input 域与 React 事件系统存在兼容问题
- 替代：`row.__reactProps.onClick(syntheticEvent)` 可触发 React handler

### 3. 独立 HTTP + Bearer Token

```python
requests.get(url, headers={"Authorization": f"Bearer {token}"})
```

- 结果：401 Unauthorized 或返回空数据
- 原因：token 绑定浏览器 session（Cookie + Origin 校验），脱离浏览器上下文即失效

## 成功路径：CDP-to-API Bridge

### 核心思路

利用 CDP `Runtime.evaluate` 在浏览器页面上下文执行 JavaScript，让页面自己的 `fetch()` 携带完整认证状态调用后台 API。

### 步骤

#### 1. 连接 CDP 并 Attach Target

```python
ws = await websockets.connect("ws://localhost:9222/devtools/browser")
# Target.getTargets → 找到 maker.taptap.cn 的 page target
# Target.attachToTarget → 获取 sessionId
```

> 注意：maker.taptap.cn 的 CDP HTTP listing API（`/json`）返回 404，但 WebSocket 路径可用。

#### 2. 参数化 API 调用

通过 `Runtime.evaluate` + `awaitPromise: true` 在页面内执行异步 fetch：

```javascript
const token = localStorage.getItem('taptap_access_token');
const resp = await fetch(
  `https://maker.taptap.cn/api/v1/docs/list?project_id=${pid}&type=docs`,
  { headers: { 'Authorization': 'Bearer ' + token } }
);
return JSON.stringify(await resp.json());
```

#### 3. 关键 API 端点

| 端点 | 方法 | 参数 | 返回 |
|------|------|------|------|
| `/api/v1/docs/list` | GET | `project_id`, `type=docs`, `sort`, `order` | `{data: [{name, size, type, uri}]}` |
| `/api/v1/docs/content` | GET | `project_id`, `name`（文件路径） | 文件 Markdown 正文 |

#### 4. 批量提取模式

```
list API → 获取文件清单
  → 过滤目标路径（如 design/**/*.md）
    → 逐个调用 content API
      → 写入本地文件
```

> **速率限制**：每次 `Runtime.evaluate` 后 `sleep(0.3s)`，避免触发浏览器或 API 限流。

### 完整工作流伪代码

```python
async def extract_site_files(ws, session_id, api_base, project_id, path_prefix):
    # 1. 获取文件清单
    files = await eval_js(f'''
        fetch("{api_base}/docs/list?project_id={project_id}&type=docs", {{
            headers: {{Authorization: 'Bearer ' + localStorage.getItem('access_token')}}
        }}).then(r => r.json())
    ''')

    # 2. 过滤目标文件
    targets = [f for f in files if f['name'].startswith(path_prefix)]

    # 3. 逐个获取内容
    for f in targets:
        content = await eval_js(f'''
            fetch("{api_base}/docs/content?project_id={project_id}&name={f['name']}", {{
                headers: {{Authorization: 'Bearer ' + localStorage.getItem('access_token')}}
            }}).then(r => r.text())
        ''')
        save_to_disk(f['name'], content)
```

## 关键技术细节

### Token 发现

通过 `Runtime.evaluate` 读取：

```javascript
// 方法 1：localStorage
localStorage.getItem('taptap_access_token')

// 方法 2：Cookie（如果 httpOnly=false）
document.cookie

// 方法 3：performance API 发现端点
performance.getEntriesByType('resource')
  .filter(e => e.name.includes('api'))
  .map(e => e.name)
```

### API 端点发现

在未掌握 API 文档时：

1. **performance API**：`getEntriesByType('resource')` 获取已请求的所有 URL
2. **CDP Network 域**：`Network.enable` + `Page.reload` 抓取初始加载 API 调用
3. **试探法**：在页面上下文调用 `fetch()` 测试不同参数组合

### CDP 连接稳定性

- CDP 连接在 `Page.reload` 后可能进入不稳定状态（握手超时）
- 建议：每个批量操作建立独立 WebSocket 连接
- Maker 站点的 CDP 连接在频繁 `Input.dispatchMouseEvent` 后易超时

### React 虚拟化树导航（备选方案）

当 API 路径不可行时，可通过 React fiber 触发文件树点击：

```javascript
// 找到目标的 __reactProps.onClick 并调用
row.querySelector('.truncate').closest('[class*="group/treerow"]')
const pk = Object.keys(row).find(k => k.startsWith('__reactProps'));
row[pk].onClick(syntheticEvent);
```

## 改进建议

### chrome-agent CLI

1. **`cdp-api-bridge` 模式**：新增 fetcher，自动从页面读取 token 并调用 API
2. **`--fetcher` 传递修复**：`runFetch()` 当前不接收 `fetcherOverride`，`--fetcher stealthy-fetch` 被静默忽略
3. **SPA 检测**：`fetch` 结果 body 为空时自动提示 "可能为 SPA，尝试 CDP 模式"

### 策略模板

为 API-backed SPA 站点建议策略模板字段：

```yaml
api:
  platform: rest  # 区别于 mediawiki
  auth:
    source: localStorage  # 或 cookie / sessionStorage
    key: taptap_access_token
    header: "Bearer {token}"
  endpoints:
    list: /api/v1/docs/list
    content: /api/v1/docs/content
  content_param: name  # content API 的文件标识参数名
```

### 通用性

此模式适用于满足以下条件的站点：
- SPA 框架（React/Vue/Angular）
- Bearer token 存储在可被 JS 访问的位置（localStorage/sessionStorage/非 httpOnly Cookie）
- 后台提供 RESTful 内容 API
- Scrapling HTTP 抓取返回空内容或登录墙

## 验证结果（2026-07-15）

### list API

```bash
cdp.mjs evalraw <target> Runtime.evaluate \
  '{"expression":"fetch(\"/api/v1/docs/list?project_id=<pid>&type=docs\", "\
  "{headers: {\"Authorization\": \"Bearer \" + localStorage.getItem(\"taptap_access_token\")}})"\
  ".then(r => r.json()).then(d => JSON.stringify(d))","awaitPromise":true,"returnByValue":true}'
```

返回 56 条记录，含文件路径、大小、类型。含目录条目（`mimeType: inode/directory`），须过滤。

### content API

```bash
cdp.mjs evalraw <target> Runtime.evaluate \
  '{"expression":"fetch(\"/api/v1/docs/content?project_id=<pid>&name=design/GDD-拼词肉鸽.md\", "\
  "{headers: {\"Authorization\": \"Bearer \" + localStorage.getItem(\"taptap_access_token\")}})"\
  ".then(r => r.text())","awaitPromise":true,"returnByValue":true}'
```

返回纯 Markdown（~54KB），无需 HTML 转换。

### Pipeline 集成

通过 `fetch_cdp_api.py` kernel + `orchestrator.py` 路由实现管线化：
- `api.platform: rest` + `backend: cdp-api-bridge` 站点自动跳过 MediaWiki API probe
- fetch 阶段通过 CDP `Runtime.evaluate` 调 list/content API
- convert 阶段走 passthrough（内容已是 Markdown）
- 详见 `openspec/changes/maker-taptap-cn-cdp-api-bridge/`

### CLI 快速验证

```python
from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api
# eval_fn 由 chrome-agent-cli.mjs 通过 cdp.mjs evalraw 注入
results = run_fetch_cdp_api(eval_fn, strategy, domain, repo_root, project_id)
print(f"Fetched {len(results)} files")
```
