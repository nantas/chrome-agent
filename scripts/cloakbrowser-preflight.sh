#!/usr/bin/env bash
# cloakbrowser-preflight.sh — Verify CloakBrowser is installed and binary is available
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERBOSE="${VERBOSE:-0}"
JSON_OUTPUT="${JSON_OUTPUT:-0}"

log() {
  if [ "$JSON_OUTPUT" = "0" ]; then
    echo "$@"
  fi
}

error() {
  if [ "$JSON_OUTPUT" = "0" ]; then
    echo "ERROR: $*" >&2
  fi
}

# Step 1: Check Python module availability
check_module() {
  if python3 -c "from cloakbrowser import launch" 2>/dev/null; then
    if [ "$VERBOSE" = "1" ]; then log "  ✓ cloakbrowser Python module available"; fi
    return 0
  else
    error "cloakbrowser Python module not found"
    return 1
  fi
}

# Step 2: Check binary existence
check_binary() {
  local binary_found=0
  local binary_path=""

  # Check standard cache locations
  for dir in "$HOME/.cloakbrowser"/chromium-*; do
    if [ -d "$dir" ]; then
      # macOS path
      local macos_bin="$dir/Chromium.app/Contents/MacOS/Chromium"
      if [ -x "$macos_bin" ]; then
        binary_found=1
        binary_path="$macos_bin"
        break
      fi
      # Linux path
      local linux_bin="$dir/chrome-linux/chrome"
      if [ -x "$linux_bin" ]; then
        binary_found=1
        binary_path="$linux_bin"
        break
      fi
    fi
  done

  if [ "$binary_found" = "1" ]; then
    if [ "$VERBOSE" = "1" ]; then log "  ✓ CloakBrowser binary found: $binary_path"; fi
    return 0
  else
    error "CloakBrowser patched Chromium binary not found in ~/.cloakbrowser/"
    return 1
  fi
}

# Step 3: Get version info
get_version() {
  local version=""
  version=$(python3 -c "import cloakbrowser; print(cloakbrowser.__version__)" 2>/dev/null || echo "unknown")
  echo "$version"
}

# Main
main() {
  local module_ok=0
  local binary_ok=0
  local version=""

  log "CloakBrowser Preflight Check"
  log "============================="

  # Check module
  if check_module; then
    module_ok=1
  fi

  # Check binary (only if module is available)
  if [ "$module_ok" = "1" ]; then
    if check_binary; then
      binary_ok=1
    fi
    version=$(get_version)
  fi

  # Output results
  if [ "$JSON_OUTPUT" = "1" ]; then
    printf '{"module": %s, "binary": %s, "version": "%s"}\n' \
      "$module_ok" "$binary_ok" "$version"
  else
    if [ "$module_ok" = "1" ] && [ "$binary_ok" = "1" ]; then
      log ""
      log "✓ CloakBrowser ready (v${version})"
      return 0
    else
      log ""
      log "✗ CloakBrowser not ready"
      log ""
      log "Install with:"
      log "  pip install cloakbrowser"
      log ""
      log "The patched Chromium binary (~200MB) will be downloaded automatically"
      log "on first use. Binary caches at ~/.cloakbrowser/chromium-{version}/"
      if [ "$(uname)" = "Darwin" ]; then
        log ""
        log "macOS: If Gatekeeper blocks the binary, run:"
        log "  xattr -cr ~/.cloakbrowser/chromium-*/Chromium.app"
      fi
      return 1
    fi
  fi
}

main "$@"
