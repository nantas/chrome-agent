---
name: chrome-agent
description: Agent-first workflow skill for chrome-agent. Uses `chrome-agent doctor --format json` as preflight, then routes intent to the repo-backed CLI backend.
---

# Chrome Agent Workflow Skill

Use this skill as the recommended agent-facing entry for `chrome-agent`.

The skill is intent-facing. It does not implement scraping, crawl rules, or fallback logic itself. The only supported execution backend is the repo-backed `chrome-agent` CLI.

## Backend Contract

Always run backend preflight first:

```bash
chrome-agent doctor --format json
```

This preflight depends on the CLI's env-first repository contract:

- default repository source: `CHROME_AGENT_REPO`
- explicit override path: `--repo <path|repo://id>`
- missing or invalid env: stop and surface CLI remediation

Interpret the doctor result as the source of truth:

- If `result` is `success`, continue.
- If `result` is `failure`, stop.
- If `result` is `partial_success`, treat it as blocking for workflow dispatch and stop unless the doctor output clearly marks all failed checks as non-blocking.

When stopping, return the doctor-provided remediation instead of inventing a non-CLI fallback.

Required result fields to preserve from doctor:

- `result`
- `summary`
- `artifacts`
- `next_action`
- `repo_ref`
- `workflow`
- `engine_path`

### Doctor Freshness Checks

Doctor performs a repo freshness check by running `git fetch origin main` against the source repository and comparing HEAD with `origin/main`.

Doctor output includes these additional check items in `artifacts`:

- `repo_freshness` — whether the source repo is current with `origin/main`. Skipped (marked ok) on network failure, non-git repo, detached HEAD, or behind-but-no-tracked-files-changed.
- `global_skill_updated` — present only when auto-update was triggered. Indicates whether the global runtime and skill files were successfully updated.

When doctor returns `partial_success` and `next_action` contains a skill reload hint:

1. Inform the user that the global skill and runtime files have been auto-updated.
2. Advise the user to reload the skill (restart the session or re-read the skill file).
3. Do not proceed with the original workflow command until the skill is reloaded.

## Intent Routing

After doctor succeeds, route user intent to exactly one CLI workflow backend.

### Route to `fetch`

Use:

- content retrieval
- 正文抽取
- bare URL fetch
- concise failure explanation
- read/get/extract page content

Command:

```bash
chrome-agent fetch <target> --format json
```

### Route to `explore`

Use:

- analysis
- debugging
- evidence collection
- structure investigation
- anti-crawl rule inspection
- reproduction
- strategy coverage questions

Command:

```bash
chrome-agent explore <target> --format json
```

Treat `explore` as the CLI backend for Platform/Page Analysis.

### Route to `crawl`

Use:

- bounded multi-page traversal
- list expansion
- batch gap fill
- strategy-guided multi-page collection

Command:

```bash
chrome-agent crawl <target> --format json
```

If the request is not yet clearly bounded by declared strategy coverage, prefer `explore` first and return its remediation.

If the user reports problems with an existing crawl (e.g., "why did X fail?", "links are missing", "category assignment is wrong"), do NOT treat this as a new explore/strategy-gap case. Instead, follow the crawl problem triage methodology defined in `AGENTS.md` § "爬取问题系统化诊断与修复": classify issues as P-line (pipeline), S-line (strategy), or W-line (workflow); map to code capabilities; design and implement a systemic solution via openspec change; then verify against the target site.

## Agent Gate (Explore → Crawl Confirmation)

When `explore` returns `partial_success` with a strategy gap and the agent proceeds to sample conversion, the following Agent Gate rules are mandatory.

### 1. Self-check report BEFORE presentation

The agent SHALL run all S1-S12 self-checks and present the pass/fail summary BEFORE showing any sample Markdown content to the user.

- Output a summary table: `{check_id, status, detail}` for all S1-S12 checks across all samples.
- Output the overall pass rate (X/Y samples passed, Z issues total).
- Do NOT output raw Markdown content until the user has seen the self-check report.
- If all samples pass, state "✅ All samples passed" and present content.
- If any sample has failures, categorize them as fixable/non-fixable and present the remediation plan.

### 2. Sample file paths

The agent SHALL write all converted samples to files under `outputs/<run-tag>/` and present absolute file paths.

- File naming: `{page_type}-{page_title_slugified}.md`
- List all output file paths explicitly.
- Do NOT only print Markdown content to stdout without saving to files.

### 3. Agent self-audit

The agent SHALL perform a self-audit comparing source HTML against converted Markdown BEFORE asking the user to review.

- Compare: source `mw-headline` sections vs MD headings, source infobox fields vs MD table rows, source images vs MD `![]()` count, source `<a href="/wiki/">` count vs MD link count.
- Produce a structured discrepancy list before presenting to user.
- Do NOT delegate QA responsibility to the user.

### 4. Full retest on converter change

When the converter or extraction rules are modified, the agent SHALL re-convert and re-check ALL samples.

- Re-run `convert_body()` on ALL sample pages.
- Re-run ALL S1-S12 checks on ALL samples.
- Do NOT claim "fixed" based on a single sample test.

### 5. Iteration limit

The agent SHALL limit the fix→retest→present cycle to at most 3 iterations.

- After 3 cycles with remaining failures, present issues and ask user to decide: continue / accept / adjust scope.
- Do NOT continue to a 4th iteration without user confirmation.

