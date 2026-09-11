# Proposal

## 问题定义

Grow a Garden 全量抽取收尾阶段产出的三处输出质量修复仍在工作区未提交（`infobox.py` 多行单元格断行、`convert.py` H1 判定、hero 图 URL 改 `Special:Redirect`、`CONVERTER_CONTRACT_REVISION` 2→3），外加策略四件套（`growagarden.fandom.com/strategy.md` 切 `html_rendered` + tabber 去重、golden 更新、registry 条目、freeze-report）。复核确认代码正确，但存在四项收尾缺口：

1. **C9 测试缺口**：`scripts/lib/extraction/` 与 `pipeline/phases/` 的修改没有任何新测试。三个修复行为（多行值 `<br>` 转义、`## Infobox` 开头补 H1、hero URL 形式）均无断言守护，属"改回即静默退化"型。
2. **L6 图片校验误报**：`strategies/__init__.py:validate_images` 对 Fandom CDN URL（`static.wikia.nocookie.net/.../revision/latest/scale-to-width-down/111?cb=...`）取末段得 `111?cb=`，批量误报 `api_missing`（实测单站 17,624 条噪音）。`Special:Redirect` 分支已修，`/revision/` 分支未修。
3. **`mobalytics.gg/` 未收编**：冻结产物（策略 + freeze-report + registry 条目）悬空在工作区，registry 已引用未跟踪目录。
4. **growagarden freeze-report.json 未跟踪**：仓库先例（gameanalytics）是跟踪的。

## 范围边界

- 收编工作区既有质量修复补丁，补齐 C9 测试义务。
- 修复 L6 `validate_images` 对 `/revision/` CDN URL 的文件名解析。
- 收编 `mobalytics.gg` 策略目录与 growagarden freeze-report（提交动作本身在 tasks 中，不产生新行为）。
- 不重跑全站抓取、不改 my-wiki 归档（上一任务已交付）。
- 不修改 `.mjs` 文件（C10 无涉）。
- 不改 discovery / explore / cache 语义（已在归档 change 中冻结）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `extract-kernel`: infobox 表格构建对含换行/竖线的单元格执行 Markdown 表格安全转义（`\n → <br>`、`| → \|`），bs4 与 selectolax 两条路径行为一致。
- `pipeline-convert-phase`: HTML 路径仅以 H1（`# ` 前缀）判定"已有标题"；hero 图 URL 从渲染标记解析（infobox 优先、CDN URL、无图则省略，含 wikitext 路径 `rendered_html` 回退）；转换语义变化由 `CONVERTER_CONTRACT_REVISION` 2→4 承载。
- `pipeline`: L6 图片可用性校验正确解析 Fandom CDN `/revision/` URL 的真实文件名，消除批量误报。
- `strategy`: growagarden 站点策略冻结产物（acquisition 切换、tabber 去重、golden、freeze-report）与 mobalytics 策略目录收编进版本管理。

## Capabilities 待确认项

- [x] 能力清单已与用户确认（用户指令：剩余问题与未提交修改整理到一个 change）

## Impact

- 代码：`scripts/lib/extraction/infobox.py`（已改，收编）、`scripts/pipeline/pipeline/phases/convert.py`（已改，收编）、`scripts/pipeline/strategies/__init__.py`（新增 `/revision/` 解析）。
- 测试：`tests/test_convert_equivalence.py` 新增三条断言；`validate_images` 新增单测（tests/ 顶层或 pipeline tests，按既有分组）。
- 策略资产：`sites/strategies/growagarden.fandom.com/*`、`sites/strategies/mobalytics.gg/*`、`sites/strategies/registry.json` 收编。
- 行为变化：所有 Fandom 域 L6 校验的 unavailable 条目减少（预期）；其他域校验输出不变。
- 风险：L6 解析改动影响面为校验报告条目数，不触碰抓取/转换产出；golden 已随策略有意更新且六域回归通过。

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：`docs/GOVERNANCE.md`；`docs/architecture/05-converter-architecture.md`、`02-pipeline-flow.md`、`03-strategy-schema.md`；回写目标见 binding「回写目标」节。
