# Auto-generated scaffold — review recommended

---
domain: ludology.libsyn.com
description: Auto-discovered site for ludology.libsyn.com
protection_level: authenticated
anti_crawl_refs:
- login-wall-redirect
structure:
  pages:
  - id: article_page
    label: Article Page
    type: static_article
    content_type: wiki_article
    pagination: none
    requires_auth: false
  - id: nav_0
    label: About
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_1
    label: Episodes
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_2
    label: All Episodes
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_3
    label: Archives
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_4
    label: '2026'
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  entry_points:
  - article_page
  - nav_0
  - nav_1
  - nav_2
  - nav_3
  - nav_4
api:
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

# ludology.libsyn.com Strategy

## Platform Notes

Auto-discovered site for ludology.libsyn.com

## Extraction Rules

- Review and adjust selectors and cleanup rules
- Verify page type mappings match actual site structure