# Chrome Agent Global Install Playbook

## Goal

Install the repo-backed global `chrome-agent` CLI launcher, install the global workflow skill on top of it, and validate that the backend can resolve the default `CHROME_AGENT_REPO` repository, dispatch into the repository, and report remediation clearly when an explicit override is needed.

## Source and Destination

- runtime source: `scripts/chrome-agent-runtime.mjs`
- workflow skill source: `skills/chrome-agent/SKILL.md`
- installer: `scripts/install-chrome-agent-cli.sh`
- runtime destination: `~/.agents/scripts/chrome-agent.mjs`
- user-facing shim: `~/.local/bin/chrome-agent`
- workflow skill destination: `~/.agents/skills/chrome-agent/SKILL.md`
- default repository locator: `CHROME_AGENT_REPO`
- explicit repo-ref locator: `--repo repo://chrome-agent`

## Decision Points

Before any persistent write, inspect:

- whether `~/.agents/scripts/chrome-agent.mjs` already exists
- whether `~/.local/bin/chrome-agent` already exists
- whether `~/.agents/skills/chrome-agent/SKILL.md` already exists
- whether `CHROME_AGENT_REPO` is already set in the current shell or shell config
- whether any existing `CHROME_AGENT_REPO` value already matches the current repository path

If an existing launcher path or conflicting environment variable is found, stop and ask for confirmation before changing it.

## Inspect Current State

Check whether the runtime and shim already exist:

```bash
ls -ld ~/.agents/scripts/chrome-agent.mjs ~/.local/bin/chrome-agent ~/.agents/skills/chrome-agent/SKILL.md
```

Check the current environment default value:

```bash
printf '%s\n' "$CHROME_AGENT_REPO"
```

Check common shell config files for an existing definition:

```bash
rg -n '^export CHROME_AGENT_REPO=' ~/.zshrc ~/.zprofile ~/.bashrc ~/.bash_profile 2>/dev/null
```

Check the current repository absolute path:

```bash
pwd
```

## Install Workflow

### Case 1: Fresh install

Install the CLI runtime and shim:

```bash
./scripts/install-chrome-agent-cli.sh
```

Then install the workflow skill:

```bash
mkdir -p ~/.agents/skills/chrome-agent
cp skills/chrome-agent/SKILL.md ~/.agents/skills/chrome-agent/SKILL.md
```

### Case 2: Launcher or skill already exists

Do not overwrite blindly. First compare and confirm. If replacement is approved, re-run the installer after removing or backing up the existing launcher paths, then update the installed skill file explicitly.

### Case 3: `CHROME_AGENT_REPO` missing and default path not ready

After user approval, append the current repository path to the active shell config. Example for `zsh`:

```bash
printf '\nexport CHROME_AGENT_REPO="%s"\n' "$PWD" >> ~/.zshrc
```

### Case 4: `CHROME_AGENT_REPO` already matches

Do not rewrite it. Report that the environment variable is already configured correctly.

### Case 5: `CHROME_AGENT_REPO` conflicts

Do not replace it silently. Ask whether to update it. If approved, replace the existing shell-config line manually and reload the shell later.

### Case 6: Manually sync global copies (ahead of origin, or immediate-effect needed)

Auto-update (see Version Freshness Check) only fires when the source repo is **behind** `origin/main` AND a tracked file differs. When local HEAD is **ahead** (unpushed commits) or you want changes to take effect without waiting for the next `doctor`, sync manually with four steps:

```bash
# 1. runtime -> ~/.agents/scripts/chrome-agent.mjs (make it executable)
cp scripts/chrome-agent-runtime.mjs ~/.agents/scripts/chrome-agent.mjs
chmod +x ~/.agents/scripts/chrome-agent.mjs

# 2. skill -> ~/.agents/skills/chrome-agent/SKILL.md
cp skills/chrome-agent/SKILL.md ~/.agents/skills/chrome-agent/SKILL.md

# 3. refresh installed-hash to the current HEAD (NOT a content hash)
git rev-parse HEAD > ~/.agents/scripts/.chrome-agent-installed-hash

# 4. validate, then reload the skill (restart session) since SKILL.md changed
chrome-agent doctor --format json
```

