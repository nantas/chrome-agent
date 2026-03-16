# Chrome Tooling Setup

This document records the minimal repo-local setup used in `chrome-agent`.

## Local Install

From the repo root:

```bash
npm install
```

Pinned repo-local dependencies:

- `chrome-devtools-mcp@0.20.0`
- `pi-chrome-cdp` from `github:pasky/chrome-cdp-skill#7c2940af8dbe12745f24845f352e7555baed0304`

## Repo-Local Entry Points

Use the local package scripts rather than global installs:

```bash
npm run devtools-cli -- start --isolated --no-usage-statistics
npm run devtools-cli -- status
npm run devtools-cli -- new_page https://example.com
npm run devtools-cli -- evaluate_script '() => document.title'
npm run devtools-cli -- stop
```

```bash
npm run chrome-cdp -- list
npm run chrome-cdp -- html <target-prefix> h1
npm run chrome-cdp -- eval <target-prefix> 'document.title'
```

## Tool Roles

- `chrome-devtools-mcp` is the default path for browser-driven tasks in this repo.
- `chrome-cdp-skill` is the supplemental path when the task must reuse a live Chrome session you already have open.

## Environment Assumptions

- Node.js `24.13.0` and npm `11.6.2` were used for the local setup.
- Local Chrome was verified at `146.0.7680.80`.
- `chrome-devtools-mcp --autoConnect` is available with Chrome `144+`, but it still requires Chrome remote debugging to be enabled in the running browser.

## Validation Notes

### `chrome-devtools-mcp`

Validated locally through the package-provided `chrome-devtools` CLI wrapper:

```bash
npm run devtools-cli -- start --isolated --no-usage-statistics
npm run devtools-cli -- new_page https://example.com --output-format json
npm run devtools-cli -- evaluate_script '() => document.title' --output-format json
npm run devtools-cli -- take_snapshot --output-format json
```

This path succeeded end-to-end against `https://example.com/` and saved a screenshot under `reports/`.

### `chrome-cdp-skill`

The pinned version works, but it has a narrower startup assumption than `chrome-devtools-mcp`:

- it does not accept a custom `--browserUrl`
- it does not accept a custom Chrome profile path
- it reads the debugging endpoint only from `~/Library/Application Support/Google/Chrome/DevToolsActivePort`

For normal use, enable remote debugging in your regular Chrome at:

`chrome://inspect/#remote-debugging`

If that toggle is on in the default Chrome profile, `npm run chrome-cdp -- list` can attach directly.

For the isolated verification run on 2026-03-16, the tool was validated against a separately launched debug Chrome, and the expected `DevToolsActivePort` file had to be written to the default location because the tool does not currently discover custom-profile debug sessions on its own.

## First Real Task

See `reports/2026-03-16-example-com-verification.md` for the exact commands, evidence, and residual blocker notes from the first public-page validation.
