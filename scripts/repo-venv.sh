#!/bin/sh

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
REQUIREMENTS="$REPO_ROOT/requirements.txt"

usage() {
  cat <<'EOF'
Usage:
  scripts/repo-venv.sh preflight [--no-install]

Commands:
  preflight       Resolve or install app-layer venv and print status lines.
EOF
}

log() {
  printf '%s\n' "$*" >&2
}

is_venv_importable() {
  # Check that all app-layer deps are importable in the venv
  "$VENV_PYTHON" -c "import bs4, yaml, selectolax, markdownify" >/dev/null 2>&1
}

install_venv() {
  log "Application-layer venv not available. Provisioning at $REPO_ROOT/.venv."
  local system_python
  system_python=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")
  uv venv "$REPO_ROOT/.venv" --python "$system_python"
  uv pip install --python "$VENV_PYTHON" -r "$REQUIREMENTS"
  log "Application-layer venv provisioned."
}

emit_status() {
  status=$1
  source=$2
  printf 'STATUS=%s\n' "$status"
  printf 'SOURCE=%s\n' "$source"
  printf 'VENV_PYTHON=%s\n' "$VENV_PYTHON"
  printf 'REQUIREMENTS=%s\n' "$REQUIREMENTS"
}

resolve_venv() {
  allow_install=$1
  status=""
  source=""

  if is_venv_importable; then
    status="available"
    source="managed"
  elif [ "$allow_install" = "yes" ]; then
    install_venv
    if is_venv_importable; then
      status="repaired"
      source="installed"
    else
      log "Failed to provision application-layer venv. Check uv output and retry."
      return 1
    fi
  else
    status="missing"
    source="none"
  fi

  emit_status "$status" "$source"

  if [ "$status" = "missing" ]; then
    log "Application-layer venv is unavailable at $VENV_PYTHON."
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
