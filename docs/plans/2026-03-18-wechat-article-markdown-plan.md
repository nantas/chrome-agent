# WeChat Article Markdown Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update the browser-task workflow so article extraction preserves image links in-order, then regenerate the current WeChat article body in Markdown with inline image URLs.

**Architecture:** This change is documentation-first. Update the repo workflow contract in `AGENTS.md` so future browser runs extract article bodies as ordered Markdown nodes rather than plain `innerText`. Then rerun extraction against the current WeChat page by traversing `#js_content` and emitting text plus image nodes in DOM order.

**Tech Stack:** Markdown, `AGENTS.md`, `chrome-devtools-mcp` DOM evaluation, repository reports

---

### Task 1: Plan And Workflow Contract

**Files:**
- Create: `docs/plans/2026-03-18-wechat-article-markdown-plan.md`
- Modify: `AGENTS.md`

**Step 1: Document the requirement**

Write a short plan that names the new extraction contract:
- article outputs must preserve ordered text/image structure
- images must use real source URLs, not placeholders
- Markdown output should use `![图片N](URL)` or equivalent inline image link format

**Step 2: Update the workflow contract**

Add a rule under browser-task workflow/reporting guidance that says:
- when extracting article-style content, preserve DOM order
- do not replace images with generic placeholders such as “图片”
- if an image appears in the article body, output its real source URL in the generated正文

**Step 3: Verify the wording**

Run: `sed -n '1,260p' AGENTS.md`
Expected: the new article extraction rule is present and readable in the workflow requirements

### Task 2: Regenerate The Current WeChat Article

**Files:**
- Modify: `reports/2026-03-18-weixin-zelda-qa.md`

**Step 1: Extract ordered content nodes**

Use a browser DOM script against `#js_content` that:
- walks descendant nodes in document order
- emits paragraph text content when non-empty
- emits image nodes using `data-src` first, then `src`
- skips known promotional lead-in text before the article body when appropriate

**Step 2: Convert ordered nodes to Markdown**

Generate a Markdown body that:
- keeps text in reading order
- inserts images as `![图片N](URL)` at their original positions
- avoids generic image placeholders

**Step 3: Replace the old report body**

Update the report so the evidence and正文 sections describe the new extraction method and contain the Markdown output with inline image links.

**Step 4: Verify output**

Run:
- `sed -n '1,220p' reports/2026-03-18-weixin-zelda-qa.md`
- `ls -l reports/2026-03-18-weixin-article-page.png reports/2026-03-18-weixin-article-full.png`

Expected:
- the report contains `![图片` Markdown image entries
- screenshot evidence files still exist

