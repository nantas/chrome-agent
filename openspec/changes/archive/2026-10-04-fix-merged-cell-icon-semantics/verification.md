# Verification

## 验证结论

验证对象：fix-merged-cell-icon-semantics；基于 `7791dd2` 的未提交工作区；2026-10-04。行为依据为本 change 两份 delta，包含用户确认的 adjacent-exact-label 扩展。未归档、未提交，未覆盖正式 collection。

- Python 全量 295 项、Node 全量 152 项、站点样本 13/13 通过；Python 3.9 语法解析、capabilities doctor、diff 检查通过。
- 209 页缓存离线重放无输入/结构错误，S5 209 pass，failed_pages=0，overall_pass=true；未修改 self_check.py，未放宽 S5。
- 相对前置修复的 core 基线，120 页合并格副本发生预期文本变化。209/209 图片 multiset、标题、表格行列、表外内容一致，无原有链接目标丢失。逐变化行原词序列完整保留，新增词均可追溯到源合并格图片 alt/title、两项精确映射或显式占位；没有未解释差异。
- 独立审查后更新 5 个 golden：Duelist (Darkest Dungeon)、Trinkets (Darkest Dungeon)、Plague Doctor (Darkest Dungeon II)、Carrion Eater (Darkest Dungeon II)、Trinkets (Darkest Dungeon II)。图片、链接目标一致、无原词项删除、结构断言通过，其余 8 个未变。
- 转换契约 revision 7→8；真实 run_convert 测试证明旧指纹不能复用、新指纹可以复用。没有触发 C10 文件修改，无需全局同步。

## Spec-to-Implementation Coverage

| requirement/scenario | 实现 | 验证 |
| --- | --- | --- |
| merged-cell-asset-retention / crypt-keeper-colspan | `_render_cell_continuation` 在克隆上替换图标为语义文字 | test_crypt_keeper_colspan；209 页来源审计 |
| mixed-span-and-repeated-source-assets | colspan/rowspan 共用延续内容，首槽保持原图 | test_spans_filters_and_source_occurrences；nested/header/transpose 测试 |
| explicit-name-or-unknown | `_merged_icon_label` 精确映射→可靠 alt/title→占位，不推测文件名 | test_name_resolution |
| linked-icon-and-existing-label | 替代名称安全转义；同名源标签保留格式和目标 | test_link_labels_and_safe_text |
| ordinary-and-filtered-content | 沿用图片过滤和普通格渲染，不复活排除图片 | test_spans_filters_and_source_occurrences；test_nested_header_transpose_and_plain_cells |
| adjacent-exact-label | 替换前计划邻接匹配；不同目标/其他内容/换行禁止合并 | test_adjacent_exact_labels_preserve_links_and_boundaries，含清理后无图片链接的真实边界 |
| merged-cell-icon-label-map / exact-mapping、invalid-map、absent-map-and-shared-paths | schema 字段校验、配置透传、能力注册、两项 DD2 映射 | test_mapping_schema、test_name_resolution、test_convert_equivalence、crawl-strategy-conversion.test.mjs |

J3：无新增生产模块；修改的 converter/schema/convert phase 均有新增或更新测试。测试 fixture 自包含且无网络依赖。

## Task-to-Evidence Coverage

- 1.1–1.2：before-status.txt/base-commit.txt；crypt-source-cell.html；converter-red.log；前置 core 及正式 collection 保留同一问题。前置两个 change 仍 active，但实现已提交。
- 2.1–2.2：schema-red.log → test_mapping_schema GREEN。
- 2.3–2.4：converter-red.log → Crypt Keeper/名称解析测试 GREEN。
- 2.5–2.6：links-red.log、adjacent-red.log、unwrapped-adjacent-red.log → 边界测试 GREEN。首次重放17页新增重复保留于 initial-replay-failures.json；用户批准更新边界后重放全部消除。
- 2.7–2.8：cache-red.log → test_pre_icon_semantics_cache_is_invalidated；Python/Node 镜像断言。
- 3.1–3.2：all-pages/manifest.json、audit.json、structure.json；comparison.json、semantic-review.json；sample-review 含 before/after/diff 和独立指标。
- 3.3：python-tests.log、node-tests.log、site-tests.log、capabilities.json；Python 3.9 parse 和 diff 检查。
- 4.1–4.3：本文件及 writeback.md，本地架构/策略 schema/handoff 回写。

