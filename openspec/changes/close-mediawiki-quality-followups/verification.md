# Verification

## 验证环境

- HEAD：`c745dc7` + 验证后修复提交（实现链：`92d468b` 代码 / `d4a516f` growagarden / `cf83fb0` mobalytics / `c745dc7` 回写 / 后续 opsx-verify 修复提交）
- 解释器：`.venv/bin/python`（selectolax 等应用层依赖可用）
- 日期：2026-09-11

## Spec-to-Implementation Coverage

### extract-kernel / infobox-table-cell-escaping ✅

| Requirement 场景 | 实现 | 证据 |
|---|---|---|
| multi-line-value-single-row | `infobox.py:_extract_bs4` / `_extract_selectolax` 的 `\n→<br>`、`\|→\\|` | `tests/test_convert_equivalence.py::TestOutputQualityFollowups::test_infobox_multiline_and_pipe_cells_are_single_rows`（kernel + pipeline 双路径断言；RED 验证：还原转义后 FAILED） |
| both-render-paths-escape | 同上两处 | 同上（pipeline 走 bs4、断言覆盖值与键） |
| regression-guard | 测试落地 | 同上（含 RED 证明） |

### pipeline-convert-phase / conversion-output-format ✅

| Requirement 场景 | 实现 | 证据 |
|---|---|---|
| output-content-integrity | 未触碰装配契约 | `scripts/pipeline/tests/test_convert_cleanup_real_data.py` golden 重录后通过（+2 行 H1 为预期漂移） |
| section-heading-still-gets-h1 | `convert.py` 首个非空行 `# ` 判定 | `test_h1_prepended_when_body_opens_with_section_heading`（RED：还原旧判定后 FAILED） |
| existing-h1-not-duplicated | 同判定逻辑 | `test_exactly_one_h1_when_body_heading_renders_as_h2`（h1 被转换器降级为 `##`，恰好一个 H1） |
| hero-image-resolved-from-markup | `_resolve_hero_image_url`（infobox 优先→正文、`//`→https、跳过 `data:`） | `test_hero_image_resolved_from_infobox_markup`（RED：构造 URL 后 FAILED） |
| hero-image-omitted-when-unusable | 返回 None 则省略注入 | `test_hero_image_omitted_when_no_http_image` |
| wikitext-path-keeps-hero-injection | `html or raw.get("rendered_html")` 回退（本次实施新增，修掉业务消费方补丁的回归） | `test_wikitext_path_hero_falls_back_to_rendered_html`（先 RED 后 GREEN） |
| revision-bump-invalidates-stale-markdown | `CONVERTER_CONTRACT_REVISION = 4`（跳过 3：本地缓存有 rev-3 指纹） | 代码常量 + `git show 92d468b` diff |
| 端到端冒烟 | 真实 Crops 样本经 `convert_single_page` | hero = `static.wikia.nocookie.net/...TomatoPlantPic.png/...`、`# Crops` 前置（评审轮记录） |

### pipeline / l6-image-filename-parsing ✅

| Requirement 场景 | 实现 | 证据 |
|---|---|---|
| revision-url-resolves-real-filename | `strategies/__init__.py:_image_file_title` 的 `/revision/` 切分 | `tests/test_validate_images_filename.py::TestImageFileTitle::test_revision_url_resolves_real_filename` |
| plain-url-behavior-unchanged | 末段回退 | `test_plain_url_last_segment` |
| special-redirect-branch-preserved | 既有分支保留 | `test_special_redirect_branch_preserved` |
| 误报消除端到端 | fake client 集成 | `TestValidateImagesNoFalsePositive::test_cdn_revision_url_not_reported_missing` |

### strategy ✅

| Requirement 场景 | 证据 |
|---|---|
| strategy-passes-schema | `validate_extraction(growagarden strategy) == []` |
| golden-regression-green | `site-samples --domain growagarden.fandom.com` → 1 test OK |
| registry-reference-resolved | mobalytics 条目 `file` 字段 → 磁盘路径存在，随 `cf83fb0` 入库 |
| strategy-content-untouched | `git show cf83fb0 --stat`：仅新增 2 文件（+86 行），无内容修改 |

