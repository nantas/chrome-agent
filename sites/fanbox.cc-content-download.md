# pixivFANBOX - Content Retrieval & Download

## Scope

This note covers authenticated content retrieval and file download from pixivFANBOX creator pages:

- Creator post list pages: `https://<creatorId>.fanbox.cc/posts`
- Post detail pages: `https://www.fanbox.cc/@<creatorId>/posts/<postId>`
- File download endpoint: `https://downloads.fanbox.cc/files/post/<postId>/<fileId>.<ext>`

It does not cover:

- Creator account management
- Payment or plan management
- Upload or write actions
- Anti-bot bypass without a valid session

## Requirements

- **Authenticated session required**: A logged-in FANBOX session with an active `FANBOXSESSID` cookie
- **Tool path**: `chrome-cdp` skill (live Chrome session with user's logged-in state)
- **Email verification must be current**: FANBOX enforces email re-verification when `isMailAddressOutdated` is true; accessing post details redirects to `/email/reactivate` until resolved

## Page Structure

### Post List Page (`/@<creatorId>/posts`)

- **Title**: `投稿列表｜<CreatorName>｜pixivFANBOX`
- **Creator info section**: name, tags (e.g. "3D"), sponsor status ("正在赞助")
- **Sub-navigation**: 个人资料 / 投稿 / 方案 / 商店
- **Sort controls**: 按最新排序 / 按旧排序, 单列显示 toggle
- **Post cards** (each contains):
  - Publish date (e.g. `2026年3月31日 22:25`)
  - Price/access level (e.g. `500日元` or `对所有人公开`)
  - Post title
  - Body text excerpt (truncated)
  - Like count + comment count (buttons)
- **Pagination**: numbered page links at bottom (1, 2, 3, ...)
- **Footer**: recommended creators, site links

### Post Detail Page (`/@<creatorId>/posts/<postId>`)

- **Title**: `<postTitle>｜<CreatorName>｜pixivFANBOX`
- **Post metadata**: date, price/plan level
- **Attached files** (images and videos):
  - Each file shown as a card with:
    - Filename and extension
    - File size
    - Download link/button (e.g. `下载(292MB)`)
  - Videos have an inline player with play/pause, volume, fullscreen controls
- **Post body**: full text in Japanese (often with English and Chinese translations)
- **Interaction section**: like count, comment count, share links
- **Comments section**: user comments with timestamps and like counts
- **Sidebar**: adjacent posts, creator plan info

## Authentication

### Cookie-Based Download

The download endpoint `downloads.fanbox.cc` requires authentication via cookies.

**Key cookies**:

| Cookie | Purpose |
|--------|---------|
| `FANBOXSESSID` | Primary session auth (httpOnly, secure) |
| `p_ab_id` | AB test ID |
| `p_ab_id_2` | AB test ID variant |
| `p_ab_d_id` | Device AB test ID |

**Required headers for curl download**:

```
Cookie: FANBOXSESSID=<value>; p_ab_id=0; p_ab_id_2=7; p_ab_d_id=<value>
Referer: https://www.fanbox.cc/
User-Agent: <standard Chrome UA string>
```

### Extracting Cookies from Live Session

Use CDP `Network.getCookies` to extract cookies for the download domain:

```bash
node scripts/cdp.mjs evalraw <target> 'Network.getCookies' '{"urls":["https://downloads.fanbox.cc"]}'
```

The `FANBOXSESSID` is the critical cookie for file download authorization.

## Content Extraction Pattern

### Step 1: Navigate to Post List

```bash
node scripts/cdp.mjs nav <target> "https://www.fanbox.cc/@<creatorId>/posts"
```

### Step 2: Identify Posts with Files

Take an accessibility snapshot to enumerate post cards:

```bash
node scripts/cdp.mjs snap <target>
```

Look for:
- Posts with video files (`.mp4` in card text)
- Posts with download buttons and file sizes
- Date strings for month-based categorization

### Step 3: Enter Post Detail

Extract post URL from list and navigate:

```bash
node scripts/cdp.mjs eval <target> 'Array.from(document.querySelectorAll("a")).filter(a => a.textContent.includes("<postTitle>"))[0].href'
node scripts/cdp.mjs nav <target> "<postUrl>"
```

### Step 4: Extract Download URLs

For video files:

```bash
node scripts/cdp.mjs eval <target> '
  Array.from(document.querySelectorAll("a"))
    .filter(a => a.textContent.includes("下载") && a.href.includes(".mp4"))
    .map(a => ({href: a.href, text: a.textContent.trim()}))
'
```

For image files, same pattern but filter for `.png`, `.jpg`, etc.

### Step 5: Download Files

```bash
curl -L -o "<outputPath>" \
  -H "Cookie: FANBOXSESSID=<sessid>; p_ab_id=0; p_ab_id_2=7; p_ab_d_id=<d_id>" \
  -H "Referer: https://www.fanbox.cc/" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36" \
  "<downloadUrl>"
```

## Month-Based Categorization

Post dates are in format `YYYY年M月D日 HH:MM`. Organize downloads by post month:

```
/Volumes/Shuttle/downloads/
  2026-02/
    project ULALA JP2moz.mp4
  2026-03/
    ...
```

To extract the month from a post card in the list:

```javascript
// Date text format: "2026年2月26日 19:45"
const dateText = card.querySelector('[some date selector]').textContent;
// Parse to "2026-02" format
```

## API Rate Limiting

FANBOX API (`api.fanbox.cc`) enforces rate limiting that results in `TypeError: Failed to fetch` errors. Once triggered, all subsequent API requests from the same session fail until the cooldown expires.

### Observed Limits (2026-04-04)

| Metric | Value | Evidence |
|--------|-------|----------|
| **Burst threshold** | ~80-100 calls within 10 min | 95 calls in ~6 min triggered limit (NFO gen session 2) |
| **Recovery time** | ~2.5-3 hours | Limit at ~03:42, recovered by ~06:32 (170 min gap) |
| **Safe sustained rate** | ~8-10 calls/min | 95 calls with 3s delay lasted ~6 min before hitting limit |
| **Error symptom** | `TypeError: Failed to fetch` | Browser `fetch()` returns network error, no HTTP response |

### Rate Limit Events

**Event 1** (~03:42):
- Download session made ~100-200 API calls over ~2 hours (with long gaps during file downloads)
- First NFO generation attempt added 2 more calls, pushing total over the threshold
- Only 1 NFO was generated before all subsequent calls failed

**Event 2** (~06:38):
- After ~170 min cooldown, API confirmed working again
- NFO generation script processed 95 posts with 3s delay between calls (~6 min total)
- Rate limit triggered again on the 96th-98th calls
- 3 posts (750722, 730697, 680036) failed — but these had no matching local directories, so no NFOs were missed

### Mitigation Strategy

- **Minimum delay**: 3 seconds between API calls (current default in scripts)
- **Safer delay**: 5 seconds for long batch operations (reduces burst to ~12 calls/min)
- **Checkpoint progress**: Save completed items to a progress file after each successful call
- **Resumable runs**: Scripts should skip already-completed items on re-run
- **Monitor for failures**: If `Failed to fetch` appears, stop immediately — retries will not help until cooldown expires
- **Recovery**: Wait at least 3 hours before retrying after rate limit detection

## Known Issues

### Email Verification Redirect

- **Symptom**: Clicking a post detail link redirects to `/email/reactivate`
- **Cause**: `isMailAddressOutdated: true` in session metadata
- **Fix**: User must click the verification link sent to their email, then return to FANBOX
- **Detection**: Check page title for `确认邮箱地址` or URL contains `/email/reactivate`

### Daemon Reconnection

- The CDP daemon may drop after inactivity or when the Allow prompt reappears
- Running `node scripts/cdp.mjs list` tests connectivity
- If it fails, user needs to click "Allow debugging" in Chrome again

### File Size Limits

- FANBOX attachment limit: 30MB per file
- Creators sometimes provide external links (e.g. Vimeo) for larger files
- Some posts mention password-protected downloads for external hosting

## Access Levels

| Label | Meaning |
|-------|---------|
| `对所有人公开` | Public - no payment required |
| `500日元` | Silver plan (500 JPY/month) |
| `1,000日元` | Gold plan (1000 JPY/month) |

Download access requires an active sponsorship at the appropriate tier.

## Batch Download

### Script: `scripts/fanbox-download-videos.mjs`

A batch download script exists for bulk video extraction from a creator's posts. It:

1. Navigates through all post list pages via `?page=N` URL parameter
2. Extracts post IDs from each page's DOM
3. Fetches each post's detail via the FANBOX API (called inside the browser via CDP eval)
4. Filters for video files only (mp4, wmv, avi, mov, mkv, webm, mpg, mpeg)
5. Downloads each video with curl using `FANBOXSESSID` cookie
6. Saves files to `<BASE_DIR>/<YYYY-MM>/<filename>.<ext>`
7. Tracks progress in `scripts/fanbox-download-progress.json` (resumable)

**Usage**:

```bash
node scripts/fanbox-download-videos.mjs
```

**Prerequisites**:
- Chrome with remote debugging enabled and a FANBOX tab open
- User has clicked "Allow debugging" in Chrome
- Valid authenticated FANBOX session

**Configuration** (at top of script):
- `CREATOR_ID`: FANBOX creator ID (default: `atdfb`)
- `BASE_DIR`: download destination (default: `/Volumes/Shuttle/downloads`)
- `CUTOFF_DATE`: stop processing posts before this date (default: `2021-06-01`)
- `MAX_PAGES`: maximum pages to scan (default: `10`)
- `VIDEO_EXTS`: file extensions to download

**Resumability**: The script saves processed post IDs to a progress JSON file. Re-running skips already-processed posts and existing files (size-checked).

### FANBOX API Notes

**Post list API** (`https://api.fanbox.cc/post.listCreator`):
- Must be called from within the browser (via `fetch` with `credentials:"include"`) — direct HTTP requests are blocked by Cloudflare
- Query parameters: `creatorId`, `limit`, `page` (page parameter does NOT work for pagination)
- Cursor-based pagination (`maxPublishedDatetime` + `maxId`) also does not reliably work
- **Workaround**: Navigate the browser to `https://www.fanbox.cc/@<creatorId>/posts?page=N` and scrape post IDs from the DOM

**Post detail API** (`https://api.fanbox.cc/post.info?postId=<id>`):
- Works via browser `fetch` with `credentials:"include"`
- Response body structure depends on `post.type`:
  - `"file"` type: `body.files[]` array with `{name, extension, size, url}`
  - `"article"` type: `body.blocks[]` with `type:"file"` referencing `body.files[]` by `fileId`
  - `"image"` type: `body.images[]` only, no videos expected
- Video download URLs point to `https://downloads.fanbox.cc/files/post/<postId>/<fileId>.<ext>`

### Shell Escaping for CDP eval

When passing JavaScript expressions to `cdp.mjs eval`, be aware:
- Use **single quotes** around the expression (not JSON.stringify) to avoid double-escaping
- Avoid regex literals — use `includes()` / `split()` / `new RegExp()` with simple strings instead
- Regex backslash escaping gets mangled by shell + JSON double-encoding

```javascript
// GOOD: use string operations
document.querySelectorAll("a").forEach(a => {
  if (a.href && a.href.includes("/@atdfb/posts/")) {
    const parts = a.href.split("/@atdfb/posts/");
    if (parts.length > 1) ids.add(parts[1].split(/[?#]/)[0]);
  }
});

// BAD: regex literals break due to escaping
a.href.match(/fanbox\.cc\/@atdfb\/posts\/(\d+)/)
```

### CDP Daemon Stability

- `cdp.mjs nav` disconnects the daemon — always `findTarget()` again after navigation
- After `nav`, wait at least 5 seconds (sync `sleep 5`) before eval
- The "Allow debugging" prompt may reappear after navigation — user must click it
- Daemon auto-exits after 20 minutes of inactivity

## Validated Run Notes

### Single file download test (2026-04-04)

- **Creator**: ATD (`@atdfb`)
- **Test post**: `project ULALA JP2` (post ID `11468835`, 2026-02-26)
- **Downloaded file**: `project ULALA JP2moz.mp4` (279MB, MP4 v2)
- **Saved to**: `/Volumes/Shuttle/downloads/2026-02/`
- **Download method**: curl with `FANBOXSESSID` cookie extracted via CDP `Network.getCookies`
- **Download speed**: ~30s for 279MB over local network
- **File integrity**: confirmed via `file` command (ISO Media, MP4 v2)

### Batch download run (2026-04-04)

- **Creator**: ATD (`@atdfb`)
- **Script**: `scripts/fanbox-download-videos.mjs`
- **Report**: `reports/fanbox-atdfb-batch-download-2026-04-04.md`
- **Scope**: 100 posts (newest to ~2021-06)
- **Posts with video**: 72
- **Total video files**: 90 mp4 files
- **Total size**: ~23GB
- **Failures**: 0
- **Run duration**: ~2 hours (split across 2 sessions due to timeout)
- **Date range covered**: 2021-06 to 2026-03
- **Month directories created**: 42 (2021-06 through 2026-03)
- **Key learnings**:
  - FANBOX API `page` and `offset` parameters do not work for pagination — DOM scraping required
  - Each post detail API call must go through the browser (Cloudflare blocks direct requests)
  - Shell escaping for CDP eval is tricky — avoid regex literals
  - Progress file enables resumable downloads across sessions
  - File size comparison (`Math.abs(local - remote) < 1024`) reliably detects existing downloads
