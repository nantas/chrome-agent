# Proposal

## 问题定义

Infobox 表格内的 wiki 内部链接缺少正确的相对路径前缀。例如 `bosses/Ultra_Greed.md` 的 Infobox 中产出 `[Ending 18](endings/index.md)` 而非 `[Ending 18](../endings/index.md)`，导致 8 条 broken links（BOI 100-page baseline）。

### 根因

`infobox.py` 的 `_extract_selectolax()` 调用 `render_inline_children_fn(value_node)` 时**未传入 `source_dir`**，导致 `HtmlToMarkdownConverter._render_inline_children()` 使用默认值 `source_dir=""`。后续 `_to_markdown_link()` 以空字符串作为 source 计算相对路径，产出 `endings/index.md` 而非 `../endings/index.md`。

调用链：
```
converter.py _render_infobox_table(node, source_dir="bosses")
  → infobox.py extract_infobox(..., source_dir 未传)
    → _extract_selectolax(..., source_dir 未接收)
      → render_inline_children_fn(value_node)           ← source_dir 丢失
        → _render_inline_children(node, source_dir="")   ← 默认空字符串
          → _to_markdown_link(href, text, source_dir="")
            → os.path.relpath("endings/index.md", "") = "endings/index.md"  ← 缺少 ../
```

正文中相同链接走 `_render_inline()` → `_render_block()` 路径，`source_dir` 正确传递，产出 `../endings/index.md`。

## 范围边界

### In scope

- `_extract_selectolax()` 接收并透传 `source_dir`
- `extract_infobox()` 签名新增 `source_dir` 参数
- `converter.py` 的 `_render_infobox_table()` 传入当前 `source_dir`

### Out of scope

- BS4 路径 (`_extract_bs4`) — explore 路径不经过 pipeline，不在此次修改范围
- `link_fixer.py` 增强 — 根因在 infobox，不需要后处理补丁
- `link-fallback-redirect-skip` change 的 scope — 独立 change

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `pipeline-converters`: Infobox 表格内的链接现在使用正确的 `source_dir` 计算相对路径

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

| 影响范围 | 变更类型 | 风险 |
|---------|---------|------|
| `scripts/lib/extraction/infobox.py` | 3 处参数透传 | 极低 — 纯签名扩展，默认值保持兼容 |
| `scripts/lib/extraction/converter.py` | 1 处调用加参数 | 极低 |
| BOI 100-page baseline | broken links 8→1（仅剩 `/wiki/Boss` 等非 manifest 页面链接） | 正向 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准：`orbitos`
  - 项目页：`openspec/specs/pipeline-converters/spec.md`, `openspec/specs/pipeline/pipeline-conversion.md`
  - 回写：`openspec/specs/pipeline-converters/spec.md`
