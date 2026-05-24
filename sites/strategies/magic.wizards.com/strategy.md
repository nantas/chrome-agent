# Auto-generated scaffold — review recommended

---
domain: magic.wizards.com
description: Auto-discovered site for magic.wizards.com
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
    label: Marvel Super Heroes
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_1
    label: The Hobbit™
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_2
    label: Reality Fracture
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_3
    label: Star Trek
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  - id: nav_4
    label: Secrets of Strixhaven
    type: static_article
    content_type: wiki_list_page
    pagination: none
    requires_auth: false
  entry_points:
  - list_page
  - nav_0
  - nav_1
  - nav_2
  - nav_3
  - nav_4
api:
  type: sitemap
  base_url: https://magic.wizards.com/sitemap.xml
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

# magic.wizards.com Strategy

## Platform Notes

Auto-discovered site for magic.wizards.com

## Extraction Rules

- Review and adjust selectors and cleanup rules
- Verify page type mappings match actual site structure