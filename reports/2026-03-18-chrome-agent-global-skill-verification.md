# Chrome Agent Global Skill Verification

## Goal

Verify that the planned dispatcher contract is practical with both `codex-agent` and `repo-agent`.

## Environment

- Worktree: `/Users/nantas-agent/projects/chrome-agent/.worktrees/chrome-agent-global-skill`
- Dispatcher skills:
  - `~/.agents/skills/codex-agent/`: present
  - `~/.agents/skills/repo-agent/`: present
- Runtime env var:
  - `CHROME_AGENT_REPO`: unset in the parent shell during verification

## Dry-Run Prompt

Both dispatchers were tested with this prompt shape:

```text
Read AGENTS.md in the target repository and execute this webpage extraction request according to the repository workflow.
User request: fetch the main content from https://example.com .
Return the final outcome exactly in this shape:
result: <success|partial_success|failure>
target: <url or page identifier>
summary: <brief result summary>
artifacts:
- <absolute path>
next_action: <none or recommended next step>
```

## `codex-agent` Path

Command:

```bash
project_dir="/Users/nantas-agent/projects/chrome-agent/.worktrees/chrome-agent-global-skill"
codex exec -C "$project_dir" -s danger-full-access --ephemeral -c "projects.\"$project_dir\".trust_level=\"trusted\"" "<prompt>"
```

Observed outcome:

- returned the required `result/target/summary/artifacts/next_action` block
- successfully extracted `https://example.com/`
- saved artifact:
  - `/Users/nantas-agent/projects/chrome-agent/.worktrees/chrome-agent-global-skill/reports/example.com-20260318-213240.md`

Observed gap:

- the final result block was preceded by execution logs
- because `CHROME_AGENT_REPO` was unset, the downstream run improvised a direct in-repo fallback based on current working directory

Contract refinement taken:

- require the result block to be the final block in the response
- explicitly forbid current-directory fallback when `CHROME_AGENT_REPO` is missing or invalid

## `repo-agent` Path

Command:

```bash
opencode run --dir /Users/nantas-agent/projects/chrome-agent/.worktrees/chrome-agent-global-skill --agent cli "<prompt>"
```

Observed outcome:

- returned the required `result/target/summary/artifacts/next_action` block
- successfully extracted `https://example.com/`
- saved artifact:
  - `/Users/nantas-agent/projects/chrome-agent/.worktrees/chrome-agent-global-skill/reports/2026-03-18-example-com-content-retrieval.md`

Observed gap:

- the command wrapper emitted status lines before the final result block

Contract refinement taken:

- parent-session parsing should consume the last required result block
- downstream prompt now requires that no additional commentary follow the final result block

## Conclusion

The dispatcher contract is practical with both downstream agent paths.

Required safeguards after verification:

- `codex-agent` remains the primary dispatcher
- `repo-agent` remains the fallback dispatcher
- `CHROME_AGENT_REPO` must remain mandatory
- the final result block must be emitted last for reliable parsing
