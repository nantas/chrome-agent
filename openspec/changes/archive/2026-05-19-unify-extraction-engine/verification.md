# Verification

## Change: unify-extraction-engine
## Date: 2026-05-19

### Pre-validation Checks

#### V1: field_selector 无 "tr" 依赖
- **Method**: `grep -r "field_selector" sites/strategies/`
- **Result**: 仅 `bindingofisaacrebirth.wiki.gg/strategy.md` 使用 `field_selector: "div.pi-data"`
- **Verdict**: ✅ PASS — 默认值统一为 `"div.pi-data"` 安全

#### V2: infox_renderer 仅有 1 个调用方
- **Method**: `grep -r "infox_renderer" scripts/ --include="*.py"`
- **Result**: 仅 `html_to_markdown.py` 中 1 处 import + 1 处 docstring 引用
- **Verdict**: ✅ PASS — 删除安全

### Entry Point Tests

#### V3: mediawiki-api-extract 管线入口正常
- **Command**: `python3 -m scripts.mediawiki-api-extract --help`
- **Result**: 正常输出 usage 信息
- **Verdict**: ✅ PASS

#### V4: sample_converter CLI 入口正常
- **Command**: `python3 scripts/explore/sample_converter.py apply --help`
- **Result**: 正常输出 usage 信息
- **Verdict**: ✅ PASS

#### V5: Node.js 测试通过
- **Command**: `node --test tests/chrome-agent-runtime.test.mjs`
- **Result**: 9/9 tests pass
- **Verdict**: ✅ PASS

### Functional Verification

#### V6: Explore 路径 — The Sad Onion 页面
- **Command**: `python3 scripts/explore/sample_converter.py apply --strategy ... --html ... --title "The Sad Onion" --output ...`
- **Output**: 2641 chars Markdown
- **Checks**:
  - Infobox 表格渲染 ✓（7 个字段正确提取）
  - 内容清理生效 ✓（edit links、footer 等已移除）
  - Markdown 转换正常 ✓（标题、列表、链接完整）
- **Verdict**: ✅ PASS

#### V7: Pipeline 路径 — The Sad Onion 页面
- **Method**: `HtmlToMarkdownConverter.convert_body()` with BOI extraction config
- **Output**: 2771 chars Markdown
- **Checks**:
  - Infobox 表格渲染正确 ✓（selectolax 模式 + handler callbacks）
  - `Collectible ID` 通过 `extract_cur_id` handler 正确提取值 `1` ✓
  - `Item pool` 通过 `dedup_pools` handler 正确去重 ✓
  - Handler 回调正常工作 ✓
- **Verdict**: ✅ PASS

### Zero-Residue Verification

#### V8: 无残留引用
- **Command**: `grep -r "_extract_infobox\|_apply_field_handler\|infox_renderer\|_load_extraction_rules" scripts/ --include="*.py"`
- **Result**: 仅 `lib/extraction/infobox.py` 注释中提及历史
- **Command**: `grep "def _extract_infobox\|def _apply_field_handler" scripts/explore/sample_converter.py`
- **Result**: 空（grep exit 1）
- **Verdict**: ✅ PASS

### Summary

| Check | Result |
|-------|--------|
| V1: field_selector no "tr" | ✅ PASS |
| V2: infox_renderer single caller | ✅ PASS |
| V3: Pipeline entry point | ✅ PASS |
| V4: Explore entry point | ✅ PASS |
| V5: Node.js tests | ✅ PASS |
| V6: Explore path output | ✅ PASS |
| V7: Pipeline path output | ✅ PASS |
| V8: Zero residue | ✅ PASS |

**Overall: 8/8 checks PASS**
