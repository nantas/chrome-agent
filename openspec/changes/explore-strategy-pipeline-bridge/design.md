# Design

## Context

Isaac Wiki (`bindingofisaacrebirth.wiki.gg`) 的策略文件已配置 `api.platform: mediawiki` 和完整的 `extraction.*` 规则，但两条执行路径都无法消费这些配置：

1. **Engine selection path** (`selectFetcher()` → `runEngineFetch()`): 完全不知道 API 引擎存在，只认 scrapling
2. **Sample conversion path** (agent 行为): 不知道 `sample_converter.py` 的存在，fallback 到裸 markdownify

result: Cloudflare 阻断 scrapling + 样本质量退化到修复前状态。

## Goals / Non-Goals

**Goals:**
- `selectFetcher()` 能识别 `api.platform` 并选择 `"mediawiki-api"` 引擎
- `runEngineFetch()` 能处理 `"mediawiki-api"` fetcher
- `sample_converter.py` 能作为独立 CLI 被 agent 发现和调用
- `main.py` 引擎选择能引用 API discovery 结果
- SKILL.md 记录标准转换路径
- `rate-limit-api` 反爬策略推荐 API 引擎

**Non-Goals:**
- 不修改 `phase_b.py`（重型管线，不适合样本评估）
- 不改变非 MediaWiki 站点的引擎选择逻辑
- 不修改 Isaac Wiki 策略的业务数据（protection_level, taxonomy）

## Decisions

### Decision 1: API 引擎选择优先于所有 scrapling 检查

`selectFetcher()` 在函数的**最开头**检查 `api.platform`，命中后立即返回，不经过 `engine_preference`、`protection`、`anti_crawl` 等 scrapling 检查链。API 是比 scrapling 更优的路径，没有理由降级。

### Decision 2: Node.js 侧 API fetch 做 HTML 获取，Python 侧做转换

`runMediawikiApiFetch()` 负责 HTTP fetch（使用 Node.js 内置能力），输出 HTML 文件。Markdown 转换由 `sample_converter.py` 的 `_apply_extraction()` 处理（需要 BeautifulSoup + markdownify + 策略规则，这些在 Python 生态中）。职责边界清晰。

### Decision 3: sample_converter.py CLI 使用 `apply` / `fetch-and-apply` 子命令

`apply`: 接受已有 HTML 文件 + 策略文件 → 输出 Markdown。用于 agent 已有 HTML 的场景。
`fetch-and-apply`: 接受页面标题 + 策略文件 → API fetch + Markdown 输出。一站式。

### Decision 4: engine-registry 新增 `type: "api"` 引擎类别

区别于现有的 `http` / `cdp_lightweight` / `playwright` 类型。`api` 类型引擎不经过浏览器，直接通过 HTTP API 获取内容。

## Risks / Migration

- **风险**: Isaac Wiki 的 API 如果未来被限流或关闭，需要 fallback。当前 `selectFetcher()` 在 API 命中后不检查 scrapling fallback。缓解措施：在 strategy 中声明 `anti_crawl_refs` 含 `rate-limit-api`，由 `selectFetcher` 的未来版本评估。
- **迁移**: 已有非 MediaWiki 站点的引擎选择逻辑不变。只新增分支，不修改现有路径。
- **向下兼容**: `sample_converter.py` 的内部函数 `_apply_extraction()` 和 `_extract_infobox()` 函数签名不变。CLI 是新增的 `main()` 入口，不影响已有调用方（`convert()` 在 `main.py` 中的使用）。
