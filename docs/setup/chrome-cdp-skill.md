# Chrome CDP Skill Setup

This repository now includes the upstream `chrome-cdp` skill at:

`.agents/skills/chrome-cdp/`

Installed source:

- Repo: `https://github.com/pasky/chrome-cdp-skill`
- Path: `skills/chrome-cdp`
- Ref used during install: `main`

## What Was Installed

- `.agents/skills/chrome-cdp/SKILL.md`
- `.agents/skills/chrome-cdp/scripts/cdp.mjs`

The skill is kept repo-local so the browser workflow can travel with this repository instead of depending on a global skill install.

## Runtime Requirements

- Node.js 22+
- Chrome or Chromium-family browser
- Remote debugging enabled

The script auto-detects Chrome's `DevToolsActivePort` file in standard locations. If the browser is running with a custom profile or a non-standard port file location, set:

```bash
export CDP_PORT_FILE=/full/path/to/DevToolsActivePort
```

## Quick Verification

The following command verifies the installed skill against a temporary Chrome session without touching an existing user profile:

```bash
PROFILE=$(mktemp -d "${TMPDIR:-/tmp}/chrome-cdp-skill-profile.XXXXXX")
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --user-data-dir="$PROFILE" \
  --remote-debugging-port=0 \
  --headless=new \
  --disable-gpu \
  --no-first-run \
  --no-default-browser-check \
  'data:text/html,<title>chrome-cdp-skill-check</title><h1>chrome-cdp-skill ok</h1>' &

export CDP_PORT_FILE="$PROFILE/DevToolsActivePort"
node .agents/skills/chrome-cdp/scripts/cdp.mjs list
```

## Recommended Real-Session Use

For live browsing work with the user's existing Chrome session:

1. Open `chrome://inspect/#remote-debugging`
2. Enable remote debugging
3. Run `node .agents/skills/chrome-cdp/scripts/cdp.mjs list`
4. Use the target prefix returned by `list` with `snap`, `eval`, `shot`, or other commands