## Task-to-Evidence Coverage

| Task | 证据 |
|---|---|
| 1.1 差距核对 / 1.2 基线 | 评审轮：unit 170 OK / site-samples 19 OK |
| 2.1–2.4（Slice A/B） | 6 条新断言 + RED/GREEN 证明（见上） |
| 2.5–2.6（Slice C） | 4 条新测试（RED=函数不存在即失败；旧行为 `url.split('/')[-1]` 产出 `111?cb=...` 被断言拒绝） |
| 2.7 growagarden 自洽 | schema [] / 回归 OK / freeze-report 入库 `d4a516f` |
| 2.8 mobalytics 完整性 | 路径存在 + 字节不动入库 `cf83fb0` |
| 2.9–2.11 提交 | `92d468b` / `d4a516f` / `cf83fb0`，工作区 clean |
| 3.1 全量回归 | unit **180 OK**（170+10）、site-samples **19 OK (skipped=10)**、`unittest discover -s scripts/pipeline/tests` **OK**、doctor **ALL GREEN** |
| 3.2 L6 行为变化 | Fandom 域 unavailable 条目预期减少（`api_missing` 误报消除）；非 Fandom 域走末段回退不变 |

## J3 测试完备检查

- 新增代码：`_resolve_hero_image_url`、`_image_file_title` 均有直接测试 ✅（WARNING/Critical 均不触发）
- 修改模块：`infobox.py`、`convert.py`、`strategies/__init__.py` 均带新测试 ✅
- 文档：无新增 `.md` 模块

## 独立验证（subagent /opsx-verify）与验证后修复

独立 reviewer 全量重跑证据（不采信本文档结论）：unit 180 OK、site-samples 19 OK、pipeline-tests 51 OK、doctor success、RED 复现全部成立。结论：**无 CRITICAL，4 WARNING**。修复情况：

| # | 发现 | 处置 |
|---|---|---|
| W1 | wiki.gg 系根相对 `/images/` src 被 hero resolver 跳过，hero 静默丢失（实测 bindingofisaacrebirth / slaythespire / vampire.survivors 三域） | ✅ 已修：根相对 src 以 `image_handling.base_url`（回退 domain）补全；测试 `test_hero_image_root_relative_src_absolutized`（base_url 有/无两分支） |
| W2 | spec 场景 `both-render-paths-escape` 无覆盖——两条既有断言都走 bs4 路径 | ✅ 已修：`test_infobox_cell_escaping_selectolax_path`（Node 输入 + inline renderer 产出多行值） |
| W3 | L6 对 MediaWiki `/thumb/` 缩略图 URL 仍误报（末段是 `150px-<name>`），且 spec 结尾段与回退规则口径冲突 | ✅ 已修：`_image_file_title` 补 `/thumb/` 分支（`NNNpx-` 前缀判定取前段）；spec 收窄为"对 `/revision/` 与 `/thumb/` 两类变换后缀"；测试 `test_mediawiki_thumb_url_resolves_real_filename` |
| W4 | 重录 golden 的守护测试不在默认 runner 发现范围 | ✅ 已修：`cmd_unit` 补 `scripts/pipeline/tests` discover，51 个 module-adjacent 测试进默认套件 |
| S1 | H1 去重分支实际不可达（h1 被降级） | ✅ 已处理：代码注释标防御性，design 决策 10 记录 |
| S2 | design 决策 1 测试落点与实现不一致 | ✅ 已处理：design 决策 1 改写并注明偏离理由 |
| S3 | verification 头部 HEAD 过期 | ✅ 本节首行已更新 |
| S4 | frontmatter `image` 与 hero 双首图定义并存 | 推迟：无害，等收敛需求出现（记入 design 决策 8 旁注与 reviewer Feedback） |

修复后回归：unit **231 OK**（含 pipeline-tests 51）、site-samples **19 OK**、equivalence 25/25。

## 缺口与遗留（更新）

- ~~`scripts/pipeline/tests/` 不在默认发现范围~~ → W4 已修。
- `installed-hash` 仍指向 `c9d3b76`（本 change 未改 `.mjs`，C10 免除；下次改 `.mjs` 时刷新）。
