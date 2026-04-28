#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
RUNTIME_SOURCE="$SCRIPT_DIR/chrome-agent-runtime.mjs"
RUNTIME_DIR="${CHROME_AGENT_RUNTIME_DIR:-$HOME/.agents/scripts}"
BIN_DIR="${CHROME_AGENT_BIN_DIR:-$HOME/.local/bin}"
RUNTIME_TARGET="$RUNTIME_DIR/chrome-agent.mjs"
SHIM_TARGET="$BIN_DIR/chrome-agent"

if [ ! -f "$RUNTIME_SOURCE" ]; then
  echo "chrome-agent runtime source missing: $RUNTIME_SOURCE" >&2
  exit 1
fi

mkdir -p "$RUNTIME_DIR" "$BIN_DIR"
cp "$RUNTIME_SOURCE" "$RUNTIME_TARGET"
chmod +x "$RUNTIME_TARGET"

cat >"$SHIM_TARGET" <<EOF
#!/bin/sh
exec node "$RUNTIME_TARGET" "\$@"
EOF
chmod +x "$SHIM_TARGET"

printf 'RUNTIME=%s\n' "$RUNTIME_TARGET"
printf 'SHIM=%s\n' "$SHIM_TARGET"
