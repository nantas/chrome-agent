# Writeback

## Source
- Change: `finish-refactor-cleanup`
- Verification: `verification.md` (2026-05-20)
- Schema: orbitos-change-v1

## Writeback Targets

### 1. `docs/plans/2026-05-19-structure-refactor-and-docs.md`

**Section**: Change 3 (拆分 orchestrator + 重命名包)
**Action**: Append completion note for deferred `html_to_markdown.py` move

```markdown
**Change 3 遗留完成 (finish-refactor-cleanup):**
- ✅ `html_to_markdown.py` 已移动到 `lib/extraction/converter.py`
- ✅ 4 个 import 方已更新：`converters/__init__.py`、`strategies/__init__.py`、`standalone.py`、`sample_converter.py`
- ✅ `architecture_gate.py` 路径引用已更新
- ⚠️ `orchestrator.py` 行数 456（目标 ≤400）：提取 helper function 会增加行数，保持现状
```

**Section**: Change 4 (重命名 Phase 文件)
**Action**: Update status and add completion note for function renames

```markdown
**Change 4 遗留完成 (finish-refactor-cleanup):**
- ✅ 5 个 phase 函数已重命名：`run_phase_0`→`run_homepage_discovery`、`run_phase_a`→`run_allpages_discovery`、`run_phase_fetch`→`run_fetch`、`run_phase_convert`→`run_convert`、`run_phase_c`→`run_assemble`
- ✅ `orchestrator.py` 中的 import 和调用已全部更新
- ✅ 全局零残留旧函数名
```

### 2. `openspec/changes/fix-pipeline-quality-gaps/`

**Action**: Update capability references to reflect new file location

- `pipeline-converters` capability: `HtmlToMarkdownConverter` now resides in `scripts/lib/extraction/converter.py`
- `mediawiki-api-extraction-pipeline` capability: phase functions renamed to align with file names

## Verification Evidence

All spec requirements verified in `verification.md`:
- ✅ `converter-location-in-lib`: File moved, old removed
- ✅ `converter-importers-updated`: All 4 importers + architecture_gate updated
- ✅ `converter-internal-imports`: Already correct from Change 2
- ✅ `phase-function-naming`: All 5 functions renamed, orchestrator updated
- ✅ `phase-naming-in-logs`: Aligned by rename
- ⚠️ `orchestrator.py` ≤ 400 lines: Best-effort (456 lines)

## No-Op Items

- `lib/extraction/infobox.py`: No changes (already correct)
- `lib/extraction/preprocessor.py`: No changes (already correct)
- `chrome-agent-cli.mjs`: No changes (out of scope)
