---
domain: mp.weixin.qq.com
description: Publicly accessible WeChat article detail pages
protection_level: low
anti_crawl_refs: []
structure:
  pages:
    - id: public_article
      label: WeChat Public Article
      url_pattern: /s/:id
      url_example: https://mp.weixin.qq.com/s/aBcDeFgHiJk
      type: static_article
      content_type: article_body
      pagination: none
      links_to: []
      requires_auth: false
  entry_points:
    - public_article
extraction:
  selectors:
    title: "#activity-name"
    title_fallback: h1
    author: "#js_name"
    author_fallback: "#js_author_name"
    publish_time: "#publish_time"
    body: "#js_content"
  image_handling:
    attribute: data-src
    fallback: src
    output_format: markdown_inline
  cleanup:
    - strip_lead_in_promo
---

## Overview

Public WeChat article detail pages at `mp.weixin.qq.com/s/<id>` are static HTML pages that render the full article content server-side. No JavaScript rendering is required for the article body.

## Page Structure

- Single page type: article detail.
- Page title matches article heading.
- Article body rendered in-page, readable without login when public.
- Images use `data-src` attributes (not `src`) which require attribute-aware extraction.

## Extraction Flow

1. Open the page URL.
2. Verify page identity with title and URL.
3. Extract: title (`#activity-name`), author/account name (`#js_name`), publish time (`#publish_time`), body (`#js_content`).
4. Walk `#js_content` in DOM order — emit non-empty text blocks in reading order.
5. For images: prefer `data-src`, fallback to `src`. Keep inline using Markdown syntax.
6. Strip lead-in promotional content (subscription prompts, account IDs, profile promo text) that appears before the main article body.

## Known Issues

- `innerText` alone drops image links from the final content — always walk DOM order.
- Lead-in promotional content (e.g., "Click follow", account promo) may appear before the article body. Strip conservatively — only when clearly outside the article.
- URL format is always `mp.weixin.qq.com/s/<id>`. Non-public articles may require login or show error.

## Evidence

- Validated on real article run (2026-04-28).
- Scrapling `get` with `--ai-targeted` returned article title and inline image URL successfully.
- Lead-in promotional fragments still present in Scrapling output — cleanup guidance remains necessary.
