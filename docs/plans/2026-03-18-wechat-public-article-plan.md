# WeChat Public Article Site Note Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a reusable site note for public WeChat article detail pages so future runs can extract content faster and more consistently.

**Architecture:** Create a compact note in `sites/` that captures the validated URL pattern, selectors, extraction order, image handling, workflow-specific guidance, and failure signals. Then update the `sites/README.md` index so the note is discoverable.

**Tech Stack:** Markdown, `sites/`, repository workflow docs

---

### Task 1: Add The Site Extraction Card

**Files:**
- Create: `sites/wechat-public-article.md`

**Step 1: Record page identity and scope**

Document:

- the `mp.weixin.qq.com/s/...` URL pattern
- that the note covers public article detail pages only
- the validated fields: title, author/account, publish time, main body, images

**Step 2: Record extraction rules**

Document:

- `#js_content` as the primary article body root
- title and metadata selectors observed in real runs
- DOM-order traversal requirement
- inline Markdown image rule using real image URLs

**Step 3: Record workflow-specific usage**

Document:

- the recommended fast path for `Content Retrieval`
- the recommended evidence path for `Platform/Page Analysis`
- known failure signals worth reporting directly

### Task 2: Index The New Site Note

**Files:**
- Modify: `sites/README.md`

**Step 1: Add an entry for the WeChat note**

Add a short list entry pointing to the new file and what it covers.

**Step 2: Verify the new files**

Run:

- `sed -n '1,220p' sites/wechat-public-article.md`
- `sed -n '1,120p' sites/README.md`

Expected:

- the site note contains selectors, extraction rules, and failure signals
- the README references the new note
