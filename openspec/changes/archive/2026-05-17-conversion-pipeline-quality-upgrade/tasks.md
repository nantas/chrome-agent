# Tasks

## 1. Spec 覆盖与实现准备

- [x] 1.1 确认 8 个 capability spec 的实现边界无重叠或遗漏
  - 覆盖：`balanced-element-removal`、`tooltip-icon-link-merge`、`full-url-parameterization`、`sample-self-check`、`explore-workflow`、`pipeline-converters`、`site-strategy`、`site-strategy-template`
- [x] 1.2 确认依赖前置条件：`bs4`, `yaml`, `markdownify` 已在 `scripts/explore/requirements.txt` 中
- [x] 1.3 确认 `HtmlToMarkdownConverter` 当前源码位置和接口签名已知（`scripts/mediawiki_api_extract/converters/html_to_markdown.py`）

## 2. 核心实现任务

### 2.1 管线层：balanced-element-removal

- [x] 2.1.1 在 `HtmlToMarkdownConverter` 中实现 `remove_balanced_element(html, tag, attr_pattern)` 静态方法
  - Spec: `balanced-element-removal` — `remove-balanced-element`
  - 验证：使用 Isaac Wiki 的 TOC HTML 片段测试（`<div id="toc"><div class="inner">…</div></div><h2>Effects</h2>`），确认 Effects 章节保留
- [x] 2.1.2 实现 `remove_all_matching(html, tag, attr_pattern)` 静态方法
  - Spec: `balanced-element-removal` — `remove-all-matching-elements`
  - 验证：含 3 个 nav-box table 的 HTML，确认全部移除
- [x] 2.1.3 将 `clean_html()` 中的 TOC/editsection/navbox 移除改为调用 `remove_all_matching()`
  - Spec: `pipeline-converters` — `balanced-element-removal-method`
  - 验证：`The_Sad_Onion` 页面的全部 5 个 `mw-headline` sections 在 MD 中完整出现

### 2.2 管线层：tooltip-icon-link-merge

- [x] 2.2.1 在 `HtmlToMarkdownConverter` 中实现 `merge_tooltip_links(html)` 静态方法
  - Spec: `tooltip-icon-link-merge` — `merge-tooltip-icon-text-links`
  - 验证：`Wire Coat Hanger` link 从双重链接合并为 `[![img] Wire Coat Hanger](url)` 单一链接
- [x] 2.2.2 在 `convert_body()` 中，`merge_tooltip_links()` 在 `convert_images_to_md()` 之前调用
  - Spec: `tooltip-icon-link-merge` — `merge-before-image-conversion`
  - 验证：检查 pipeline 调用顺序

### 2.3 管线层：full-url-parameterization

- [x] 2.3.1 修改 `convert_links_to_md()` 接受 `wiki_domain` 必填参数，将 `/wiki/Xxx` 转为 `https://domain/wiki/Xxx`
  - Spec: `full-url-parameterization` — `convert-internal-links-to-full-urls`
  - 验证：扫描输出 MD，`grep '](/wiki/' *.md` 返回 0 行
- [x] 2.3.2 修改 `convert_images_to_md()` 接受 `wiki_domain` 必填参数和 `skip_patterns` 可选参数
  - Spec: `full-url-parameterization` — `convert-internal-images-to-full-urls`
  - 验证：所有 `![](...)` 使用 `https://` 前缀；Font_TeamMeat 和 Dlc_*_indicator 图片不在输出中
- [x] 2.3.3 在 `HtmlToMarkdownConverter.__init__()` 中从 `extraction_config` 提取 `wiki_domain`，缺失时 raise TypeError
  - Spec: `full-url-parameterization` — `base-url-from-strategy`
  - 验证：调用 `HtmlToMarkdownConverter(extraction_config={})` 应抛出 TypeError

### 2.4 管线层：YouTube oEmbed

- [x] 2.4.1 在 `HtmlToMarkdownConverter` 中实现 `extract_video_links(html)` 静态方法
  - Spec: `pipeline-converters` — `youtube-oembed-extraction-method`
  - 验证：The Sad Onion 输出中 `In-game Footage` 章节包含真实视频标题（非 "YouTube Video"）
- [x] 2.4.2 视频链接插入到 MD body 的 `## In-game Footage` 章节
  - Spec: `pipeline-converters` — `video-links-insert-into-body`
  - 验证：`grep "In-game Footage"` 后紧跟 YouTube 链接行

### 2.5 自检系统：S1-S12 升级

- [x] 2.5.1 修改 S1：增加 full URL 验证（`relative_image_url` fixable type）
  - Spec: `sample-self-check` — `self-check-s1-image-retention` (modified)
- [x] 2.5.2 修改 S2：改为零相对链接检测（`relative_link` fixable type）
  - Spec: `sample-self-check` — `self-check-s2-link-resolution` (modified)