### 6. Architecture Gate (strategy↔pipeline alignment)

The agent SHALL ensure the Architecture Gate passes before proceeding to user confirmation.

- The Architecture Gate runs AFTER self-check completes and BEFORE user confirmation.
- The gate checks two directions:
  - **Strategy→Pipeline**: Every strategy extraction field must have a corresponding consumer in the pipeline code (no dead config).
  - **Pipeline→Strategy**: Every site-specific value in the pipeline must be sourced from strategy config (no hardcoded selectors, domains, or patterns).
- If the gate returns `status: "fail"`:
  - The agent MUST fix all reported violations before presenting to the user.
  - Violation fixes do NOT count toward the 3-iteration limit (that limit is for quality issues, not architecture violations).
  - After fixing violations, the agent MUST re-run full sample conversion + self-check + Architecture Gate.
- If the gate returns `status: "pass"`:
  - Include "✅ Architecture Gate passed — no dead config, no hardcoded selectors" in the confirmation summary.

## Result Packaging

For routed commands, treat the CLI JSON result as the only source of truth.

Return or re-render these fields without changing their meaning:

- `result`
- `command`
- `target`
- `repo_ref`
- `summary`
- `artifacts`
- `next_action`
- `workflow`
- `engine_path`

Packaging rules:

- Do not claim success when the CLI returned `partial_success` or `failure`.
- Do not rewrite the backend workflow, engine path, or remediation into a conflicting interpretation.
- You may summarize the result for readability, but preserve artifact paths exactly.
- If the CLI reports a strategy gap, preflight issue, or fallback recommendation, surface that as-is.

Preferred final shape:

```text
result: <success|partial_success|failure>
command: <fetch|explore|crawl|doctor>
target: <url or runtime>
repo_ref: <repo://chrome-agent|path:...|env:CHROME_AGENT_REPO>
summary: <brief backend-grounded summary>
artifacts:
- <absolute path>
next_action: <none or remediation>
workflow: <content_retrieval|platform_analysis|runtime_support>
engine_path: <backend path summary>
```

## Route to Sample Conversion

When `explore` returns a matched strategy (result: `success`) and the agent needs
to convert sample pages, follow this standard path:

### API-based sites (strategy has `api.platform`)

Use the standalone sample converter CLI directly:

```bash
python3 scripts/explore/sample_converter.py fetch-and-apply \
  --strategy <path/to/strategy.md> \
  --page "<Page Title>" \
  --output <path/to/output.md>
```

Steps:
1. Read the matched strategy file from `explore` output
2. Select 3-7 representative sample pages from the strategy's taxonomy
3. For each sample, run `sample_converter.py fetch-and-apply`
4. Run self-check on converted samples (S1-S12 checks)
5. Present quality report before user confirmation

### Non-API sites (no `api.platform`)

Use the standard `chrome-agent fetch` command for content retrieval,
then apply strategy extraction rules manually if needed.

### Conversion flow note

- `sample_converter.py` reads extraction rules from the strategy file's YAML
  frontmatter (`extraction.*` fields) — no separate config needed
- The `fetch-and-apply` subcommand calls the MediaWiki `action=parse` API,
  then applies the same `_apply_extraction()` function as the explore pipeline
- Output is JSON `{"ok": true, "output": "...", "length": N}` or exits with
  code 1 and JSON error on failure

## Runtime Boundaries

- Do not depend on `repo-agent`, `codex-agent`, or any other prompt-forwarding runtime.
- Do not re-implement repository routing, engine selection, strategy matching, or fallback escalation inside the skill.
- Do not bypass `chrome-agent doctor --format json`.
- Do not treat the skill as a standalone scraper runtime; it is a CLI-backed orchestration layer only.

## Install Notes

Repository source of truth:

- `skills/chrome-agent/SKILL.md`

Recommended global install destination:

- `~/.agents/skills/chrome-agent/`

Install and update guidance must present:

- the global workflow skill as the recommended agent-facing entry
- the global `chrome-agent` CLI as the required backend prerequisite
- the skill as delegating to the CLI rather than replacing it
- `CHROME_AGENT_REPO` as the default backend repository prerequisite
- `--repo <path|repo://id>` as the explicit non-default override path

### 7. KI Lifecycle Gate (post-Architecture Gate)

After the Architecture Gate passes, the agent SHALL run the KI Lifecycle phase to manage Known Issues systematically.

- The KI Lifecycle phase uses `scripts/explore/ki_lifecycle.py` for classification, prioritization, status tracking, and batch planning.
- **Classification**: Every self-check failure SHALL be classified by owner domain (strategy/pipeline/self_check) using `classify_ki()`.
- **Prioritization**: Every KI SHALL be assigned P0-P3 priority using `assign_priority()`. Contextual overrides via `priority_override` field are allowed.
- **Status tracking**: KI status SHALL follow the state machine: open → in_progress → (resolved|wontfix|open_systemic) using `transition_status()`.
- **Fix order**: KI fixes SHALL be applied in P0→P1→P2 batches. Each batch = 1 iteration. Max 3 iterations.
- **Documentation**: The KI table in strategy.md SHALL be updated to the 7-column schema (ID/Issue/Status/Priority/Owner/Impact/Resolution) after any status change.
