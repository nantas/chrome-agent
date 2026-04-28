# Scrapling CLI Preflight

## Goal

Ensure Scrapling is runnable before any Scrapling-first workflow starts.

## Contract

- Canonical executable environment variable: `SCRAPLING_CLI_PATH`
- Default managed install root: `$HOME/.cache/chrome-agent-scrapling`
- Default managed executable: `$HOME/.cache/chrome-agent-scrapling/bin/scrapling`
- Persistent shell file for this repo workflow: `/Users/nantas-agent/.zshenv`

## Required Order

Before choosing a Scrapling fetcher or launching the Scrapling MCP server:

1. Check `SCRAPLING_CLI_PATH` if it is already set and runnable.
2. Check the managed install path if the environment variable is missing or invalid.
3. If neither is runnable, provision the managed install with `uv`.
4. Re-verify the CLI before continuing the original workflow.

If step 4 still fails, stop and report the installation/configuration failure. Do not claim the workflow is already on the Scrapling-first path.

## Repo Script

Use the repository helper:

```bash
./scripts/scrapling-cli.sh preflight
```

Possible outcomes:

- `STATUS=available` with `SOURCE=env` or `SOURCE=managed`
- `STATUS=repaired` with `SOURCE=installed`
- non-zero exit with a clear failure message if installation assurance could not restore the CLI

For the current shell only, print an export line without writing shell config:

```bash
./scripts/scrapling-cli.sh shellenv
```

For MCP launch:

```bash
./scripts/scrapling-cli.sh mcp
```

## Persistent Shell Confirmation

Do not silently rewrite `/Users/nantas-agent/.zshenv`.

- If `SCRAPLING_CLI_PATH` is already correct in `.zshenv`, report success and do nothing.
- If `.zshenv` has no `SCRAPLING_CLI_PATH`, ask the user before appending it.
- If `.zshenv` has a different `SCRAPLING_CLI_PATH`, treat that as a conflict and require explicit approval before replacing it.

After approval, the helper supports:

```bash
./scripts/scrapling-cli.sh persist-zshenv
./scripts/scrapling-cli.sh persist-zshenv --replace-conflict
```
