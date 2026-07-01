# Design

## Context

当前 Convert 能力有三份 HTML→Markdown 实现，需要归一为 `lib/extraction/converter.py`（selectolax）作为唯一共享内核。详见 [proposal.md](./proposal.md) 和 [00-target-architecture.md §3.1](../../../docs/architecture/00-target-architecture.md)。

## Goals / Non-Goals

**Goals:**
- 删除 `fandom_html_to_markdown.py`（死代码，零调用者）
- `convert_html.py`（CDP 路径）从 `html_to_markdown()` 切到 `convert_html_to_markdown()`
- 删除 `html_to_markdown.py`
- `test_runner.py` 同步切换 import
- 添加 golden snapshot 测试，验证 pipeline 和 explore 转换输出等价

**Non-Goals:**
- 不修改 `converter.py` 核心逻辑
- 不改 `chrome-agent-cli.mjs` 的 JS `htmlToMarkdown()` fallback（基础设施）
- 不改 `preprocessor.py` 的 `context` 参数（属于 `unify-extract-fetch-kernels` change）

## Decisions

### D1: 删除顺序

```
① 删 fandom_html_to_markdown.py（零依赖）
② 切 convert_html.py import → converter.py
③ 切 test_runner.py import → converter.py
④ 删 html_to_markdown.py
⑤ 添加 golden snapshot 测试
```

理由：先删无依赖的死代码，再逐一切换调用方，最后删除源文件。任何一步出错可安全回退。

### D2: converter.py 支持空 `wiki_domain`（generic HTML 路径）

`HtmlToMarkdownConverter.__init__` 当前强制要求非空 `wiki_domain` 并报 `TypeError`。这与 00-target-architecture 的 "wiki_domain 可选" 设计冲突。

需要修改 converter.py 3 处：
1. `__init__`: 将 `if not wiki_domain: raise TypeError(...)` 改为 `if wiki_domain is None: raise TypeError(...)`——允许空字符串
2. `_to_markdown_link`: 链接 absolutization 前检查 `if self.wiki_domain:`，空时跳过 host 前缀
3. `/wiki/` 路径解析: 同上前置 `if self.wiki_domain:` guard，空 domain 时保持链接原样

CDP 路径调用：`convert_html_to_markdown(html, wiki_domain="")`

```python
# Before (convert_html.py:92)
md_body = html_to_markdown(html)

# After
md_body = convert_html_to_markdown(html, wiki_domain="")
```

### D4: 次要清理

| # | 项目 | 操作 |
|---|------|------|
| 1 | `tests/lib/test_html_to_markdown.py` | 删除——测试的是即将删除的模块
| 2 | `preprocessor.py:27` docstring | 更新注释——cite 了 `html_to_markdown.clean_html()`（已不存在）
| 3 | site-samples golden 文件 | **重新生成**——regex → selectolax 内核切换后输出格式不同，`test_runner.py` 需要 `--update-golden`

### D3: Golden snapshot 测试实现

选取一个已有 cache 的页面（如 wiki.gg 的某个 sample 页面），分别走两条路径：

1. **直接调用** `convert_html_to_markdown(html)` — 等价于 explore `sample_converter.py` 路径
2. **通过 pipeline** `run_convert()` 的 `HtmlToMarkdownConverter.convert_body()` — 等价于 pipeline 路径

比较两个输出。差异即为 B 轴漂移。

测试放置：`tests/test_golden_convert.py`，使用 `unittest`。测试标记为 `@unittest.skipIf(no_cached_page, reason)` 以容忍无缓存环境。

## Risks / Migration

| 风险 | 缓解 |
|------|------|
| converter.py 空 domain 守卫改动引入新 bug | 3 处改动均为加 `if self.wiki_domain:` guard，不改现有 wiki 路径逻辑；现有 `test_table_grid.py` 仍以非空 domain 运行，覆盖不变 |
| site-samples golden 文件因引擎切换失效 | `--update-golden` 重新生成所有 golden 文件（D4-3） |
| 有其他隐藏调用者 | 删除前 `grep -r html_to_markdown scripts/` 确认只有 convert_html.py 和 test_runner.py 两个调用方 |
