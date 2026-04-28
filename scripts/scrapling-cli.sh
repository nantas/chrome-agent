#!/bin/sh

set -eu

MANAGED_ROOT="${SCRAPLING_MANAGED_ROOT:-$HOME/.cache/chrome-agent-scrapling}"
MANAGED_CLI="$MANAGED_ROOT/bin/scrapling"
MANAGED_PYTHON="$MANAGED_ROOT/bin/python"
ZSHENV_FILE="${SCRAPLING_ZSHENV_FILE:-$HOME/.zshenv}"

usage() {
  cat <<'EOF'
Usage:
  scripts/scrapling-cli.sh preflight [--no-install]
  scripts/scrapling-cli.sh shellenv
  scripts/scrapling-cli.sh persist-zshenv [--replace-conflict]
  scripts/scrapling-cli.sh mcp

Commands:
  preflight       Resolve or install Scrapling CLI and print status lines.
  shellenv        Print an export command for the resolved CLI path.
  persist-zshenv  Persist SCRAPLING_CLI_PATH after explicit confirmation.
  mcp             Resolve the CLI, then exec "scrapling mcp".
EOF
}

log() {
  printf '%s\n' "$*" >&2
}

strip_wrapping_quotes() {
  value=$1
  case "$value" in
    \"*\") value=${value#\"}; value=${value%\"} ;;
    \'*\') value=${value#\'}; value=${value%\'} ;;
  esac
  printf '%s' "$value"
}

get_zshenv_value() {
  if [ ! -f "$ZSHENV_FILE" ]; then
    return 1
  fi

  raw_value=$(
    sed -n 's/^[[:space:]]*export[[:space:]]\{1,\}SCRAPLING_CLI_PATH=//p' "$ZSHENV_FILE" \
      | tail -n 1
  )

  if [ -z "$raw_value" ]; then
    return 1
  fi

  strip_wrapping_quotes "$raw_value"
}

is_runnable_cli() {
  candidate=$1
  [ -n "$candidate" ] && [ -x "$candidate" ] && "$candidate" --help >/dev/null 2>&1
}

install_managed_cli() {
  log "Scrapling CLI not available. Provisioning managed install at $MANAGED_ROOT."
  mkdir -p "$MANAGED_ROOT"
  uv venv "$MANAGED_ROOT" --python 3.11
  uv pip install --python "$MANAGED_PYTHON" "scrapling[ai]"
  "$MANAGED_CLI" install
}

emit_status() {
  status=$1
  source=$2
  resolved=$3

  zshenv_status="missing"
  zshenv_value=""
  if existing_value=$(get_zshenv_value 2>/dev/null); then
    zshenv_value=$existing_value
    if [ "$existing_value" = "$resolved" ]; then
      zshenv_status="correct"
    else
      zshenv_status="conflict"
    fi
  fi

  printf 'STATUS=%s\n' "$status"
  printf 'SOURCE=%s\n' "$source"
  printf 'RESOLVED_CLI_PATH=%s\n' "$resolved"
  printf 'MANAGED_ROOT=%s\n' "$MANAGED_ROOT"
  printf 'MANAGED_CLI_PATH=%s\n' "$MANAGED_CLI"
  printf 'ZSHENV_FILE=%s\n' "$ZSHENV_FILE"
  printf 'ZSHENV_STATUS=%s\n' "$zshenv_status"
  printf 'ZSHENV_VALUE=%s\n' "$zshenv_value"
}

resolve_cli() {
  allow_install=$1
  status=""
  source=""
  resolved=""

  if [ -n "${SCRAPLING_CLI_PATH:-}" ] && is_runnable_cli "${SCRAPLING_CLI_PATH}"; then
    status="available"
    source="env"
    resolved=$SCRAPLING_CLI_PATH
  elif is_runnable_cli "$MANAGED_CLI"; then
    status="available"
    source="managed"
    resolved=$MANAGED_CLI
  elif [ "$allow_install" = "yes" ]; then
    if install_managed_cli && is_runnable_cli "$MANAGED_CLI"; then
      status="repaired"
      source="installed"
      resolved=$MANAGED_CLI
    else
      log "Failed to make Scrapling CLI available. Check uv output and retry."
      return 1
    fi
  else
    log "Scrapling CLI is unavailable. Checked SCRAPLING_CLI_PATH and $MANAGED_CLI."
    return 2
  fi

  emit_status "$status" "$source" "$resolved"
}

