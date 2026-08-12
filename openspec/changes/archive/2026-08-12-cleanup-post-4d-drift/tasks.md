# Tasks

## T1 删除死模块与其副本测试

- [x] 删除 `scripts/pipeline/pipeline/discovery_summary.py`
- [x] 删除 `scripts/pipeline/tests/test_discovery_summary.py`
- [x] 验证：`grep -rn "discovery_summary" scripts/ tests/ --include="*.py" | grep -v "discovery_summary.json"` 无 import 残留

## T2 删除失效等价测试

- [x] 删除 `tests/test_golden_convert.py`
- [x] 验证：`tests/test_convert_equivalence.py` 3 个用例绿

## T3 文档修正

- [x] `CONTEXT.md`：删除 `html_to_markdown.py` 过期从句
- [x] `docs/architecture/01-overview.md`：目录树移除 discovery_summary.py 行

## T4 验证

- [x] `.venv/bin/python -m unittest discover -s tests` 全绿
- [x] `.venv/bin/python -m unittest discover -s scripts/pipeline/tests` 无 import 错误
- [x] 填写 verification.md（spec→code 映射）
