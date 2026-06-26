#!/usr/bin/env bash
#
# engine-version-check.sh — Check and optionally update engine CLI versions
#
# Reads configs/engine-versions.json, detects installed versions,
# compares against expected, and optionally triggers updates.
#
# Usage:
#   ./scripts/engine-version-check.sh                    # check all
#   ./scripts/engine-version-check.sh --engine obscura   # check one
#   ./scripts/engine-version-check.sh --update           # check and auto-update
#   ./scripts/engine-version-check.sh --json             # JSON output
#   ./scripts/engine-version-check.sh --update --force   # force re-download
#
# Exit codes:
#   0 — all engines at expected version
#   1 — some engines need update (or update failed)
#   2 — invalid arguments or missing manifest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$REPO_ROOT/configs/engine-versions.json"

# Defaults
ENGINE_FILTER=""
DO_UPDATE=false
FORCE_UPDATE=false
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --engine) ENGINE_FILTER="${2:-}"; shift 2 ;;
    --update) DO_UPDATE=true; shift ;;
    --force)  FORCE_UPDATE=true; shift ;;
    --json)   JSON_OUTPUT=true; shift ;;
    -h|--help)
      echo "Usage: $0 [--engine <name>] [--update] [--force] [--json]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ ! -f "$MANIFEST" ]]; then
  echo "Manifest not found: $MANIFEST" >&2; exit 2
fi

# Delegate all detection + update logic to Python
python3 - "$MANIFEST" "$REPO_ROOT" "$ENGINE_FILTER" "$DO_UPDATE" "$FORCE_UPDATE" "$JSON_OUTPUT" <<'PYEOF'
import json, os, sys, subprocess, hashlib, stat, shutil, urllib.request

manifest_path = sys.argv[1]
repo_root = sys.argv[2]
engine_filter = sys.argv[3]
do_update = sys.argv[4] == "true"
force_update = sys.argv[5] == "true"
json_output = sys.argv[6] == "true"

with open(manifest_path) as f:
    manifest = json.load(f)

engines_cfg = manifest["engines"]
if engine_filter:
    if engine_filter not in engines_cfg:
        print(f"Unknown engine: {engine_filter}", file=sys.stderr)
        print(f"Available: {', '.join(engines_cfg.keys())}", file=sys.stderr)
        sys.exit(2)
    engines_cfg = {engine_filter: engines_cfg[engine_filter]}


def log(msg):
    if not json_output:
        print(msg)


def expand(p):
    return os.path.expandvars(p.replace("$HOME", os.environ.get("HOME", "~")))


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return r.stdout.strip(), r.returncode


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ─── Detection ───

def detect_scrapling(cfg):
    python_bin = expand(cfg["detection"]["managed_path"])
    if not os.path.isfile(python_bin):
        return None, "missing"
    out, rc = run([python_bin, "-c", "from importlib.metadata import version; print(version('scrapling'))"])
    if rc != 0 or not out:
        return None, "detect_failed"
    return out, "detected"


def detect_obscura(cfg):
    binaries = cfg["detection"]["binaries"]
    all_match = True
    details = {}
    for b in binaries:
        path = expand(b["path"])
        if not os.path.isfile(path):
            return None, "missing"
        actual_md5 = md5_file(path)
        actual_size = os.path.getsize(path)
        match = (str(actual_size) == str(b["expected_size"]) and actual_md5 == b["expected_md5"])
        details[b["name"]] = {"match": match, "size": actual_size, "md5": actual_md5}
        if not match:
            all_match = False

    if all_match:
        return cfg["expected_version"], "match"
    else:
        return "unknown", "hash_mismatch"


def detect_cloakbrowser(cfg):
    python_bin = expand(cfg["detection"]["managed_path"])
    out, rc = run([python_bin, "-c", "import cloakbrowser; print(cloakbrowser.__version__)"])
    if rc != 0 or not out:
        return None, "missing"
    return out, "detected"


DETECTORS = {
    "scrapling": detect_scrapling,
    "obscura": detect_obscura,
    "cloakbrowser": detect_cloakbrowser,
}


