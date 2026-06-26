#!/bin/sh

set -eu

MANAGED_ROOT="${CLOAKBROWSER_MANAGED_ROOT:-$HOME/.cache/chrome-agent-cloakbrowser}"
MANAGED_PYTHON="$MANAGED_ROOT/bin/python"

usage() {
  cat <<'EOF'
Usage:
  scripts/cloakbrowser-cli.sh preflight [--no-install]

Commands:
  preflight       Resolve or install CloakBrowser managed venv and print status lines.
EOF
}

log() {
  printf '%s\n' "$*" >&2
}

is_managed_importable() {
  # Check that cloakbrowser is importable in the managed venv
  "$MANAGED_PYTHON" -c "import cloakbrowser" >/dev/null 2>&1
}

install_managed() {
  log "CloakBrowser managed venv not available. Provisioning at $MANAGED_ROOT."
  mkdir -p "$(dirname "$MANAGED_ROOT")"
  uv venv "$MANAGED_ROOT" --python 3.11
  uv pip install --python "$MANAGED_PYTHON" cloakbrowser
  log "CloakBrowser managed venv provisioned."
}

emit_status() {
  status=$1
  source=$2
  printf 'STATUS=%s\n' "$status"
  printf 'SOURCE=%s\n' "$source"
  printf 'RESOLVED_CLI_PATH=%s\n' "$MANAGED_PYTHON"
  printf 'MANAGED_ROOT=%s\n' "$MANAGED_ROOT"
}

resolve_venv() {
  allow_install=$1
  status=""
  source=""

  if is_managed_importable; then
    status="available"
    source="managed"
  elif [ "$allow_install" = "yes" ]; then
    install_managed
    if is_managed_importable; then
      status="repaired"
      source="installed"
    else
      log "Failed to provision CloakBrowser managed venv. Check uv output and retry."
      return 1
    fi
  else
    status="missing"
    source="none"
  fi

  emit_status "$status" "$source"

  if [ "$status" = "missing" ]; then
    log "CloakBrowser managed venv is unavailable at $MANAGED_PYTHON."
    return 2
  fi
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
    resolve_venv "$allow_install"
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    usage
    exit 64
    ;;
esac