- [x] 2.5.3 修改 S3：增加字段数 ≥3 和 HTML 残留检测
  - Spec: `sample-self-check` — `self-check-s3-infobox-extraction` (modified)
- [x] 2.5.4 修改 S5：增加 HTML 标签残留和实体残留检测
  - Spec: `sample-self-check` — `self-check-s5-text-integrity` (modified)
- [x] 2.5.5 修改 S6：增加行数偏差 ≤5% 阈值
  - Spec: `sample-self-check` — `self-check-s6-table-integrity` (modified)
- [x] 2.5.6 实现 S8：章节完整性检查
  - Spec: `sample-self-check` — `self-check-s8-section-completeness`
- [x] 2.5.7 实现 S9：导航泄漏检查
  - Spec: `sample-self-check` — `self-check-s9-navigation-leakage`
- [x] 2.5.8 实现 S10：YouTube 标题质量检查
  - Spec: `sample-self-check` — `self-check-s10-youtube-title-quality`
- [x] 2.5.9 实现 S11：相对链接零残留检查
  - Spec: `sample-self-check` — `self-check-s11-zero-relative-links`
- [x] 2.5.10 实现 S12：Infobox 语义质量检查（Name 空格、ID 导航泄漏）
  - Spec: `sample-self-check` — `self-check-s12-infoxbox-semantic-quality`
- [x] 2.5.11 更新 `run_checks()` 函数签名，接受 `wiki_domain` 参数
- [x] 2.5.12 更新 `auto_remediate()` 函数，增加 6 个新 fixable types
  - Spec: `sample-self-check` — `auto-remediation-extended`

### 2.6 策略与模板更新

- [x] 2.6.1 更新 `mediawiki-wiki-gg.yaml` 模板：增加 `image_filtering.skip_patterns`
  - Spec: `site-strategy-template` — `template-image-filtering`
- [x] 2.6.2 更新 `mediawiki-wiki-gg.yaml` 模板：增加 `cleanup_selectors`（含 `.nav-header`, `.nav-box`）
  - Spec: `site-strategy-template` — `template-extraction-cleanup-selectors`
- [x] 2.6.3 更新 `mediawiki-wiki-gg.yaml` 模板：修改 `content_profile` 推荐值为 `allpages` + `html_rendered` + `exact_title_match`
  - Spec: `site-strategy-template` — `template-content-profile-recommendations` (modified)
- [x] 2.6.4 更新 Isaac Wiki `strategy.md`：增加 `extraction.infoxbox_field_handlers` 配置
  - Spec: `site-strategy` — `infobox-field-handler-configuration`
  - Handlers: `health: count_images`, `id: extract_cur_id`, `alias(Item pool): dedup_pools`, `alias(Collection grid): simplify_collection`, `tags: extract_tags`, `image: image`, `portrait: image`, `costume: image`
- [x] 2.6.5 更新 Isaac Wiki `strategy.md`：增加 `extraction.image_filtering.skip_patterns`
- [x] 2.6.6 更新 Isaac Wiki `strategy.md`：修改 `api.content_profile.content_acquisition` 为 `html_rendered`

### 2.7 Skill 更新

- [x] 2.7.1 更新 `skills/chrome-agent/SKILL.md`：在 explore → crawl confirmation gate 后增加 Agent Gate 行为规范子章节
  - 自检报告先于样本展示
  - 样本必须输出文件路径到 `outputs/<run-tag>/`
  - agent 自行审计后展示 discrepancy list
  - 修改 converter 后全量重测
  - 最多 3 轮迭代
  - Spec: `explore-workflow` — 5 个 ADDED Requirements
- [x] 2.7.2 更新 `AGENTS.md`：在 explore gate 描述中增加 Agent Gate 规则引用
  - 不复制完整规则，只添加链接到 `skills/chrome-agent/SKILL.md`

## 3. 收敛与验证准备

- [x] 3.1 使用 Isaac Wiki 的 5 个样本页面运行完整 S1-S12 自检
  - 证据：`outputs/isaac-sample-validation/` 中的 `.md` 文件 + self-check 输出
- [x] 3.2 验证 `grep '](/wiki/' *.md` 返回 0 行（零相对链接）
- [x] 3.3 验证所有 5 个样本 `✅ Clean`（S1-S12 全部 pass）
- [x] 3.4 验证 `HtmlToMarkdownConverter` 单元测试：balanced removal、tooltip merge、oEmbed failover
- [x] 3.5 确认 pipeline 向下兼容：同一站点策略的现有 Phase B/C 输出与升级前一致（除 URL 从相对变完整外）

## 4. 验证与回写收敛

- [x] 4.1 基于真实实现结果生成 `verification.md`
- [x] 4.2 基于 verification 结论生成 `writeback.md`（目标：4 个 spec delta 文件 + `AGENTS.md`）
- [x] 4.3 执行 writeback：更新 spec 文件、`AGENTS.md`、`strategy.md`、`registry.json`
