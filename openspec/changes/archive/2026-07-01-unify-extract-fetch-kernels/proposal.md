# Proposal

## 问题定义

chrome-agent 的 Extract 和 Fetch 能力各有 1-3 项 B 轴/C 轴漂移，违反 [00-target-architecture.md](../../../docs/architecture/00-target-architecture.md) §3.2-3.3 的目标架构：

### Extract: B 轴分支 + 编排逻辑不在共享内核

| # | Drift | 证据 |
|---|-------|------|
| E1 | `preprocessor.py` 的 `context` 参数分 explore/pipeline 路径 | `preprocessor.py:18,33-37` — pipeline 路径 `return html`（无操作），但 pipeline 实际调用已传入 `context="explore"`——死路径 |
| E2 | `sample_converter._apply_extraction()` 4 步编排（infobox→preprocess→convert→prepend）不在共享内核 | `sample_converter.py:126-165` — 编排逻辑重复在 explore 路径，应归入 `converter.py` |

### Fetch: .mjs 与 pipeline 重复实现

| # | Drift | 证据 |
|---|-------|------|
| F1 | `.mjs` `runMediawikiApiFetch()` spawn `standalone.py` 做单页 fetch；pipeline `fetch.py` 用 `ApiClient`+`ContentAcquisitionStrategy` 做批量 fetch——同是 MediaWiki API 调用 | `chrome-agent-cli.mjs:817-870` vs `fetch.py:16-136` |

根因：B 轴（执行路径）不应通过代码分叉表达。pipeline 有成熟的批量 fetch + 缓存 + 重试基础设施，.mjs 的 trivial wrapper 应直接复用。

## 范围边界

**包含**：
- 删除 `preprocessor.py` 的 `context` 参数（统一为 always-explore 路径）
- 将 `sample_converter._apply_extraction()` 编排逻辑移入 `converter.py.convert_page_full()`
- `sample_converter.py` 改为调用 `convert_page_full()`
- `.mjs` `runMediawikiApiFetch()` → 改为调 pipeline `fetch.py`（或 shared API client）
- 更新相关测试

**不包含**：
- 修改 `converter.py` 核心转换逻辑（仅加编排入口）
- 修改 `infobox.py` 提取逻辑
- 修改 `preprocessor.py` 的 6 步清理逻辑（仅删 context 分支）

## Capabilities

### Modified Capabilities

- `extract-kernel`: 删除 `preprocessor` context 分支 + 新增 `convert_page_full` 共享编排入口
- `fetch-kernel`: .mjs mediawiki-api fetch 路径统一到 pipeline fetch.py

## Impact

| 受影响的文件 | 变更类型 |
|-------------|---------|
| `scripts/lib/extraction/preprocessor.py` | 删除 `context` 参数 |
| `scripts/lib/extraction/converter.py` | 新增 `convert_page_full()` |
| `scripts/explore/sample_converter.py` | 改为调用 `convert_page_full()` |
| `scripts/chrome-agent-cli.mjs` | `runMediawikiApiFetch()` → 调 pipeline |
| `scripts/pipeline/pipeline/phases/convert.py` | 调用方去除 `context=...` |
| `tests/` | 更新与新增测试 |

## 关联绑定

- 关联 binding: [binding.md](./binding.md)
