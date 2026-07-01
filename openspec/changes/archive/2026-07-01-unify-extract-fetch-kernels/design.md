# Design

## Context

Extract 和 Fetch 能力各有 2-1 项 B 轴漂移。详见 [proposal.md](./proposal.md) 和 [00-target-architecture.md](../../../docs/architecture/00-target-architecture.md) §3.2-3.3。

## Goals / Non-Goals

**Goals:**
- 删除 `preprocessor.py` 的 `context` 参数
- 将 `_apply_extraction()` 4 步编排移到 `converter.py` 为 `convert_page_full()`
- `.mjs` MediaWiki fetch 路径统一到 pipeline `fetch.py`
- 回归全绿

**Non-Goals:**
- 不修改 `converter.py` 核心转换逻辑
- 不修改 `infobox.py`
- 不修改 pipeline orchestrator 编排
- 不修改 `standalone.py`（服务于 non-fetch 用途如 reconvert）

## Decisions

### D1: 删除 `context` 参数策略

```python
# Before
def preprocess_html(html: str, config: dict, context: str = "explore") -> str:
    if context == "explore":
        return _preprocess_explore(html, config)
    else:
        return html

# After
def preprocess_html(html: str, config: dict) -> str:
    return _preprocess_explore(html, config)
```

仅 2 个调用方需改：
- `sample_converter.py:154`: `preprocess_html(html, extraction_rules, context="explore")` → 去掉 `context=`
- `convert.py:171`: 同样去掉

### D2: `convert_page_full()` 实现

```python
# converter.py 新增
def convert_page_full(html: str, extraction_rules: dict) -> str:
    from scripts.lib.extraction.infobox import extract_infobox
    from scripts.lib.extraction.preprocessor import preprocess_html
    
    base_url = extraction_rules.get("image_handling", {}).get("base_url", "")
    wiki_domain = base_url.replace("https://", "").replace("http://", "") if base_url else ""
    
    infobox_md = extract_infobox(html, extraction_rules, wiki_domain)
    cleaned_html = preprocess_html(html, extraction_rules)
    md = _convert_html_to_markdown_helper(cleaned_html, wiki_domain, extraction_rules)
    
    if infobox_md:
        md = infobox_md + "\n\n" + md
    return md
```

`sample_converter._apply_extraction()` 改为委托调用此函数。

### D3: .mjs fetch 统一

`.mjs` `runMediawikiApiFetch()` 当前 spawn `standalone.py` 做单页 fetch。改为 spawn pipeline：

```javascript
// Before
const args = [python, "scripts/pipeline/standalone.py", "fetch", ...];
// After  
const args = [python, "-m", "scripts.pipeline", "fetch", "--page", pageTitle, ...];
```

或更简单：如果 pipeline 的 `fetch.py` 有 CLI 入口则直接用；否则在 `.mjs` 中调用 shared Python module。

## Risks / Migration

| 风险 | 缓解 |
|------|------|
| `context` 参数删除后 pipeline convert 出现双重清理 | 验证：pipeline 路径当前已传入 `context="explore"`（完全通过），删除参数后行为不变 |
| `convert_page_full()` 内 import 循环依赖 | `converter.py` 已 import `preprocessor` / `infobox`，无循环风险 |
| .mjs fetch 切换后 CLI 接口变化 | `.mjs` `runMediawikiApiFetch` 的调用方仅 `runEngineFetch`，保持返回格式 `{ok, html, ...}` 不变 |
