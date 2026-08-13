# Verification

## 全量测试

| 套件 | 命令 | 结果 |
|------|------|------|
| Python 单元 | `.venv/bin/python -m unittest discover -s tests` | 100 tests OK |
| Python 管线遗留 | `.venv/bin/python -m unittest discover -s scripts/pipeline/tests` | 51 tests OK |
| Node fanbox | `node --test tests/fanbox-shared.test.mjs` | pass 6（不变） |
| Node runtime | `node --test tests/chrome-agent-runtime.test.mjs` | pass 9（不变） |

## spec→code 映射

### `standalone-orchestrator-delegates-to-cv4-mirror`

| spec scenario | 实现位置 | 证据 |
|---------------|----------|------|
| fetch-subcommand-applies-preprocess | `standalone.py::fetch_and_convert` HTML 分支委托 `convert_single_page`；测试 `tests/test_standalone_convert.py::TestFetchAndConvertAppliesPreprocess` | RED 阶段确认漂移（'shouldBeRemoved' 存在）→ GREEN 阶段修复（'shouldBeRemoved' 不存在） |
| reconvert-without-source-url-uses-kernel-entry | `standalone.py::reconvert_file` 无 source_url 分支改用 `convert_page_full(body, extraction_config or {})` | `tests/test_standalone_convert.py::TestReconvertFileWithoutSourceUrl::test_in_place_reconvert_applies_preprocess`（commit b590eb1，mutation-checked） |
| wikitext-mode-unchanged | `fetch_and_convert` wikitext 分支仍走 `convert_wikitext_to_markdown` | 该分支未改 |

### `convert-kernel-three-layer-interface`

| spec scenario | 实现位置 | 证据 |
|---------------|----------|------|
| cv4-class-entry-is-declared-and-proven | `00-target-architecture.md` §3.1「内核三层接口」表 + CV4-standalone 变体行；`tests/test_convert_equivalence.py::test_cv4_pipeline_mirror_matches_kernel` | 文档声明 + 等价测试守护 |

## 漂移修复证据

- **RED 证明漂移存在**（commit 前状态）：`fetch_and_convert` 直接 `convert_body(html)`，跳过 `preprocess_html`，`#catlinks` 在 `cleanup:["strip_footer"]` 配置下未被移除 → 测试 FAIL
- **GREEN 证明修复**：折叠后委托 `convert_single_page`（CV4 镜像，内部执行 `preprocess_html`），`#catlinks` 被移除 → 测试 PASS
- **代码量**：`standalone.py` 247→234 行（净 -13）；删除 ~20 行重复编排（frontmatter/card_stats/title 装配），新增 kernel 委托 + 三层接口说明

## 行为影响（可见变化）

- 有 cleanup 配置的站点，`fetch`/`reprocess`/`reconvert` 子命令的 HTML 模式输出 SHALL 开始应用配置驱动清理（此前静默失效）。方向是 bug 修复。wikitext 模式零影响。
- `reconvert_file` 无 source_url 分支：输出从「clean_html+convert（无 infobox/prepend）」变为「convert_page_full（含 infobox/preprocess/prepend）」，对齐声明的 kernel entry。

## 归档前置检查

- [x] 全量测试绿
- [x] spec→code 映射完整
- [x] 漂移修复 RED→GREEN 证据
- [x] doctor --check capabilities（归档时执行，全 `[durable] (checked)`，`next_action: none`）

## 归档后跟进（post-archive follow-up）

`/opsx-verify` 在归档后审查时标出一条 WARNING：`reconvert-without-source-url-uses-kernel-entry` scenario 有实现但无测试覆盖。该缺口由后续提交 `b590eb1` 闭合（新增 `TestReconvertFileWithoutSourceUrl`，以 `#catlinks`+`strip_footer` 为判别器，mutation check 确认退化到裸 `clean_html+convert` 会 FAIL）。本节为审计轨迹补记——归档时该 scenario 证据原为 grep，现更新为真实测试指针。
