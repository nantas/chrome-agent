# Specification Delta

## Capability 对齐（已确认）

- Capability: `pipeline-infobox`（专题 spec：`openspec/specs/pipeline/pipeline-infobox.md`）
- 来源: `proposal.md` / 已确认 capabilities（C 候选）
- 变更类型: `removed`
- 用户确认摘要: 用户选定 REMOVED on `pipeline-infobox.md`。subagent reachability audit 确认 converter 内的 infobox 渲染子系统（`_render_infobox_table` + `_apply_infobox_handler` + 7 handler + `__init__` 配置读取 + `_render_block` div-handler 分支，~130 行）在所有声明路径中不可达——CV3/CV4 经 `preprocess_html` 先剥掉 infobox 容器，CV5 空 config。架构已演变为 `(preprocess 去除容器) + (convert_page_full Step-1 经 infobox.py BS4 路径独立提取)`，convert 期渲染路径废弃。infobox 的 SSOT 是 `scripts/lib/extraction/infobox.py`（由 `unified-infobox-extraction` / `shared-infobox-renderer` specs 覆盖）。

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## REMOVED Requirements

### Requirement: render-infobox-table-uses-shared-lib

**Reason**: 该 requirement 要求 `HtmlToMarkdownConverter._render_infobox_table()` SHALL 调用 `lib.extraction.infobox.extract_infobox()`——但 `_render_infobox_table()` 本身（及其调用点 `_apply_infobox_handler` + 7 handler 方法）在所有声明路径中不可达：CV3/CV4 经 `preprocess_html` 先剥掉 infobox 容器（per `infobox.selector`），CV5 空 config 致 `_infobox_enabled=False`。convert 期 infobox 渲染路径已被架构演变为 `(preprocess 去除容器) + (convert_page_full Step-1 经 infobox.py BS4 路径独立提取)` 取代。infobox 提取/渲染的 SSOT 是 `scripts/lib/extraction/infobox.py`（`extract_infobox()`，BS4 路径，由 `unified-infobox-extraction` + `shared-infobox-renderer` specs 覆盖），converter 内的副本是历史遗留 dead code（~130 行，本 change 同步删除）。该 requirement 约束的实现已不存在，requirement 失去约束对象。

**Migration**: infobox 提取的契约真源转为 `openspec/specs/unified-infobox-extraction/` 与 `openspec/specs/shared-infobox-renderer/`（两者均以 `infobox.py` SSOT 为对象）。任何依赖 convert 期 infobox 渲染的代码/文档应改为依赖 `infobox.py` 的 `extract_infobox()`（已由 convert_page_full Step-1 调用）。

### Requirement: handler-implementation-stays-in-converter

**Reason**: 该 requirement 要求 `_apply_infobox_handler()` 和所有 handler 方法 SHALL 保留在 converter 中、通过回调传递给 `extract_infobox()`。reachability audit 确认这些 handler 方法（`_strip_html`、`_extract_image_value`、`_count_images`、`_extract_cur_id`、`_dedup_pools`、`_simplify_collection`、`_extract_tags`）连同其分发器 `_apply_infobox_handler` 全部不可达（调用点 line 293 + line 347 均失效，见上）。`extract_infobox()` 经 BS4 路径用其**自身**的 `_apply_bs4_handler`（`infobox.py:213-262`），从不经回调触达 converter 的 handler。requirement 约束的对象（converter 内的 handler 实现）是 dead code，本 change 同步删除。

**Migration**: handler 行为的真源是 `infobox.py` 的 `_apply_bs4_handler`（BS4 路径）。若未来需要自定义 handler，在 `infobox.py` SSOT 内扩展，不复活 converter 内的副本。

## 保留的 requirement（不在本 change 范围）

`pipeline-infobox.md` 的其余 requirement（`infox-renderer-module-deprecated`、`remove-balanced-element` 等）不涉及 convert 期渲染路径，不受本 change 影响，保留不动。

## 关联代码变更（同 change 闭环）

本 REMOVED delta 与 `scripts/lib/extraction/converter.py` 删除 ~130 行 dead code（line 273-293、343-350、391-519、54-68、`_strip_html` 纯 infobox 作用域）在同一 change 内闭环。删除后 convert 产出 Markdown 字节级不变（dead code 本就不可达），由 `tests/test_convert_equivalence.py`（CV3/CV4/CV5 等价）+ `tests/pipeline/test_convert_cleanup_consistency.py`（已断言 infobox 被**去除**而非渲染）双重保证。
