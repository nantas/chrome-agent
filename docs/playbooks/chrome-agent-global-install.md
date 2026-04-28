# Chrome Agent Global Install Playbook

## Goal

Install the repo-backed global `chrome-agent` CLI launcher and validate that it can resolve `repo://chrome-agent`, dispatch into the repository, and report remediation clearly when fallback is needed.

## Source and Destination

- runtime source: `scripts/chrome-agent-runtime.mjs`
- installer: `scripts/install-chrome-agent-cli.sh`
- runtime destination: `~/.agents/scripts/chrome-agent.mjs`
- user-facing shim: `~/.local/bin/chrome-agent`
- primary repository locator: `repo://chrome-agent` via repo-registry
- fallback repository locator: `CHROME_AGENT_REPO`

## Decision Points

Before any persistent write, inspect:

- whether `~/.agents/scripts/chrome-agent.mjs` already exists
- whether `~/.local/bin/chrome-agent` already exists
- whether `repo://chrome-agent` is already registered in repo-registry
- whether `CHROME_AGENT_REPO` is already set in the current shell or shell config
- whether any existing `CHROME_AGENT_REPO` value already matches the current repository path

If an existing launcher path or conflicting environment variable is found, stop and ask for confirmation before changing it.

## Inspect Current State

Check whether the runtime and shim already exist:

```bash
ls -ld ~/.agents/scripts/chrome-agent.mjs ~/.local/bin/chrome-agent
```

Check repo-registry resolution first:

```bash
python3 "$HOME/.agents/scripts/repo-registry.py" resolve --repo-ref 'repo://chrome-agent'
```

Check the current environment fallback value:

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

Install the runtime and shim:

```bash
./scripts/install-chrome-agent-cli.sh
```

### Case 2: Launcher already exists

Do not overwrite blindly. First compare and confirm. If replacement is approved, re-run the installer after removing or backing up the existing launcher paths.

### Case 3: repo-registry missing, `CHROME_AGENT_REPO` fallback needed

After user approval, append the current repository path to the active shell config. Example for `zsh`:

```bash
printf '\nexport CHROME_AGENT_REPO="%s"\n' "$PWD" >> ~/.zshrc
```

### Case 4: `CHROME_AGENT_REPO` already matches

Do not rewrite it. Report that the environment variable is already configured correctly.

### Case 5: `CHROME_AGENT_REPO` conflicts

Do not replace it silently. Ask whether to update it. If approved, replace the existing shell-config line manually and reload the shell later.

## Validation

After installation, verify:

```bash
test -x ~/.local/bin/chrome-agent && echo shim_ok
test -f ~/.agents/scripts/chrome-agent.mjs && echo runtime_ok
chrome-agent doctor --format json
```

Expected result:

- `shim_ok`
- `runtime_ok`
- doctor result with `success` or a clearly scoped `partial_success`/`failure` remediation

## Operator Notes

- Starting installation from a single prompt is fine.
- The operator must still inspect repo-registry and fallback state before persisting shell configuration.
- Persistent changes to launcher paths or shell config must remain explicit and reviewable.
- `skills/chrome-agent` is no longer the formal installation path.
