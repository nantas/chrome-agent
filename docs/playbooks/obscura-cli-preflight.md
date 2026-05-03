# Obscura CLI Preflight

## Goal

Ensure Obscura is runnable before any `obscura-fetch` workflow starts.

## Contract

- Canonical executable environment variable: `OBSCURA_CLI_PATH`
- Default managed install root: `$HOME/.cache/chrome-agent-obscura`
- Default managed executable: `$HOME/.cache/chrome-agent-obscura/bin/obscura`
- Persistent shell file for this repo workflow: `/Users/nantas-agent/.zshenv`

## Required Order

Before routing to the `obscura-fetch` engine or executing an Obscura-backed fetch:

1. Check `OBSCURA_CLI_PATH` if it is already set and runnable.
2. Check the managed install path if the environment variable is missing or invalid.
3. If neither is runnable, try downloading the precompiled release for the current platform.
4. If download fails or platform has no precompiled release, ask the user to locate the Obscura source repository, then build and install from source.
5. Re-verify the CLI before continuing the original workflow.

If verification step 5 still fails, stop and report the installation/configuration failure. Do not claim the workflow is already on the Obscura path.

### Source Repo Discovery

When precompiled download fails:

1. Ask the user for the path to their local Obscura clone.
   - Look for `/Volumes/Shuttle/projects/agentic/obscura` (common location).
   - Accept any user-provided path.
2. Verify the path exists and contains `Cargo.toml`.
3. If no local repo exists, offer to clone from GitHub:
   ```
   git clone https://github.com/h4ckf0r0day/obscura.git
   ```

## Installation Logic

### Platform Detection

Supported platforms with precompiled releases:
- macOS ARM64
- Linux x86_64

Other platforms fall back to source compilation.

### Download & Install

```bash
# Example: macOS ARM64
OBSCURA_VERSION="0.1.0"
INSTALL_DIR="$HOME/.cache/chrome-agent-obscura/bin"
mkdir -p "$INSTALL_DIR"
curl -L -o "$INSTALL_DIR/obscura.tar.gz" \
  "https://github.com/h4ckf0r0day/obscura/releases/download/v${OBSCURA_VERSION}/obscura-${OBSCURA_VERSION}-aarch64-apple-darwin.tar.gz"
tar -xzf "$INSTALL_DIR/obscura.tar.gz" -C "$INSTALL_DIR"
rm "$INSTALL_DIR/obscura.tar.gz"
chmod +x "$INSTALL_DIR/obscura"
```

### Version Pinning

After first download, lock the version:

```bash
"$INSTALL_DIR/obscura" --help
```

If `--help` returns the expected usage output, mark the installation as valid. Version updates require an explicit openspec change.

### Source Compilation

Build from a local or freshly cloned repository:

```bash
cd <obscura-repo-path>

# Patch: remove prefix-symbols from wreq (macOS arm64 workaround)
# This avoids boring-sys2 linker errors with Apple's ld64
sed -i '' 's/features = \["prefix-symbols"\]//' crates/obscura-net/Cargo.toml

# Build without stealth (stealth mode still functional via reqwest)
# Note: --features stealth adds wreq TLS impersonation but requires
# boring-sys2 which has arm64 build issues.
cargo build --release

# If stealth TLS impersonation is needed and boring-sys2 is fixed upstream:
# cargo build --release --features stealth

# Install binary to managed path
cp target/release/obscura "$INSTALL_DIR/obscura"
cp target/release/obscura-worker "$INSTALL_DIR/obscura-worker"
chmod +x "$INSTALL_DIR/obscura" "$INSTALL_DIR/obscura-worker"
```

**Expected build time**: ~15 seconds (incremental) to ~5 minutes (first build, V8 snapshot).

## Persistent Shell Confirmation

Do not silently rewrite `/Users/nantas-agent/.zshenv`.

- If `OBSCURA_CLI_PATH` is already correct in `.zshenv`, report success and do nothing.
- If `.zshenv` has no `OBSCURA_CLI_PATH`, ask the user before appending it.
- If `.zshenv` has a different `OBSCURA_CLI_PATH`, treat that as a conflict and require explicit approval before replacing it.

## Verification

After preflight, the caller MUST verify:

```bash
"$OBSCURA_CLI_PATH" --help
# or
"$HOME/.cache/chrome-agent-obscura/bin/obscura" --help
```

Expected: usage output including `fetch` subcommand.
