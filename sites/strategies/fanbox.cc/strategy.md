---
domain: fanbox.cc
description: pixivFANBOX authenticated content retrieval and file download
protection_level: authenticated
anti_crawl_refs:
  - cookie-auth-session
  - rate-limit-api
structure:
  pages:
    - id: creator_post_list
      label: Creator Post List
      url_pattern: /@:creatorId/posts
      url_example: https://www.fanbox.cc/@atdfb/posts
      type: dynamic_list
      content_type: post_card
      pagination:
        mechanism: url_parameter
        parameter: page
        start: 1
      links_to:
        - target: post_detail
          selector: a[href*="/posts/"]
      requires_auth: false
    - id: post_detail
      label: Post Detail
      url_pattern: /@:creatorId/posts/:postId
      url_example: https://www.fanbox.cc/@atdfb/posts/11468835
      type: dynamic_content
      content_type: article_with_attachments
      pagination: none
      links_to: []
      requires_auth: true
    - id: file_download
      label: File Download
      url_pattern: https://downloads.fanbox.cc/files/post/:postId/:fileId.:ext
      url_example: https://downloads.fanbox.cc/files/post/11468835/abc123.mp4
      type: binary_file
      content_type: binary_file
      pagination: none
      links_to: []
      requires_auth: true
  entry_points:
    - creator_post_list
extraction:
  image_handling:
    attribute: src
    output_format: markdown_inline
---

## Overview

pixivFANBOX is a creator subscription platform with authenticated content. Access requires a valid `FANBOXSESSID` cookie from a logged-in session. The site has three main page types: post list, post detail, and file download.

## Page Structure

### Creator Post List (`/@<creatorId>/posts`)

- Title: `投稿列表｜<CreatorName>｜pixivFANBOX`.
- Displays post cards with: publish date, price/access level, post title, body excerpt, like/comment counts.
- Pagination via `?page=N` URL parameter. FANBOX API page parameter does not work — DOM scraping is required for pagination.
- Sub-navigation: 个人资料 / 投稿 / 方案 / 商店.

### Post Detail (`/@<creatorId>/posts/<postId>`)

- Title: `<postTitle>｜<CreatorName>｜pixivFANBOX`.
- Shows post metadata: date, price/plan level.
- Attached files (images/videos) shown as cards with filename, size, download link.
- Videos have inline player.
- Full post body text.
- Interaction: like/comment counts, comments section.

### File Download (`downloads.fanbox.cc/files/post/...`)

- Binary file endpoint requiring `FANBOXSESSID` cookie.
- File sizes up to 30MB (FANBOX limit).

## Extraction Flow

1. Open the creator post list page via `chrome-cdp` (requires authenticated session).
2. Enumerate post cards from accessibility snapshot or DOM.
3. For each post with downloadable files (look for `.mp4`, download buttons, file sizes):
   a. Navigate to post detail page.
   b. Extract download URLs from DOM.
4. Download files using curl with `FANBOXSESSID` cookie and proper headers.
5. Organize downloads by month: `<BASE_DIR>/<YYYY-MM>/`.
6. Track progress in a JSON file for resumable runs.

## Authentication

- Requires `FANBOXSESSID` cookie (httpOnly, secure).
- Extract cookie via CDP: `Network.getCookies` with `{"urls":["https://downloads.fanbox.cc"]}`.
- Email verification must be current. If `isMailAddressOutdated` is true, accessing post details redirects to `/email/reactivate`.
- Download headers: `Cookie`, `Referer: https://www.fanbox.cc/`, Chrome UA.

## Rate Limiting

- FANBOX API enforces rate limiting on `api.fanbox.cc`.
- Burst threshold: ~80-100 calls within 10 min.
- Recovery time: ~2.5-3 hours.
- Safe rate: ~8-10 calls/min with 3-5s delay.
- Error: `TypeError: Failed to fetch` — stop immediately, retries won't help until cooldown.
- See `sites/anti-crawl/rate-limit-api.md` for full details.

## Known Issues

- Post list API `page` parameter does not work — must scrape DOM.
- CDP daemon may drop after inactivity; "Allow debugging" prompt may reappear.
- Some creators provide external links (Vimeo) for files exceeding FANBOX 30MB limit.
- Shell escaping for CDP eval is tricky — avoid regex literals, use `includes()`/`split()`.

## Evidence

- Single file download test (2026-04-04): `project ULALA JP2moz.mp4` (279MB).
- Batch download run (2026-04-04): 72 posts with video, 90 mp4 files, ~23GB, 0 failures.
- Reports: `reports/fanbox-atdfb-batch-download-2026-04-04.md`.
- Script: `_attachments/fanbox-download-videos.mjs`.
