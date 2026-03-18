# WeChat Public Article

## Scope

This note covers publicly accessible WeChat article detail pages under URLs like:

- `https://mp.weixin.qq.com/s/<id>`

It does not cover:

- login-required pages
- account management pages
- comments or write actions
- anti-bot or risk-control bypass

## Validated Page Identity

Observed on a real run:

- host: `mp.weixin.qq.com`
- path shape: `/s/<id>`
- page title is available in the document title and article header
- article body is rendered in-page and can be read without login when the page is public

## Useful Selectors

These selectors were validated during extraction of a public article detail page.

- title:
  - `#activity-name`
  - fallback: `h1`
- author or account name:
  - `#js_name`
  - fallback: `#js_author_name`
- publish time:
  - `#publish_time`
- article body root:
  - `#js_content`

## Extraction Pattern

For public article detail pages, do not rely on plain `innerText` for the final正文 output when images matter.

Preferred pattern:

1. Find `#js_content`
2. Walk the body in DOM order
3. Emit non-empty text blocks in reading order
4. Emit image nodes using:
   - `data-src` first
   - fallback to `src`
5. Keep images in-place using Markdown syntax such as:
   - `![图片1](https://...)`
6. Avoid replacing images with generic placeholders such as `图片`

## Content Retrieval Path

Use this when the user gives a WeChat article URL and primarily wants the content.

Recommended fast path:

1. Open the page
2. Verify page identity with title and URL
3. Extract:
   - title
   - author/account name
   - publish time
   - body from `#js_content`
4. For article body output:
   - preserve DOM order
   - preserve inline image URLs
5. Return content directly unless the user asked for a saved report

Lightweight verification is usually enough:

- final URL
- page title
- body extracted or explicit failure reason

## Page Analysis Path

Use this when the prompt asks for analysis, debugging, evidence, structure, or reusable platform knowledge.

Recommended deeper path:

1. Open the page
2. Capture title and URL
3. Capture a structure clue such as an accessibility snapshot or DOM summary
4. Capture at least one screenshot
5. Extract the article body in DOM order with inline image URLs
6. Save a report under `reports/`
7. Update `sites/` if the run validates or changes the pattern

## Body Cleanup Notes

Public WeChat articles can include lead-in promotional content before the main article body.

Observed example:

- subscription prompts
- account IDs
- profile promo text

When extracting正文, prefer to start at the first clearly article-specific paragraph rather than blindly returning all leading promo content.

This cleanup should be conservative:

- remove obvious lead-in promo only when it is clearly outside the article
- do not drop article images or body paragraphs once the article has started

## Known Failure Signals

For this public-article scope, report failures directly when you observe:

- page opens but `#js_content` is missing
- title/metadata load but article body is empty
- navigation resolves somewhere other than the article URL
- the browser lands on an error, redirect, or unavailable page instead of the article

When failure occurs, report:

- final URL
- visible page title or error state
- whether `#js_content` existed
- whether body text or images were present

## Notes From The Validated Run

Observed on the validated article run:

- the article was readable without login
- the page title matched the article heading
- `#js_content` contained text and inline images
- image URLs were available from article image elements and could be preserved in Markdown output
- `innerText` alone was insufficient because it dropped image links from the final正文
