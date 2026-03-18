# WeChat Public Article Site Note Design

## Goal

Capture a reusable extraction pattern for publicly accessible WeChat article detail pages under `mp.weixin.qq.com/s/...`.

## Scope

In scope:

- public article detail pages
- title, author/account name, publish time, main content extraction
- inline image preservation in article body
- lightweight failure signals relevant to public article access

Out of scope:

- login-required pages
- anti-bot or risk-control bypass
- account management or comment interaction

## Proposed Output

Create a site note card under `sites/` that records:

- URL pattern
- page identity clues
- stable selectors observed in real runs
- extraction rules for text and images
- a recommended fast path for `Content Retrieval`
- a deeper evidence path for `Platform/Page Analysis`
- known failure signals and how to report them

## Design Choice

Use a compact “site extraction pattern card” instead of a run-specific case study.

This is the right format because the repository now distinguishes between fast content retrieval and deeper page analysis. The site note should help both workflows reuse the same validated structural knowledge.