Why manual sync is needed when ahead: doctor reports `repo_freshness` as `ahead` and ok, so it does NOT auto-update, yet the global copies are stale relative to local HEAD. Alternatively, `git push` first so the normal behind-path applies on other machines.

## Validation

After installation, verify:

```bash
test -x ~/.local/bin/chrome-agent && echo shim_ok
test -f ~/.agents/scripts/chrome-agent.mjs && echo runtime_ok
test -f ~/.agents/skills/chrome-agent/SKILL.md && echo skill_ok
chrome-agent doctor --format json
```

Expected result:

- `shim_ok`
- `runtime_ok`
- `skill_ok`
- doctor result with `success` or a clearly scoped `partial_success`/`failure` remediation
- doctor output includes `repo_freshness` check (ok when source repo is current with `origin/main`)

## Version Freshness Check

`chrome-agent doctor` automatically checks whether the source repository is current with `origin/main` by running `git fetch origin main` (timeout: 10 seconds).

Behavior:

- **Source repo current** (`HEAD == origin/main`): `repo_freshness` check is ok. No action needed.
- **Source repo AHEAD of `origin/main`** (unpushed local commits): `repo_freshness` reports `ahead: …` and is ok. Auto-update does NOT fire, but the global copies are stale relative to local HEAD — sync manually (see Case 6) or `git push` first so the normal behind-path applies on other machines.
- **Source repo behind with tracked file changes**: doctor auto-updates global runtime (`~/.agents/scripts/chrome-agent.mjs`) and skill (`~/.agents/skills/chrome-agent/SKILL.md`), refreshes the installed-hash to the current HEAD (see Installed Hash Semantics), and returns `partial_success` with a skill reload hint.
- **Source repo behind but no tracked files changed**: `repo_freshness` is ok. The `behind but no tracked files changed` detail indicates no update is needed.
- **Network failure / non-git repo / detached HEAD**: check is skipped (marked ok). Does not block workflow.

Tracked files for auto-update:

- `scripts/chrome-agent-runtime.mjs`
- `scripts/chrome-agent-cli.mjs`
- `skills/chrome-agent/SKILL.md`

Note: `scripts/chrome-agent-cli.mjs` is a **trigger**, not a copy destination. When it changes, doctor / manual sync re-copies `chrome-agent-runtime.mjs` to `~/.agents/scripts/chrome-agent.mjs` — the cli file itself is never copied globally. This is why a cli change forces a runtime refresh.

## Installed Hash Semantics

`~/.agents/scripts/.chrome-agent-installed-hash` records the commit SHA captured at the last sync. Its value equals `git rev-parse HEAD` — it is **not** a hash of file contents. Confusion often arises when the global file sha1 already matches the source but this hash file still points at an older commit.

- It seeds `doctor`'s incremental freshness check (the behind-vs-tracked-files decision).
- Any manual sync (Case 6) MUST refresh it, otherwise subsequent `doctor` runs may misjudge freshness.

When doctor returns `partial_success` with a skill reload hint, the operator must reload the skill (restart the session or re-read the skill file) before proceeding.

## Operator Notes

- Starting installation from a single prompt is fine.
- The operator must still inspect existing `CHROME_AGENT_REPO` state before persisting shell configuration.
- The operator must treat `CHROME_AGENT_REPO` as the default runtime prerequisite.
- Persistent changes to launcher paths or shell config must remain explicit and reviewable.
- The workflow skill is the recommended agent-facing entry, but it depends on the CLI backend rather than replacing it.
- Do not document `repo-agent`, `codex-agent`, or any other prompt-forwarding dispatcher as part of the supported install chain.