## 关键证据入口

诊断根目录为 `outputs/debug-merged-cell-icons/`（ignored，可本地复核）；持久测试为 `tests/test_merged_cell_icons.py`、`tests/test_convert_equivalence.py`、`tests/pipeline/test_conversion_resume.py`、`tests/crawl-strategy-conversion.test.mjs`。离线重放脚本 `replay_all.py` 只读取缓存并写独立目录，网络元数据尝试为 0。

## 缺口与阻塞项

- 本次 scope 无未完成实现项。996 个延续槽位仍显示 `（未命名图标）`，主要来自头像、饰品或缺失/文件名式 alt；没有可靠名称证据则不猜测。原格图片完整，不表示这些副本的准确名称已恢复。
- 全量 complete_validation=false：S3/S12 各209 skip；S6 53 无表格、S8 16 无标题、S9 61 正文导航重叠、S10 205 无视频。S1/S2/S4/S5/S7/S11 全部209 pass，其余适用检查通过。skip 不视为已验证。
- 未重跑本地化脚本及锚点审计、未重新抓取、未发布新 collection；既有跨 DD1 映射与锚点缺口不在本 change 范围。
- 归档需先回填 fix-wiki-table-sample-integrity 的 merged-cell-asset-retention，再应用本 MODIFIED block；fix-conversion-structure-and-audit-fidelity 的先行规范也应先同步。本次不代为归档前置 change。

## Evidence Map

```json
{
  "evidence_map": [
    {
      "scenario_key": "exact-mapping",
      "evidence_ref": "tests/test_merged_cell_icons.py",
      "external_ref": "7791dd2 + fix-merged-cell-icon-semantics working tree",
      "verification_result": "pass"
    },
    {
      "scenario_key": "invalid-map",
      "evidence_ref": "tests/test_merged_cell_icons.py",
      "external_ref": "7791dd2 + fix-merged-cell-icon-semantics working tree",
      "verification_result": "pass"
    },
    {
      "scenario_key": "absent-map-and-shared-paths",
      "evidence_ref": "tests/test_merged_cell_icons.py",
      "external_ref": "7791dd2 + fix-merged-cell-icon-semantics working tree",
      "verification_result": "pass"
    },
    {
      "scenario_key": "crypt-keeper-colspan",
      "evidence_ref": "tests/test_merged_cell_icons.py",
      "external_ref": "7791dd2 + fix-merged-cell-icon-semantics working tree",
      "verification_result": "pass"
    },
    {
      "scenario_key": "mixed-span-and-repeated-source-assets",
      "evidence_ref": "tests/test_merged_cell_icons.py",
      "external_ref": "7791dd2 + fix-merged-cell-icon-semantics working tree",
      "verification_result": "pass"
    },
    {
      "scenario_key": "explicit-name-or-unknown",
      "evidence_ref": "tests/test_merged_cell_icons.py",
      "external_ref": "7791dd2 + fix-merged-cell-icon-semantics working tree",
      "verification_result": "pass"
    },
    {
      "scenario_key": "linked-icon-and-existing-label",
      "evidence_ref": "tests/test_merged_cell_icons.py",
      "external_ref": "7791dd2 + fix-merged-cell-icon-semantics working tree",
      "verification_result": "pass"
    },
    {
      "scenario_key": "ordinary-and-filtered-content",
      "evidence_ref": "tests/test_merged_cell_icons.py",
      "external_ref": "7791dd2 + fix-merged-cell-icon-semantics working tree",
      "verification_result": "pass"
    },
    {
      "scenario_key": "adjacent-exact-label",
      "evidence_ref": "tests/test_merged_cell_icons.py",
      "external_ref": "7791dd2 + fix-merged-cell-icon-semantics working tree",
      "verification_result": "pass"
    }
  ]
}
```
