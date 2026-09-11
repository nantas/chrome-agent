# Writeback

## 回写摘要

**Change**：`close-mediawiki-quality-followups` — 收编 Grow a Garden 抽取收尾的三处输出质量修复（infobox 单元格转义 / H1 判定 / hero URL 从渲染标记解析）、修复 L6 图片校验对 Fandom CDN `/revision/` URL 的批量误报、修复 wikitext 路径 hero 静默丢弃回归、收编 growagarden 冻结产物与 mobalytics 策略。**结果**：4 capability spec 全覆盖，180 unit + 19 site-samples + pipeline-tests + doctor 全绿，三提交落地（`92d468b` / `d4a516f` / `cf83fb0`）。

## Capability / Spec 增量摘要

| Capability | 变更类型 | spec 文件 | 核心增量 |
|---|---|---|---|
| `extract-kernel` | ADDED requirement | `specs/extract-kernel/spec.md` | `infobox-table-cell-escaping`：两条渲染路径 `\n→<br>`、`\|→\\|` |
| `pipeline-convert-phase` | MODIFIED requirement | `specs/pipeline-convert-phase/spec.md` | `conversion-output-format`：H1 判定收紧为 `# ` 前缀；hero URL 从渲染标记解析（infobox 优先、`data:` 跳过、无图省略、wikitext `rendered_html` 回退）；`CONVERTER_CONTRACT_REVISION` 2→4（跳 3 有意，本地缓存 rev-3 指纹需失效） |
| `pipeline` | ADDED requirement | `specs/pipeline/spec.md` | `l6-image-filename-parsing`：`Special:Redirect` / `/revision/` / 末段三级解析，消除 ~17k/站 `api_missing` 误报 |
| `strategy` | MODIFIED + ADDED | `specs/strategy/spec.md` | growagarden 冻结产物自洽入库；mobalytics 收编（字节不动） |

归档后合并入 `openspec/specs/`：`extract-kernel/spec.md`、`pipeline-convert-phase/spec.md`、`pipeline/spec.md`（新 requirement）、`strategy/strategy-lifecycle.md` 或 `strategy-schema.md`（按归档工具惯例归位）。

## 验证结论与证据入口

- 真源：`verification.md`（spec-to-implementation 4/4 全覆盖、task-to-evidence 全映射、J3 无缺口）。
- 关键证据：`tests/test_convert_equivalence.py::TestOutputQualityFollowups`（6 断言，含 RED 证明）、`tests/test_validate_images_filename.py`（4 测试）、`boa_bloody_gust_minimal.golden.md` 重录（+H1 预期漂移）、unit 180 OK / site-samples 19 OK / doctor ALL GREEN。

## 回写目标与字段映射

| 目标页面 | 回写字段 | 来源 |
|---|---|---|
| `docs/architecture/05-converter-architecture.md` | infobox 表格单元格转义约定；hero 图 URL 解析规则（infobox 优先→正文、无图省略、wikitext 回退）；H1 判定语义；`CONVERTER_CONTRACT_REVISION` bump 纪律（语义变化必须 bump，跳号需注明理由） | spec delta extract-kernel / pipeline-convert-phase |
| `docs/architecture/02-pipeline-flow.md` | L6 `validate_images` 的 URL→`File:` 三级解析规则 | spec delta pipeline |

## 回写执行结果

| 目标 | 结果 | 说明 |
|---|---|---|
| `docs/architecture/05-converter-architecture.md` | 成功（见 4.3 证据） | converter 行为章节补三段 |
| `docs/architecture/02-pipeline-flow.md` | 成功（见 4.3 证据） | L6 校验小节补解析规则 |

## 回写前置条件

- verification.md 结论为全绿（已满足）。
- 归档（`/opsx-archive`）时 specs 合并 `openspec/specs/`，回写先于归档执行。

## 不回写的内容

- my-wiki 侧归档/ingest 状态（上轮任务已交付，非本 change 范围）。
- `scripts/pipeline/tests/` 不被 test_runner 发现的治理盲区（verification.md 已记录，独立事项）。
- mobalytics 策略内容细节（外部任务产物，registry 已可追溯）。
