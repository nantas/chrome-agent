# Design

## Context

工作区已含三份修复补丁（复核验证正确）：`infobox.py` 两条渲染路径的单元格转义、`convert.py` 的 H1 判定 + hero URL + `CONVERTER_CONTRACT_REVISION=3`、growagarden 策略四件套。缺：C9 测试、L6 `/revision/` 解析、mobalytics/freeze-report 收编。规格见 `specs/extract-kernel`、`specs/pipeline-convert-phase`、`specs/pipeline`、`specs/strategy`。

## Goals / Non-Goals

**Goals:**

- 收编三处质量修复补丁并补齐 C9 测试断言。
- 修复 L6 `validate_images` 的 `/revision/` URL 解析（spec `pipeline/l6-image-filename-parsing`）。
- 收编 growagarden 冻结产物（含 freeze-report）与 mobalytics 策略目录。
- 按逻辑单元拆分提交（代码修复 / 策略资产）。

**Non-Goals:**

- 不重跑全站抓取、不动 my-wiki 归档、不改 `.mjs`（C10 无涉）。
- 不改 discovery/explore/cache 语义（已在归档 change 冻结）。
- 不为 `CONVERTER_CONTRACT_REVISION` 引入 converter 源码 hash 自动化（现有 bump 约定 + 文档提示足够；见 Risks）。

## Decisions

1. **测试落点**：三条 convert 断言进 `tests/test_convert_equivalence.py`（既有 equivalence 家族，直接用 `convert_single_page`/`convert_page_full` 夹具模式）；`validate_images` 解析测试**落在 `tests/` 顶层**（偏离原计划 `scripts/pipeline/tests/`：C9 顶层目录约定 + 默认 runner 只发现 `tests/`；同时已把 `scripts/pipeline/tests` 补进 runner 发现范围，见决策 9）。
2. **hero URL 从渲染标记解析**（业务消费方第二版方案，取代第一版 Special:Redirect 构造）：Cloudflare 保护的 Fandom 站上 wiki 域名路径（含 `/Special:Redirect/file/`）返回 challenge 页，而真实 CDN URL 已在渲染 HTML 里，直接读。`_resolve_hero_image_url` 优先 infobox 容器图、回退正文图、协议相对 `//` 与根相对 `/images/...` 均补全为绝对 URL（根相对用 `image_handling.base_url` 回退 wiki 域名——独立验证 W1 发现：wiki.gg 系标记全是根相对 src，不补全则 hero 静默丢失）、跳过 `data:` 占位、无图则省略注入。附带修复其 wikitext 调用点回归：wikitext 路径 raw 无 `html` 键只有 `rendered_html`，需 `html or rendered_html` 回退，否则动态 wikitext 页 hero 被静默丢弃（balatrowiki 等策略受影响）。
3. **L6 解析顺序**：先判 `Special:Redirect/file/`（既有），再判 `/revision/`（Fandom CDN）与 `/thumb/`（MediaWiki 缩略图，独立验证 W3 发现的同类误报），最后回退末段。切分逻辑内聚在 `_image_file_title` 单函数内。
4. **mobalytics 收编**：策略 + freeze-report + registry 条目作为一个整体提交，内容逐字节不动（外部任务冻结产物）。
5. **提交拆分**：① 代码修复 + 测试（`infobox.py`、`convert.py`、`strategies/__init__.py`、两处测试文件）；② growagarden 策略资产（含 freeze-report）；③ mobalytics 收编。registry.json 的 mobalytics hunk 归 ③。
6. **H1 判定用 `# ` 前缀**（带空格）而非 `#`：ATX H1 的严格形式，避免 `## Infobox` 误命中；非 ATX 的 `#heading` 无空格形式按无标题处理并前置 H1，语义安全。
7. **revision 2→4 跳过 3 是有意的**：本地 `.cache/mediawiki/` 已有 rev-3 指纹产物（1,602 页，含 Special:Redirect hero）；提交 3 会让 resume 静默复用旧 markdown，4 强制重转。
8. **body lazy-load 图不读 `data-src`**（known limitation）：无 infobox 页的 hero 可能取自后续非 lazy 图或省略。当前无站点需要；需要时在 resolver 里 honors `lazyload.real_src_attr` 再扩。
9. **runner 发现范围**（独立验证 W4）：`cmd_unit` 补上 `scripts/pipeline/tests` 的 discover，module-adjacent 的 golden 守护进入默认套件，不再依赖手动发现。
10. **H1 去重分支为防御性代码**（独立验证 S1）：转换器把 `<h1>` 降级为 `##`，HTML 路径正文实际不会以 `# ` 开头；保留分支并加注释，防内核 heading 语义变化。

## Risks / Migration

- **L6 输出变化**：其他 Fandom 域校验的 unavailable 条目减少（预期方向）；非 Fandom 域走 else 分支行为不变。回归以 site-samples + unit 覆盖。
- **hero 输出变化（全策略面）**：所有 `html_rendered` 策略的 hero URL 从 wiki 域名路径变为真实 CDN URL；wikitext 动态页在回退修复落地后保持注入。revision 4 强制全量重转（含 1,602 页缓存），重跑只耗 convert+assemble 时间（fetch 缓存可复用）。
- **`CONVERTER_CONTRACT_REVISION` 依赖人工 bump**：本次已 bump；自动化（源码 hash 入 fingerprint）留作后续独立提案，不在本 change 扩面。
- **golden 更新的不可逆性**：golden 已随策略有意更新并六域回归通过；若后续发现 tabber 去重误删，可从 `Crops.html.gz` 样本重生成。
- **mobalytics 归属**：外部任务产物，收编提交信息注明来源，避免与原任务冲突。
