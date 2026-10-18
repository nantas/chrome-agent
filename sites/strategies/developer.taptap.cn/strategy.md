# Auto-generated scaffold — review recommended

---
domain: developer.taptap.cn
description: Auto-discovered site for developer.taptap.cn
protection_level: low
anti_crawl_refs:
- default
structure:
  pages:
  - id: nav_0
    label: 推广平台
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_1
    label: 资源置换平台
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_2
    label: 内容营销平台
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_3
    label: 广告联盟平台
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_4
    label: 开发者学堂
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  entry_points:
  - nav_0
  - nav_1
  - nav_2
  - nav_3
  - nav_4
api:
  type: sitemap
  base_url: https://developer.taptap.cn/sitemap.xml
  version: ''
  capabilities: []
extraction:
  engine: scrapling-get
  selectors:
    content: body
    title: title
    nav: body
  cleanup: []
  text_normalization: []
lifecycle:
  status: draft
  review_evidence: null

---

# developer.taptap.cn Strategy

## Platform Notes

Auto-discovered site for developer.taptap.cn

## Extraction Rules

- Review and adjust selectors and cleanup rules
- Verify page type mappings match actual site structure