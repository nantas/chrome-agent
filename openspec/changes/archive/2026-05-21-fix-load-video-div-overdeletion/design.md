# Design

## Context

`HtmlToMarkdownConverter.clean_html()`（`scripts/lib/extraction/converter.py` L260-275）在清理 YouTube oEmbed 嵌入组件时，遍历 `parser.css("div")` 并对 `text(deep=True)` 包含 "Load video" 的 div 执行 `decompose()`。由于 `selectolax` 的 `css("div")` 返回从外到内的顺序，且 `text(deep=True)` 包含所有后代节点的文本，页面根容器 `div.mw-parser-output` 因嵌套视频组件而匹配条件，导致整个页面被销毁。

当前 BOI 100 页基线测试中 20/99 页面受影响，输出 markdown 仅有 video link 提取的数行链接。

## Goals / Non-Goals

**Goals:**
- 修复 "Load video" div 清理循环，仅删除视频嵌入的叶级 UI 容器
- 保持 `extract_video_links()` 提取的视频链接正常注入到 markdown 末尾
- 确保所有 20 个受影响页面恢复完整内容输出
- 更新 validation baseline 以反映修复后的指标

**Non-Goals:**
- 不重构 clean_html 整体逻辑
- 不改变 video link 提取行为
- 不引入新依赖

## Decisions

### D1: 改用精确 CSS 选择器替代文本匹配

**选择**：将 `parser.css("div")` + `text(deep=True)` 文本匹配替换为针对已知 YouTube embed CSS 类的精确选择器。

**方案**：
```python
# Before (buggy):
for node in parser.css("div"):
    text_content = node.text(deep=True, separator=" ", strip=True)
    if text_content and "Load video" in text_content:
        node.decompose()

# After (fixed):
VIDEO_EMBED_SELECTORS = [
    "div.embedvideo-wrapper",
    "div.embedvideo-consent",
    "div.embedvideo-overlay",
    "div.embedvideo-loader",
]
for selector in VIDEO_EMBED_SELECTORS:
    for node in parser.css(selector):
        node.decompose()
```

**理由**：
- wiki.gg 的 YouTube embed HTML 结构固定为 `embedvideo-wrapper > embedvideo-consent > embedvideo-overlay > embedvideo-loader`
- 精确选择器不会误匹配祖先容器
- 无需遍历全部 div 节点，性能更优
- 不依赖文本内容匹配，不受页面语言或 UI 文案变化影响

### D2: 保留 `<figure class="embedvideo">` 容器不删除

`<figure>` 元素在 `clean_html` 中没有被 div 选择器匹配，且 converter 的 `_render_block` 对 `figure` 会降级到 `_render_inline_children`（基本无输出），无需额外处理。视频链接已由 `extract_video_links()` 在 clean_html 之前提取。

### D3: 修复后更新 validation baseline

运行 `--update-baseline` 将 empty_content 数量从 7 更新为 1（仅 `modes/index.md` 分类页为空），并更新 unavailable_images 和 broken_links 的基线值。

## Risks / Migration

- **风险**：wiki.gg 如果更改 embed HTML 结构，选择器可能失效 → 影响低（最坏情况是视频 UI 文本残留，不会丢失页面内容）
- **回归验证**：修复后重跑 `boi-100-baseline.sh` 并确认 20 个受影响页面均有实质内容输出
