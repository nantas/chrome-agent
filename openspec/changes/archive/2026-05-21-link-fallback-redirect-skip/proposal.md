# Proposal

## 问题定义

pipeline 对 wiki 内部链接的解析存在两个 gap：

1. **Link fallback gap**：当 `LinkResolver.resolve()` 遇到不在 manifest 中的 target 时，两个实现（`ExactTitleLinkResolver`、`ShortNameLinkResolver`）均 fallback 为 `[display](slug.md)` — 一个裸 `.md` 相对路径。该路径不指向任何实际文件，`link_fixer.py` 也无法修复（manifest 中无对应条目）。对比 Fandom converter 的 `_resolve_wiki_link()` 已正确回退到原始 wiki URL。

2. **Redirect page gap**：wiki 重定向页（HTML 中包含 `<div class="redirectMsg">`）被完整 fetch 和 convert，但产出仅为 frontmatter + 空 heading。BOI 100-page baseline 中 7 个空页面里有 6 个是重定向页（Item→Items、The Shop→Shop、Epilogue→Endings 等）。convert 阶段未检测 redirect 并跳过或替换链接。

## 范围边界

### In scope

- `LinkResolver.resolve()` 的 fallback 语义变更：不在 manifest 中的 target → 原始 wiki URL
- `convert` 阶段新增 redirect 检测：识别 `redirectMsg`，跳过页面产出，不生成空文件
- `link_fixer.py` 对 redirect 源链接的后续处理（已由 resolver fallback 覆盖，无需额外处理）
- 两个 `LinkResolver` 实现（`ExactTitleLinkResolver`、`ShortNameLinkResolver`）同步修改
- `mediawiki/api.md` spec 中 `LinkResolver` 接口语义更新

### Out of scope

- Discovery 阶段通过 API `redirects` 参数预过滤（独立优化，可作为后续 change）
- `fandom_html_to_markdown.py` 的修改（已有正确的 fallback 行为）
- Manifest 构建阶段的重定向页过滤（本 change 在 convert 阶段处理，不需要修改 manifest）

## Capabilities

### New Capabilities

- `redirect-detection`: convert 阶段检测 wiki 重定向页，跳过产出并记录 redirect 映射

### Modified Capabilities

- `pipeline-converters`: 新增 redirect 检测逻辑，对 redirect 页不生成空 .md 文件
- `link-resolver-fallback`: `LinkResolver.resolve()` fallback 从裸 `.md` 路径改为原始 wiki URL

## Capabilities 待确认项

- [x] 能力清单已与用户确认

## Impact

| 影响范围 | 变更类型 | 风险 |
|---------|---------|------|
| `scripts/pipeline/strategies/link_resolver.py` | 修改两处 fallback return | 低 — 仅改变不在 manifest 中的链接行为 |
| `scripts/pipeline/pipeline/phases/convert.py` | 新增 redirect 检测 | 低 — 跳过空页面，不改变正常页面 |
| `openspec/specs/pipeline/pipeline-conversion.md` | 新增 scenario | 无 — spec 只读更新 |
| `openspec/specs/mediawiki/api.md` | 更新 LinkResolver 语义 | 无 |
| BOI 100-page baseline | empty files 7→1（仅剩 Category:Modes） | 正向 — 减少无效产出 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：
  - 标准：`orbitos` (OpenSpec Standard v0.3)
  - 项目页：`openspec/specs/pipeline/pipeline-conversion.md`, `openspec/specs/pipeline-converters/spec.md`, `openspec/specs/mediawiki/api.md`
  - 回写：上述三个 spec 文件
