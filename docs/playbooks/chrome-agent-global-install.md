# Chrome Agent Global Install Playbook

## Goal

Install the repository-owned `chrome-agent` skill into `~/.agents/skills/` and optionally configure `CHROME_AGENT_REPO` without silently overwriting existing state.

## Source and Destination

- source: `skills/chrome-agent/`
- destination: `~/.agents/skills/chrome-agent/`
- environment variable: `CHROME_AGENT_REPO`

## Decision Points

Before any persistent write, inspect:

- whether `~/.agents/skills/chrome-agent/` already exists
- whether `CHROME_AGENT_REPO` is already set in the current shell
- whether `CHROME_AGENT_REPO` appears in shell config files
- whether any existing `CHROME_AGENT_REPO` value already matches the current repository path

If an existing skill or conflicting environment variable is found, stop and ask for confirmation before changing it.

## Inspect Current State

Check whether the global skill already exists:

```bash
ls -ld ~/.agents/skills/chrome-agent
```

Check the current environment value:

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

### Case 1: Skill does not exist

Copy the skill directory:

```bash
mkdir -p ~/.agents/skills
cp -R skills/chrome-agent ~/.agents/skills/chrome-agent
```

### Case 2: Skill already exists

Do not overwrite immediately. First compare and confirm. If replacement is approved:

```bash
rm -rf ~/.agents/skills/chrome-agent
cp -R skills/chrome-agent ~/.agents/skills/chrome-agent
```

### Case 3: `CHROME_AGENT_REPO` is unset

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
test -f ~/.agents/skills/chrome-agent/SKILL.md && echo skill_ok
test -d "$CHROME_AGENT_REPO" && test -f "$CHROME_AGENT_REPO/AGENTS.md" && echo repo_ok
```

Expected result:

- `skill_ok`
- `repo_ok`

## Operator Notes

- Starting installation from a single prompt is fine.
- The operator must still run the preflight checks above.
- Persistent changes to `~/.agents/skills/` or shell config must remain explicit and reviewable.
