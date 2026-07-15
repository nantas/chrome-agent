# Design

## Context

现有 `fetch_cdp.py` 为 CDP 导航→DOM HTML 提取模式设计（输入 HTML，经过 `convert_html.py` → `converter.py`）。maker.taptap.cn 不同：API 直接返回 Markdown，不需 HTML→MD 转换。需要新的 fetch kernel 和 orchestrator 路由。

CDP 连接管理：由外层 `.mjs`（`cdp.mjs` skill）管理 WebSocket 生命周期，Python 侧接收 `CdpApiEvalFn` callback——镜像 `fetch_cdp.py` 的 `CdpExtractFn` 模式。

## Goals / Non-Goals

**Goals:**

- `fetch_cdp_api.py`：接收 `eval_fn` callback + strategy config，执行 list→content 流程，产出 `extraction_results.json`
- `orchestrator.py`：识别 `api.platform: rest` + `backend: cdp-api-bridge`，路由到新 fetch 模块
- strategy.md 重写为合法 frontmatter
- 使用当前浏览器中已打开的 maker.taptap.cn 页面完成端到端验证

**Non-Goals:**

- 不实现 CDP WebSocket 连接管理（由 `.mjs` 负责）
- 不实现通用 REST API client（token 绑定浏览器 session）
- 不实现 explore 对 REST 站点的自动探测
- 不修改 `converter.py`（rest 平台跳过 convert）

## Decisions

### D1: `CdpApiEvalFn` callback 签名

```python
CdpApiEvalFn = Callable[[str], Optional[str]]
# 输入: 完整 JS 表达式字符串（含 fetch() + 认证头）
# 输出: Runtime.evaluate result.value (JSON 字符串) 或 None
```

与 `CdpExtractFn` 模式一致——Python 侧不管理 CDP 连接，只编排业务逻辑。外层 `.mjs` 负责：
1. `cdp.mjs evalraw <target> Runtime.evaluate '{"expression":"...","awaitPromise":true,"returnByValue":true}'`
2. 解析 stdout JSON，提取 `result.value`，传给 Python

### D2: Cache key 生成

复用 `.cache/chrome-cdp/<domain>/` 目录。cache key 用文件路径的 safe 表示：

```python
safe_path = name.replace("/", "_").replace(" ", "_")
```

与 `fetch_cdp._url_to_safe_path()` 模式对齐（替换路径分隔符为 `_`）。

### D3: 缓存格式

```json
{
  "title": "design_GDD-拼词肉鸽.md",
  "name": "design/GDD-拼词肉鸽.md",
  "content": "# GDD：拼词肉鸽\n\n...",
  "fetched_at": "2026-07-15T..."
}
```

存 `content` 字段（Markdown 字符串），非 `html` 字段。因为数据不走 convert 阶段。

### D4: `cache_mod` 复用

直接 `import` `cache_mod.save_page_cache()` / `cache_mod.is_cached()`，platform 固定 `"chrome-cdp"`。`save_page_cache` 的 `raw_data` 参数传入上述字典结构。

### D5: Orchestrator 路由

在 `run_pipeline()` 的 fetch 阶段添加 backend 判断：

```python
backend = strategy.get("backend")
if backend == "cdp-api-bridge":
    # 需要外部注入 eval_fn -> 通过 args 或函数参数传入
    fetch_stats = run_fetch_cdp_api(...)
else:
    fetch_stats = run_fetch(client, ...)
```

`eval_fn` 如何传入 orchestrator？两种方案：

- **方案 A**：通过 `args` 属性（`args.cdp_eval_fn`）——需要 CLI 支持，但 CLI 是 Node.js 侧
- **方案 B**：`run_fetch_cdp_api` 作为独立函数被 `.mjs` 直接调用，不走 orchestrator 的 `run_pipeline()`

选择 **方案 B**。理由：`eval_fn` 是 CDP 实时连接，无法序列化或从 CLI args 传入。orchestrator 的 `run_pipeline()` 是批量离线管线，不适合交互式 CDP session。`fetch_cdp_api.py` 作为独立模块，由 chrome-agent skill 的工作流脚本直接 import 调用，不经过 orchestrator。

但 orchestrator 仍需要知道 rest 平台存在（validate 时不报错、convert passthrough 正确路由）。Orchestrator 只负责 convert+assemble 的 rest 路径。

### D6: Convert passthrough

对于 `api.platform: rest`，orchestrator 的 convert 阶段：

```python
if api_config.get("platform") == "rest":
    # Passthrough: read cache, write extraction_results.json directly
    results = _passthrough_convert(manifest, strategy, domain, repo_root)
else:
    results, stats = run_convert(...)
```

`_passthrough_convert` 读 `.cache/chrome-cdp/<domain>/<safe_path>.json`，取 `content` 字段，写入 `extraction_results.json`。

### D7: Strategy 验证放宽

`validate_api_config()` 当前拒绝所有非 `mediawiki` 的 platform。修改为：

```python
if api_config["platform"] == "rest":
    return None  # REST platforms skip MediaWiki validation
if api_config["platform"] != "mediawiki":
    return f"Unsupported api.platform: {api_config['platform']}"
```

### D8: 文档同步

- `03-strategy-schema.md`：追加 `api.platform: rest`、`requires_authentication`、`api.auth` 字段
- `00-target-architecture.md`：fetch 表格追加 `fetch_cdp_api.py` 行
- `configs/capability-registry.yaml`：`fetch.engines` 追加 `cdp-api-bridge`
- playbook 更新验证结果

## Risks / Migration

| 风险 | 缓解 |
|------|------|
| CDP 连接不稳定（maker 站点已知频繁 Input 操作后超时） | `eval_fn` 超时由外层 `.mjs` 处理，Python 侧只处理 None 返回值 |
| Token 过期（JWT 有时效） | 每次 `eval_fn` 调用均实时读 localStorage，不缓存 token |
| List API 返回目录条目（`mimeType: inode/directory`） | 过滤 `type == "resource_link"` 且无 `mimeType` 的条目 |
| 项目 ID 硬编码在 strategy 中 | 当前 maker.taptap.cn 单 project 场景可接受；多 project 场景后续扩展 |
