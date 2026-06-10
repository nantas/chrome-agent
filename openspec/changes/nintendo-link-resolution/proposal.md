# Proposal

## 问题定义

`developer.nintendo.com` 站点的 3 个 site sample 回归测试持续失败（`assert_links_resolved` 断言），原因是转换后的 Markdown 中残留 `../Pages/Page_*.html` 未解析链接。

根因分析：
1. `html_to_markdown()` 将 HTML 中的 `<a href="../Pages/Page_xxx.html">` 原样转为 Markdown 链接
2. `markdown_link_resolver.py` 的 `fix_all_links()` 有能力将这些链接解析为 `.md` 文件名或完整 URL，但**未被任何代码调用**
3. pipeline 的 `link_resolver.py`（`ExactTitleLinkResolver`）处理的是 MediaWiki `[[wikilink]]` 语法，不处理 HTML 遗留的相对链接

## 范围边界

**In scope**：
- 在 `html_to_markdown()` 转换后、site sample 回归检查前，集成 `markdown_link_resolver` 解析 `../Pages/Page_*.html` 链接
- 修复 3 个失败的 site sample 回归测试
- 更新 `08-tech-stack.md` §4 注明链接解析断言依赖

**Out of scope**：
- 修改 pipeline 的 `ExactTitleLinkResolver`（不同路径，不同输入格式）
- 修改 `test_assertions.py` 的断言规则（断言本身正确，问题在于转换输出质量）
- 处理其他站点的链接问题

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `link-resolution-integration`: 将 `markdown_link_resolver.fix_all_links()` 集成到 site sample 转换流程中，使 `../Pages/Page_*.html` 链接在回归测试前被正确解析

## Capabilities 待确认项

- [x] 能力清单已确认——单点修复，一个 modified capability

## Impact

| 影响面 | 说明 |
|--------|------|
| `scripts/lib/extraction/converter.py` 或 `scripts/explore/sample_converter.py` | 转换后调用 `fix_all_links()` |
| `tests/` | 新增链接解析集成测试 |
| 3 个 nintendo site sample | 从 FAIL → PASS |
| `docs/architecture/08-tech-stack.md` §4 | 更新站点样本回归描述 |

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：见 binding.md 回写目标章节
