# Proposal

## 问题定义

`maker.taptap.cn`（TapTap 制造）是一个 React SPA 文档站，内容通过 RESTful JSON API 提供（Bearer token 认证），但 Scrapling HTTP 无法抓取（返回空 body）。需要通过 CDP `Runtime.evaluate` 在已登录浏览器页面上下文调用后台 API 获取内容。

当前 chrome-agent 管线仅支持 `api.platform: mediawiki`，缺乏对 REST API 后端 + CDP 桥接模式的策略描述和管线执行路径。现有的 `fetch_cdp.py` 是为 CDP 导航→DOM 提取 HTML 设计的，与 CDP→API 桥接是不同的 D 轴（Input Format）：前者产出 `html_generic`，后者产出 `api_json`（直接 Markdown）。

## 范围边界

**In scope:**

- 新增 `fetch_cdp_api.py` — fetch 能力在 `pipeline(cdp-api)` 执行路径的新 kernel
  - 通过 CDP `Runtime.evaluate` 从 `localStorage` 读取 Bearer token
  - 调用 REST list API 获取文件清单
  - 逐个调用 REST content API 获取 Markdown 正文
  - 写入 `.cache/` 并产出 `extraction_results.json`（跳过 convert 阶段）
  - 接收外部传入的 `CdpApiEvalFn` callback，WebSocket 管理由外层 `.mjs` 负责
- strategy schema 扩展：新增 `api.platform: rest`、`requires_authentication: bool`、`api.auth` 字段
- `orchestrator.py` 新增 `api.platform: rest` 路由分支
- `maker.taptap.cn` 站点策略重写为合法 YAML frontmatter
- `registry.json`、`capability-registry.yaml`、相关架构文档同步更新

**Out of scope:**

- Sitemap 发现或其他自动化 discover 管线（maker 的文件清单来自 list API，在 fetch 阶段内部获取）
- CDP WebSocket 连接管理（由外层 `.mjs` / `cdp.mjs` skill 负责）
- 通用 REST API client（不抽象独立 HTTP 请求路径——token 绑定浏览器 session，脱离 CDP 即失效）
- 策略模板 scaffold 自动生成（explore 对 REST API 站点的自动化探测）
- 独立于 CDP 的认证方案（token 不可脱离浏览器上下文）

## Capabilities

### New Capabilities

- `fetch-cdp-api-kernel`: CDP Runtime.evaluate 桥接到 RESTful 内容 API。在 pipeline(cdp-api) 执行路径下，从已登录浏览器页面的 localStorage 读取 Bearer token，通过页面内 fetch() 调用 list/content API 获取文件清单和 Markdown 正文，写入缓存并产出 extraction_results.json。接收外部 `CdpApiEvalFn` callback 管理 CDP 生命周期。

### Modified Capabilities

- `strategy-schema`: 新增 `api.platform` 合法值 `rest`；新增顶层字段 `requires_authentication`（布尔，标记站点在登录门后）；新增 `api.auth` 子字段（`source`、`key`、`header_format`）用于描述 token 来源与格式。
- `pipeline-orchestration`: `validate_api_config()` 不再硬拒绝非 `mediawiki` 的 `api.platform`，增加 `rest` + `backend: cdp-api-bridge` 分支。`run_pipeline()` fetch 阶段根据 `backend` 路由到 `fetch_cdp_api`，convert 阶段对 `rest` 平台走 passthrough。

## Capabilities 待确认项

- [x] 能力清单已确认（经 grill-with-docs session 对齐）

## Impact

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/pipeline/pipeline/phases/fetch_cdp_api.py` | 新增 | CDP→REST API bridge fetch kernel |
| `scripts/pipeline/pipeline/orchestrator.py` | 修改 | `validate_api_config()` + `run_pipeline()` 分支 |
| `sites/strategies/maker.taptap.cn/strategy.md` | 重写 | 合法 YAML frontmatter |
| `sites/strategies/registry.json` | 修改 | 同步 strategy 变更 |
| `configs/capability-registry.yaml` | 修改 | 注册 `cdp-api-bridge` 引擎 |
| `docs/architecture/03-strategy-schema.md` | 修改 | 新字段定义 |
| `docs/architecture/00-target-architecture.md` | 修改 | fetch 模块追加 `fetch_cdp_api.py` |
| `docs/architecture/02-pipeline-flow.md` | 修改 | rest 平台路径 |
| `docs/playbooks/api-backed-spa-cdp-bridge.md` | 修改 | 补充验证结果 |
| `docs/playbooks/authenticated-sessions.md` | 已修改 | 已有 maker 条目 |
| `docs/playbooks/README.md` | 已修改 | 已有索引 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页: `fetch-kernel`、`strategy-schema`、`pipeline-orchestration`、`pipeline-fetch`
- 已确认项目页: `00-target-architecture.md`、`02-pipeline-flow.md`、`03-strategy-schema.md`
- 已确认回写目标: 归档时回填 delta specs，同步上述项目页面
