# Writeback

## 回写目标

| 目标文件 | 变更内容 | 状态 |
|----------|----------|------|
| `sites/strategies/slaythespire.wiki.gg/strategy.md` | 更新 content_acquisition 为 html_rendered，扩展 namespaces 为 [0, 3000, 14]，新增 category_page_generation 和 image_filtering 配置 | ✅ 已完成 |
| `sites/strategies/registry.json` | 更新 slaythespire.wiki.gg 条目描述、page_types、entry_points | ✅ 已完成 |

## 变更摘要

### strategy.md 变更
- `description`: 更新为反映 StS1 + StS2 + categories 完整覆盖
- `api.namespaces`: `[0, 3000]` → `[0, 3000, 14]`
- `api.content_profile.content_acquisition`: `"hybrid_wikitext_plus_rendered"` → `"html_rendered"`
- `api.category_page_generation`: 新增 `true`
- `api.image_filtering.list_pages`: 新增 `base_only`
- `api.output.link_format`: 新增 `markdown_relative`

### registry.json 变更
- `description`: 更新为反映完整站点爬取能力
- `page_types`: 新增 `wiki_list_page`, `wiki_category`
- `entry_points`: 新增 `category_page`

## 前置条件

- [x] 所有核心 task 完成
- [x] 组件测试通过
- [x] 端到端小样本验证通过（25/25 pages，0 failure）
- [x] verification.md 生成

## 审计证据

- **变更提交**: 直接在 working tree 中修改（未通过 git commit，由用户决定提交时机）
- **修改文件清单**:
  - `scripts/mediawiki-api-extract/strategies.py` — 新增 HtmlRenderedAcquisitionStrategy, HtmlToMarkdownConverter, title_to_filepath
  - `scripts/mediawiki-api-extract/phase_a.py` — 集成语义化目录映射
  - `scripts/mediawiki-api-extract/phase_b.py` — 支持 HTML 路径分支
  - `scripts/mediawiki-api-extract/phase_c.py` — 添加分类页生成器
  - `scripts/mediawiki-api-extract/pipeline.py` — 注册 html_rendered 策略
  - `sites/strategies/slaythespire.wiki.gg/strategy.md` — 更新策略配置
  - `sites/strategies/registry.json` — 更新索引
- **测试证据**:
  - 组件测试输出：All component tests passed!
  - 端到端测试：`/tmp/test-html-crawl-v2/` 包含 25 页面文件 + 5 分类索引
- **执行时间**: 2026-05-07
