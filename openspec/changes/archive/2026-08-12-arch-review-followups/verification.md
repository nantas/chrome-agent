# Verification

> 本 change 为回溯性记录，实现已于本 session 完成（commits `f03376d`/`ac08bba`/`42e2dcc`）。verification 复跑现有测试确认状态与 spec 一致。

## 全量测试（复跑确认）

| 套件 | 命令 | 结果 |
|------|------|------|
| Python 单元 | `.venv/bin/python -m unittest discover -s tests` | 99 tests OK |
| Python 管线遗留 | `.venv/bin/python -m unittest discover -s scripts/pipeline/tests` | 51 tests OK |
| Node fanbox | `node --test tests/fanbox-shared.test.mjs` | pass 6 / fail 0 |
| Node runtime | `node --test tests/chrome-agent-runtime.test.mjs` | pass 9 / fail 0 |

## spec→code 映射

### capability: convert — `mirror-equivalence-golden-snapshot`（MODIFIED）

| spec scenario | 实现位置 | 证据 |
|---------------|----------|------|
| cv3-explore-mirror-matches-kernel | `tests/test_convert_equivalence.py::test_cv3_explore_mirror_matches_kernel` | `_apply_extraction(HTML, RULES, set()) == convert_page_full(HTML, RULES)`，字节级 |
| cv4-pipeline-mirror-matches-kernel | `::test_cv4_pipeline_mirror_matches_kernel` | `convert_single_page` 剥离声明包装后 == `convert_page_full`，字节级 |
| cv5-generic-mirror-matches-kernel | `::test_cv5_generic_mirror_matches_kernel` | `convert_html_to_markdown(HTML, "") == convert_page_full(HTML, {})`，字节级 |
| fixture-discriminates-preprocessing | fixture 含 `#catlinks` + `RULES.cleanup=["strip_footer"]` | 突变检查（task 2.3）：模拟「CV4 跳过 preprocess」被捕获为 DIFF |
| test-never-skips | fixture 内嵌于测试文件 | 无 `.cache` 依赖；`@unittest.skipIf` 模式未被使用 |

### 永久 spec 指针（跨 change 一致性）

- `openspec/specs/convert/spec.md` 已在 `archive/2026-08-12-cleanup-post-4d-drift/` 回填为指向 `tests/test_convert_equivalence.py`（grep 计数 2：capability 架构图 + requirement scenario）
- 本 change 的 convert delta 仅新增 2 个 scenario（fixture-discriminates-preprocessing / test-never-skips）细化契约，归档时合并入永久 spec（见 task 4.3）

### 候选 6（fanbox，非能力实现记录）

| 检查 | 结果 |
|------|------|
| `scripts/lib/fanbox-shared.mjs` 存在（10 helper） | ✅ |
| 两脚本 import 共享层 | ✅ grep 计数各 1 |
| `node --check` 两脚本 + 共享层 | ✅ |
| `node --test tests/fanbox-shared.test.mjs` 6 用例 | ✅ pass 6 |
| 无残留本地 helper 定义 | ✅ task 2.9 交叉核对 |

## 行为影响

- 候选 1：纯新增测试，零运行时影响
- 候选 6：纯重构，两脚本外部行为不变（两处有意硬化已记于 design D6 + commit message：downloadCover 失败返回 "0" 而非抛异常；generateNfo dateadded 改为调用时计算）

## 归档前置检查

- [x] 全量测试绿
- [x] spec→code 映射完整
- [x] 跨 change spec 指针一致（与 cleanup-post-4d-drift）
- [ ] doctor --check capabilities（归档前补，见 task 4.3）
