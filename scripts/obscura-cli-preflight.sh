#!/usr/bin/env bash
#
# obscura-cli-preflight.sh — Download and verify Obscura + obscura-worker
#
# Usage: ./scripts/obscura-cli-preflight.sh
#
# Installs to $HOME/.cache/chrome-agent-obscura/bin/
# Verifies both `obscura` and `obscura-worker` are executable.
#
# Exit codes:
#   0  — success (both binaries available)
#   1  — download/install failed
#   2  — verification failed (binary exists but not executable or --help fails)

set -euo pipefail

OBSCURA_VERSION="$(python3 -c "import json; print(json.load(open('configs/engine-versions.json'))['engines']['obscura']['expected_version'])" 2>/dev/null || echo '0.1.2')"
INSTALL_DIR="$HOME/.cache/chrome-agent-obscura/bin"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load version from manifest if running from repo root
if [[ -f "$REPO_ROOT/configs/engine-versions.json" ]]; then
  MANIFEST_VERSION="$(python3 -c "import json; print(json.load(open('$REPO_ROOT/configs/engine-versions.json'))['engines']['obscura']['expected_version'])" 2>/dev/null)" || true
  if [[ -n "$MANIFEST_VERSION" ]]; then
    OBSCURA_VERSION="$MANIFEST_VERSION"
  fi
fi

echo "=== Obscura CLI Preflight v${OBSCURA_VERSION} ==="

# Step 0: Check if already installed and valid
if [ -x "$INSTALL_DIR/obscura" ]; then
  echo "✓ Obscura already installed: $INSTALL_DIR/obscura"
  if [ -x "$INSTALL_DIR/obscura-worker" ]; then
    echo "✓ obscura-worker already installed"

    # Version check against manifest
    if [[ -f "$REPO_ROOT/configs/engine-versions.json" ]]; then
      CHECK_RESULT="$(cd "$REPO_ROOT" && ./scripts/engine-version-check.sh --engine obscura --json 2>/dev/null)" || true
      if echo "$CHECK_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); exit(0 if not d['engines'][0]['needs_update'] else 1)" 2>/dev/null; then
        echo "✓ Version matches manifest: v${OBSCURA_VERSION}"
        echo "=== Preflight complete ==="
        exit 0
      else
        echo "! Version mismatch detected. Re-downloading v${OBSCURA_VERSION}..."
      fi
    else
      echo "=== Preflight complete ==="
      exit 0
    fi
  else
    echo "! obscura-worker missing, re-extracting..."
  fi
fi

# Step 1: Detect platform
ARCH="$(uname -m)"
OS="$(uname -s)"
case "${OS}-${ARCH}" in
  Darwin-arm64|darwin-arm64)
    PLATFORM="aarch64-macos"
    ;;
  Darwin-x86_64|darwin-x86_64)
    PLATFORM="x86_64-macos"
    ;;
  Linux-x86_64|linux-x86_64)
    PLATFORM="x86_64-linux"
    ;;
  *)
    echo "! No precompiled release for ${OS}-${ARCH}, falling back to source compilation."
    echo "  See docs/playbooks/obscura-cli-preflight.md for source build instructions."
    exit 1
    ;;
esac

ARCHIVE_NAME="obscura-${PLATFORM}.tar.gz"
DOWNLOAD_URL="https://github.com/h4ckf0r0day/obscura/releases/download/v${OBSCURA_VERSION}/${ARCHIVE_NAME}"

# Step 2: Create install directory
mkdir -p "$INSTALL_DIR"

# Step 3: Download tarball
echo "Downloading: ${DOWNLOAD_URL}"
if ! curl -Lfs -o "$INSTALL_DIR/obscura.tar.gz" "$DOWNLOAD_URL"; then
  echo "✗ Download failed: ${DOWNLOAD_URL}"
  echo "  Falling back to source compilation."
  echo "  See docs/playbooks/obscura-cli-preflight.md for source build instructions."
  rm -f "$INSTALL_DIR/obscura.tar.gz"
  exit 1
fi

# Step 4: Extract
echo "Extracting..."
tar -xzf "$INSTALL_DIR/obscura.tar.gz" -C "$INSTALL_DIR"
rm -f "$INSTALL_DIR/obscura.tar.gz"

# Step 5: Set permissions
chmod +x "$INSTALL_DIR/obscura" 2>/dev/null || true
chmod +x "$INSTALL_DIR/obscura-worker" 2>/dev/null || true

# Step 6: Verify obscura
echo "Verifying obscura..."
if ! "$INSTALL_DIR/obscura" --help > /dev/null 2>&1; then
  echo "✗ obscura binary is not executable or --help failed"
  exit 2
fi
echo "✓ obscura OK"

# Step 7: Verify obscura-worker
echo "Verifying obscura-worker..."
if ! "$INSTALL_DIR/obscura-worker" --help > /dev/null 2>&1; then
  echo "✗ obscura-worker binary is not executable or --help failed"
  echo "  Check that the release archive contains both binaries."
  exit 2
fi
echo "✓ obscura-worker OK"

echo "=== Preflight complete ==="
exit 0
