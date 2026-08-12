# Verification

## 全量测试

- `.venv/bin/python -m unittest discover -s tests` → 99 tests OK（删除 test_golden_convert 后 100→99）
- `.venv/bin/python -m unittest discover -s scripts/pipeline/tests` → 51 tests OK，无 import 错误

## 引用残留扫描

- `grep -rn "discovery_summary" scripts/ tests/ --include="*.py" --include="*.mjs"` → 仅 `discovery_summary.json` 数据字段引用（cli.mjs 内联构建的产物，行为不变）
- `grep -rn "test_golden_convert" scripts/ tests/ docs/architecture/` → 无（openspec/changes/archive/ 内为历史记录，不改）
- `html_to_markdown.py` 残留：`00-architecture-review.md` / `00-target-architecture.md` 中的引用为历史基线清单（"从基线删除" 记录），有意保留；07/08 活文档已修正为 converter.py / convert_html_to_markdown()

## spec→code 映射

| delta | 回填目标 | 状态 |
|-------|----------|------|
| convert: 等价证明指针 → test_convert_equivalence.py | `openspec/specs/convert/spec.md` | ✅ 测试存在且绿（f03376d/ac08bba） |
| pipeline-discovery: REMOVED ×3 | `openspec/specs/pipeline/pipeline-discovery.md` | ✅ 模块+测试已删除 |
| pipeline-orchestration: 依赖清单移除 discovery_summary | `openspec/specs/pipeline/pipeline-orchestration.md` | ✅ orchestrator.py 实际 import 清单一致（本就无此 import） |
