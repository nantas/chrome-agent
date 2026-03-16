# Example.com Verification

## Task Goal

Validate the repo-local `chrome-devtools-mcp` and `chrome-cdp-skill` setup end-to-end against a safe public page.

## Target Site

- `https://example.com/`

## Tooling Path Used

- Default path: repo-local `chrome-devtools-mcp@0.20.0`
- Supplemental path: repo-local `pi-chrome-cdp@1.0.2` from `pasky/chrome-cdp-skill`

## Result

- `chrome-devtools-mcp`: success
- `chrome-cdp-skill`: partial success with an environment-specific bootstrap workaround

## Key Evidence

### `chrome-devtools-mcp`

Commands used:

```bash
npm run devtools-cli -- start --isolated --no-usage-statistics --logFile /tmp/chrome-devtools-mcp.log
npm run devtools-cli -- new_page https://example.com --output-format json
npm run devtools-cli -- evaluate_script '() => ({ title: document.title, h1: document.querySelector("h1")?.textContent?.trim(), url: location.href })' --output-format json
npm run devtools-cli -- take_snapshot --output-format json
npm run devtools-cli -- take_screenshot --filePath reports/example-com-devtools-mcp.png --output-format json
```

Observed results:

- `new_page` opened `https://example.com/`
- `evaluate_script` returned `{"title":"Example Domain","h1":"Example Domain","url":"https://example.com/"}`
- `take_snapshot` returned the expected accessibility tree with `RootWebArea` name `Example Domain`
- Screenshot saved to `reports/example-com-devtools-mcp.png`

### `chrome-cdp-skill`

Commands used:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-cdp-profile https://example.com
curl -sf http://127.0.0.1:9222/json/version
npm run chrome-cdp -- list
npm run chrome-cdp -- eval 3ABF38D2 '({ title: document.title, href: location.href })'
npm run chrome-cdp -- html 3ABF38D2 h1
npm run chrome-cdp -- shot 3ABF38D2 reports/example-com-chrome-cdp.png
```

Observed results after bootstrap:

- `list` returned the `Example Domain` page
- `eval` returned title `Example Domain` and URL `https://example.com/`
- `html` returned `<h1>Example Domain</h1>`
- Screenshot saved to `reports/example-com-chrome-cdp.png`

## Exact Blocker

The pinned `chrome-cdp-skill` version reads the debugging endpoint only from:

- `~/Library/Application Support/Google/Chrome/DevToolsActivePort`

It does not accept a custom debugging URL or custom Chrome profile path. Because this verification used an isolated Chrome profile at `/tmp/chrome-cdp-profile`, the tool initially failed with:

```text
ENOENT: no such file or directory, open '/Users/nantas-agent/Library/Application Support/Google/Chrome/DevToolsActivePort'
```

To finish the validation safely without using the real everyday Chrome session, the expected `DevToolsActivePort` file was written to the default location using the active isolated browser's WebSocket endpoint.

## Next Recommended Action

- Use `chrome-devtools-mcp` as the default repo path for future tasks.
- Use `chrome-cdp-skill` only when live-session reuse is required and remote debugging is enabled in the default Chrome profile via `chrome://inspect/#remote-debugging`.
- If future runs need `chrome-cdp-skill` against non-default profiles or explicit ports, either patch the upstream script to accept a browser URL/profile override or document a local wrapper once that need is real.
