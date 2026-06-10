# developer.nintendo.com — Nintendo Developer Portal


---
domain: developer.nintendo.com
description: Nintendo Developer Portal — authenticated documentation for Switch SDK, network services, account system, and online play
protection_level: authenticated
anti_crawl_refs:
  - login-wall-redirect
  - object-embed-content
  - contents-subdirectory
structure:
  pages:
    - id: viewer_page
      label: Document Viewer
      type: embedded_object_viewer
      content_type: documentation_hub
      pagination: none
      requires_auth: true
      engine: chrome-cdp
    - id: sdk_api_page
      label: SDK API Reference Page
      type: static_article
      content_type: api_reference
      pagination: none
      requires_auth: true
      engine: chrome-cdp
    - id: guide_subpage
      label: Guide/Manual Sub-Page
      type: static_article
      content_type: documentation_section
      pagination: none
      requires_auth: true
      engine: chrome-cdp
      notes: "Direct URL via contents/ subdirectory: dirname(<doc_path>) + /contents/ + <sub_page_href>"
  entry_points:
    - viewer_page
    - sdk_api_page
    - guide_subpage
api:
  capabilities: []
extraction:
  engine: chrome-cdp
  reason: "login-wall requires authenticated browser session; scrapling-get returns login page"
  selectors:
    content: "#autoindex_content, .autoindex_content"
    title: ".pagetitle"
    nav: "#contents_tree"
    toc_print: "#selectCategory option"
    object_data: "object[data]"
    subpage_links: "a[href*='Pages/']"
  cleanup:
    - "Remove .page_navigation_top tables"
    - "Remove <noscript> blocks"
    - "Remove .copyright and .confidential boilerplate"
  text_normalization: []
  notes: |
    URL Architecture (critical):
    - Viewer URL: /html/online-docs/<locale>/document.html?doc=<rel_path>&docname=<name>
    - Content embedded via <object data="<rel_path>"> (same-origin, contentDocument accessible)
    - Guide/Manual sub-pages directly accessible via contents/ path pattern:
      https://developer.nintendo.com/html/online-docs/<locale>/<doc_dir>/contents/Pages/Page_xxx.html
    - SDK API pages (Doxygen-style) directly accessible without viewer
    
    Extraction workflow:
    1. Load viewer → extract sub-page links from object.contentDocument
    2. For each sub-page: nav to resolved URL (with contents/) → extract #autoindex_content
    3. Sub-page title from .pagetitle or document.title
    
    Content types:
    - Guide/Manual (multi-page): Shell HTML + JS dynamic sub-pages via Reassemble module
    - SDK API (static): Standard Doxygen HTML, directly accessible
    - Network docs (static): Independent HTML pages, directly accessible
samples:
  - page: "Account_Guide/4-4_Account_Link_Status.html"
    label: "表格密集的账户链接状态页"
  - page: "Independent_Server_Setup_Manual/4-7.4_Account_API.html"
    label: "含表格的 API 参考页"
  - page: "Online_Play_Guide/8_Previous_Revision_History.html"
    label: "修订历史长列表页"

---

# developer.nintendo.com Strategy

## Platform Notes

Nintendo Developer Portal documentation site. Requires NDID authentication. All `/html/online-docs/` paths behind login wall.

## URL Architecture

### Viewer Pattern
```
https://developer.nintendo.com/html/online-docs/g1kr9vj6-en/document.html
  ?doc=<relative_path>
  &docname=<display_name>
```

### Content Embedding
- Viewer creates `<object data="<relative_path>">` to embed document
- `object.contentDocument` is same-origin → accessible via CDP eval
- Object's contentDocument includes navigation tree, print controls, and content area

### Sub-Page Direct Access (Key Discovery)
Guide/Manual sub-pages are directly accessible via the `contents/` path pattern:
```
Base URL:  https://developer.nintendo.com/html/online-docs/g1kr9vj6-en/
Doc path:  Packages/Network/Guides/NX-Account_Guide/NX-Account_Guide.html
Sub-page:  Packages/Network/Guides/NX-Account_Guide/contents/Pages/Page_106359742.html
                                                                                                                                                             
Rule:      dirname(<doc_path>) + "/contents/" + <relative_subpage_href>
```

## Content Types

1. **Guide/Manual (multi-page)**: Shell HTML with JS navigation tree. Main HTML = nav + title sheet. Sub-pages loaded by Reassemble JS via AJAX. Direct URL access works via `contents/` path.
2. **SDK API (static)**: Standard Doxygen HTML. Directly accessible.
3. **Network docs (static)**: Independent HTML pages. Directly accessible.

## Extraction Rules

- Always use chrome-cdp engine (login-wall)
- For SDK/API pages: direct URL access works
- For Guide/Manual index: viewer URL + object.contentDocument extraction
- For Guide/Manual sub-pages: construct `contents/Pages/` URL and navigate directly
- Extract `#autoindex_content` for body, `.pagetitle` for title, `#contents_tree` for nav
- Clean up .page_navigation_top, <noscript>, .copyright, .confidential

## CDP Reference

```javascript
// Extract sub-page links from viewer
const obj = document.querySelector('object');
const cd = obj.contentDocument;
const links = Array.from(cd.querySelectorAll('a[href*="Pages/"]')).map(a => ({
  href: a.getAttribute('href'),
  text: a.textContent.trim()
}));

// Extract sub-page content (after nav to direct URL)
const content = document.querySelector('#autoindex_content').innerHTML;
const title = document.querySelector('.pagetitle')?.textContent || document.title;
```
