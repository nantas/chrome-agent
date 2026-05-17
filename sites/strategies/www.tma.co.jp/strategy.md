# Auto-generated scaffold — review recommended

---
domain: www.tma.co.jp
description: Auto-discovered site for www.tma.co.jp
protection_level: low
anti_crawl_refs:
- default
structure:
  pages:
  - id: list_page
    label: List Page
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_0
    label: 関連商品
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  entry_points:
  - list_page
  - nav_0
api:
  type: robots
  base_url: https://www.tma.co.jp/robots.txt
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

---

# www.tma.co.jp Strategy

## Platform Notes

Auto-discovered site for www.tma.co.jp

## Extraction Rules

- Review and adjust selectors and cleanup rules
- Verify page type mappings match actual site structure