# ─── Update ───

def update_scrapling(cfg):
    install_dir = expand(cfg["update"]["managed_path"])
    if os.path.isdir(install_dir):
        shutil.rmtree(install_dir)
    out, rc = run(["./scripts/scrapling-cli.sh", "preflight"], cwd=repo_root)
    return rc == 0


def update_obscura(cfg):
    version = cfg["expected_version"]
    update_cfg = cfg["update"]
    import platform
    key = f"{platform.system()}-{platform.machine()}"
    platform_file = update_cfg["platform_map"].get(key)
    if not platform_file:
        log(f"  ✗ No precompiled release for {key}")
        return False

    install_dir = expand(update_cfg["install_dir"])
    url = f"https://github.com/{update_cfg['repo']}/releases/download/v{version}/{platform_file}"

    os.makedirs(install_dir, exist_ok=True)
    archive = os.path.join(install_dir, "obscura.tar.gz")

    log(f"  Downloading Obscura v{version}...")
    try:
        urllib.request.urlretrieve(url, archive)
    except Exception as e:
        log(f"  ✗ Download failed: {e}")
        if os.path.exists(archive):
            os.unlink(archive)
        return False

    log("  Extracting...")
    out, rc = run(["tar", "-xzf", archive, "-C", install_dir])
    if os.path.exists(archive):
        os.unlink(archive)

    for name in ("obscura", "obscura-worker"):
        p = os.path.join(install_dir, name)
        if os.path.isfile(p):
            os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)

    log(f"  ✓ Obscura updated to v{version}")
    return True


def update_cloakbrowser(cfg):
    out, rc = run(["pip3", "install", "--upgrade", cfg["update"]["package"]])
    return rc == 0


UPDATERS = {
    "scrapling": update_scrapling,
    "obscura": update_obscura,
    "cloakbrowser": update_cloakbrowser,
}


# ─── Main ───

results = []
all_ok = True

for engine_name, cfg in engines_cfg.items():
    expected = cfg["expected_version"]

    # Detect
    detector = DETECTORS.get(engine_name)
    if not detector:
        results.append({"engine": engine_name, "expected": expected, "detected": None, "status": "no_detector", "needs_update": True, "update_result": "skipped"})
        all_ok = False
        continue

    detected, status = detector(cfg)

    # Determine needs_update
    if force_update:
        needs_update = True
    elif detected is None:
        needs_update = True
    elif detected == expected:
        needs_update = False
    elif status == "hash_mismatch":
        needs_update = True
    else:
        needs_update = True

    if needs_update:
        all_ok = False

    # Update if requested
    update_result = "skipped"
    if needs_update and do_update:
        log(f"  Updating {engine_name}...")
        updater = UPDATERS.get(engine_name)
        if updater:
            ok = updater(cfg)
            update_result = "success" if ok else "failed"
            if ok:
                # Re-detect after update
                detected, status = detector(cfg)
                needs_update = (detected != expected)
        else:
            update_result = "no_updater"

    results.append({
        "engine": engine_name,
        "expected": expected,
        "detected": detected,
        "status": status,
        "needs_update": needs_update,
        "update_result": update_result,
    })


# ─── Output ───

if json_output:
    print(json.dumps({"all_ok": all_ok, "engines": results}, indent=2))
else:
    log("=== Engine Version Check ===")
    log("")
    for r in results:
        e = r["engine"]
        exp = r["expected"]
        det = r["detected"] or "not installed"
        st = r["status"]
        nu = r["needs_update"]
        ur = r["update_result"]

        if not nu:
            log(f"  ✓ {e}: {det} (expected: {exp})")
        else:
            log(f"  ✗ {e}: {det} (expected: {exp}) — status: {st}")
            if ur == "success":
                log(f"    ↑ Updated successfully")
            elif ur == "failed":
                log(f"    ↑ Update FAILED")
            elif not do_update:
                log(f"    → Run with --update to fix")
    log("")
    if all_ok:
        log("All engines at expected version.")
    else:
        log("Some engines need attention.")

sys.exit(0 if all_ok else 1)
PYEOF
