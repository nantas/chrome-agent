---
domain: darkestdungeon.wiki.gg
description: 暗黑地牢一代及六项DLC：按确认清单通过正文HTML采集，遵循 robots 排除API
protection_level: high
extraction:
  selectors:
    title: '#firstHeading'
    content: .mw-parser-output
  image_handling:
    base_url: https://darkestdungeon.wiki.gg
    attribute: src
    output_format: markdown_inline
  cleanup:
  - strip_edit_links
  - unwrap_image_wrappers
  - convert_nested_images
  - strip_empty_parens
  cleanup_selectors:
  - .toc
  - '#toc'
  - .mw-editsection
  - style
  - .hash-anchor
  url_conversion:
    enabled: true
lifecycle:
  status: frozen
  review_evidence:
    quality_report: outputs/dd1-quality-fixed/quality-report.json
    scope_review: outputs/dd1-scope-review/scope-review-final.json
    user_approved: 用户已确认一代本体及六项DLC全量范围、样本质量、目标raw目录及内部链接要求
    policy_probe: outputs/dd1-policy/robots.txt
structure:
  pages:
  - id: dd1_home
    label: 暗黑地牢一代首页
    url_example: https://darkestdungeon.wiki.gg/wiki/Darkest_Dungeon_Wiki_1
    type: static_article
    content_type: wiki_main_page
    pagination: none
    requires_auth: false
    page_pattern:
    - regex:^https://darkestdungeon\.wiki\.gg/wiki/
  entry_points:
  - dd1_home
samples:
- page: Duelist (Darkest Dungeon)
  label: 已确认的正文结构回归样本
- page: The Fire's Edge
  label: 已确认的正文结构回归样本
- page: The Crimson Court
  label: 已确认的正文结构回归样本
- page: The Color of Madness
  label: 已确认的正文结构回归样本
- page: The Butcher's Circus
  label: 已确认的正文结构回归样本
- page: Trinkets (Darkest Dungeon)
  label: 已确认的正文结构回归样本
- page: Stress Bar
  label: 已确认的正文结构回归样本
discovery:
  method: sitemap
  sitemap_url: https://darkestdungeon.wiki.gg/sitemaps/sitemap-index-darkestdungeon_en.xml
engine_preference:
  preferred: cloakbrowser-fetch
---

# 暗黑地牢一代冻结采集策略

正文通过 CLI 读取 /wiki/ HTML，使用站点地图发现并按用户确认清单过滤；不调用 robots 禁止的 API。策略已注册、冻结，图片保留来源 URL。共享转换器清除 style 和标题锚点组件；管理链接映射时核验重定向和 Markdown 章节。

## Known Issues (Post-Validation)

| ID | Issue | Status | Priority | Owner | Impact | Resolution |
|----|-------|--------|----------|-------|--------|------------|
| KI-1 | Duelist (Darkest Dungeon)：Expected 156 images, found 220 in Markdown | resolved | P3 | pipeline | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
| KI-2 | Duelist (Darkest Dungeon)：Repeated link text | resolved | P1 | self_check | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
| KI-3 | Duelist (Darkest Dungeon)：Missing 8 sections: ['Anticipation', 'Touché', 'Feint', 'Disengage', 'Anticipation'] | resolved | P1 | pipeline | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
| KI-4 | The Fire's Edge：Repeated link text | resolved | P1 | self_check | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
| KI-5 | The Crimson Court：Repeated link text | resolved | P1 | self_check | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
| KI-6 | The Color of Madness：Repeated link text | resolved | P1 | self_check | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
| KI-7 | The Butcher's Circus：Repeated link text | resolved | P1 | self_check | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
| KI-8 | Trinkets (Darkest Dungeon)：Expected 519 images, found 522 in Markdown | resolved | P3 | pipeline | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
| KI-9 | Trinkets (Darkest Dungeon)：Repeated link text | resolved | P1 | self_check | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
| KI-10 | Stress Bar：Repeated link text | resolved | P1 | self_check | 对应告警已消除 | 七样本重新转换、自检及来源审计通过 |