append_zshenv_export() {
  resolved=$1
  mkdir -p "$(dirname "$ZSHENV_FILE")"
  if [ -f "$ZSHENV_FILE" ] && [ -s "$ZSHENV_FILE" ]; then
    printf '\n' >>"$ZSHENV_FILE"
  fi
  printf 'export SCRAPLING_CLI_PATH="%s"\n' "$resolved" >>"$ZSHENV_FILE"
}

replace_zshenv_export() {
  resolved=$1
  tmp_file=$(mktemp "${TMPDIR:-/tmp}/scrapling-zshenv.XXXXXX")
  trap 'rm -f "$tmp_file"' EXIT HUP INT TERM

  if [ -f "$ZSHENV_FILE" ]; then
    sed '/^[[:space:]]*export[[:space:]]\{1,\}SCRAPLING_CLI_PATH=/d' "$ZSHENV_FILE" >"$tmp_file"
  fi
  if [ -s "$tmp_file" ]; then
    printf '\n' >>"$tmp_file"
  fi
  printf 'export SCRAPLING_CLI_PATH="%s"\n' "$resolved" >>"$tmp_file"
  mv "$tmp_file" "$ZSHENV_FILE"
  trap - EXIT HUP INT TERM
}

cmd=${1:-}
case "$cmd" in
  preflight)
    shift
    allow_install="yes"
    while [ $# -gt 0 ]; do
      case "$1" in
        --no-install) allow_install="no" ;;
        *)
          usage
          exit 64
          ;;
      esac
      shift
    done
    resolve_cli "$allow_install"
    ;;
  shellenv)
    shift
    resolved=$(
      resolve_cli "yes" | sed -n 's/^RESOLVED_CLI_PATH=//p' | tail -n 1
    )
    printf 'export SCRAPLING_CLI_PATH="%s"\n' "$resolved"
    ;;
  persist-zshenv)
    shift
    replace_conflict="no"
    while [ $# -gt 0 ]; do
      case "$1" in
        --replace-conflict) replace_conflict="yes" ;;
        *)
          usage
          exit 64
          ;;
      esac
      shift
    done

    status_output=$(resolve_cli "yes")
    resolved=$(printf '%s\n' "$status_output" | sed -n 's/^RESOLVED_CLI_PATH=//p' | tail -n 1)
    zshenv_status=$(printf '%s\n' "$status_output" | sed -n 's/^ZSHENV_STATUS=//p' | tail -n 1)

    case "$zshenv_status" in
      correct)
        log "SCRAPLING_CLI_PATH is already persisted in $ZSHENV_FILE."
        ;;
      missing)
        append_zshenv_export "$resolved"
        log "Persisted SCRAPLING_CLI_PATH to $ZSHENV_FILE."
        ;;
      conflict)
        if [ "$replace_conflict" != "yes" ]; then
          log "Conflicting SCRAPLING_CLI_PATH found in $ZSHENV_FILE. Re-run with --replace-conflict after explicit approval."
          exit 3
        fi
        replace_zshenv_export "$resolved"
        log "Replaced conflicting SCRAPLING_CLI_PATH in $ZSHENV_FILE."
        ;;
      *)
        log "Unexpected zshenv status: $zshenv_status"
        exit 4
        ;;
    esac
    ;;
  mcp)
    shift
    status_output=$(resolve_cli "yes")
    resolved=$(printf '%s\n' "$status_output" | sed -n 's/^RESOLVED_CLI_PATH=//p' | tail -n 1)
    zshenv_status=$(printf '%s\n' "$status_output" | sed -n 's/^ZSHENV_STATUS=//p' | tail -n 1)
    case "$zshenv_status" in
      missing)
        log "SCRAPLING_CLI_PATH is not persisted. Current run will continue with $resolved."
        log "If you want future shells to pick it up automatically, confirm before running:"
        log "  scripts/scrapling-cli.sh persist-zshenv"
        ;;
      conflict)
        log "SCRAPLING_CLI_PATH in $ZSHENV_FILE conflicts with $resolved."
        log "Current run will continue without rewriting shell config."
        log "If you approve the replacement later, run:"
        log "  scripts/scrapling-cli.sh persist-zshenv --replace-conflict"
        ;;
    esac
    exec "$resolved" mcp
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    usage
    exit 64
    ;;
esac
