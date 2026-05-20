#!/usr/bin/env bash
# ===========================================================================
# BOI 100-Page Crawl Baseline — End-to-End Test Runner
#
# Frozen artifacts (committed):
#   tests/fixtures/boi-crawl-100-manifest.json    — curated 100-page manifest
#   tests/fixtures/boi-crawl-100-validation-baseline.json — reference validation
#
# Usage:
#   ./tests/e2e/boi-100-baseline.sh                             # run + compare
#   ./tests/e2e/boi-100-baseline.sh --output=./my-output         # custom dir
#   ./tests/e2e/boi-100-baseline.sh --only-compare=./my-output   # skip pipeline
#   ./tests/e2e/boi-100-baseline.sh --update-baseline            # new baseline
#
# Exit codes:
#   0 — all good (no regressions or pipeline failure)
#   1 — pipeline execution failed
#   2 — regressions detected (broken links or empty files increased)
# ===========================================================================

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

MANIFEST="tests/fixtures/boi-crawl-100-manifest.json"
BASELINE="tests/fixtures/boi-crawl-100-validation-baseline.json"
STRATEGY="sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md"
URL="https://bindingofisaacrebirth.wiki.gg/"

# ----- Parse args -----
OUTPUT_DIR=""
ONLY_COMPARE=false
UPDATE_BASELINE=false

for arg in "$@"; do
  case "$arg" in
    --output=*)       OUTPUT_DIR="${arg#*=}" ;;
    --only-compare)   ONLY_COMPARE=true ;;
    --only-compare=*) OUTPUT_DIR="${arg#*=}"; ONLY_COMPARE=true ;;
    --update-baseline) UPDATE_BASELINE=true ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

if [ -z "$OUTPUT_DIR" ]; then
  OUTPUT_DIR="outputs/test-100-extraction"
fi

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: Manifest not found at $MANIFEST" >&2
  echo "  Regenerate from full discovery manifest with tests/e2e/build_100_manifest.py" >&2
  exit 1
fi

# ============================================================
# 1. Pipeline
# ============================================================
if [ "$ONLY_COMPARE" = false ]; then
  echo "========================================================"
  echo "  BOI 100-Page Crawl Baseline"
  echo "========================================================"
  echo "  Manifest:  $MANIFEST ($(wc -c < "$MANIFEST") bytes, $(python3 -c "import json; print(len(json.load(open('$MANIFEST'))['pages']))") pages)"
  echo "  Strategy:  $STRATEGY"
  echo "  Output:    $OUTPUT_DIR"
  echo ""

  # Run pipeline (allow exit 30 from --validate, treat as non-fatal for comparison)
  python3 -m scripts.pipeline pipeline \
    "$URL" \
    --strategy "$STRATEGY" \
    --output "$OUTPUT_DIR" \
    --from-manifest "$MANIFEST" \
    --phase all \
    --concurrency 1 \
    --batch-delay-ms 1200 \
    --validate 2>&1 || true

  echo ""
  echo "Pipeline complete."
  echo ""
fi

# ============================================================
# 2. Compare
# ============================================================
echo "========================================================"
echo "  Validation Comparison"
echo "========================================================"

if [ ! -f "$OUTPUT_DIR/validation_report.json" ]; then
  echo "ERROR: No validation report at $OUTPUT_DIR/validation_report.json" >&2
  echo "  Run the pipeline first (omit --only-compare)" >&2
  exit 1
fi

# Run comparison via Python
export CURR_DIR="$OUTPUT_DIR"
export BASE_PATH="$BASELINE"
export UPD_BASELINE="$UPDATE_BASELINE"

python3 << 'PYEOF'
import json, os, sys

output_dir = os.environ['CURR_DIR']
baseline_path = os.environ['BASE_PATH']
update_baseline = os.environ.get('UPD_BASELINE', 'False').lower() in ('true', '1', 'yes')

with open(f'{output_dir}/validation_report.json') as f:
  current = json.load(f)

with open(baseline_path) as f:
  baseline = json.load(f)

cur_bl = len(current.get('broken_links', []))
cur_ec = len(current.get('empty_content', []))
cur_ui = len(current.get('unavailable_images', []))

baseline_bl = len(baseline.get('broken_links', []))
baseline_ec = len(baseline.get('empty_content', []))
baseline_ui = len(baseline.get('unavailable_images', []))

def delta_str(cur, base):
  d = cur - base
  if d == 0: return f"= ({cur})"
  elif d < 0: return f"✅ -{abs(d)} ({cur} vs {base})"
  else: return f"❌ +{d} ({cur} vs {base})"

print(f"  {'Metric':25s} {'Current':>10s} {'Baseline':>10s} {'Delta':>25s}")
print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*25}")
print(f"  {'Broken links':25s} {cur_bl:>10d} {baseline_bl:>10d} {delta_str(cur_bl, baseline_bl):>25s}")
print(f"  {'Empty files':25s} {cur_ec:>10d} {baseline_ec:>10d} {delta_str(cur_ec, baseline_ec):>25s}")
print(f"  {'Unavailable images':25s} {cur_ui:>10d} {baseline_ui:>10d} {delta_str(cur_ui, baseline_ui):>25s}")

has_regression = False
if cur_bl > baseline_bl:
  print(f"\n  ⚠ REGRESSION: Broken links increased ({baseline_bl} → {cur_bl})")
  has_regression = True
if cur_ec > baseline_ec:
  print(f"\n  ⚠ REGRESSION: Empty files increased ({baseline_ec} → {cur_ec})")
  has_regression = True

if update_baseline:
  with open(baseline_path, 'w') as f:
    json.dump(current, f, indent=2)
  print(f"\n  ✅ Baseline updated: {baseline_path}")
  print(f"     Broken links: {cur_bl} | Empty files: {cur_ec} | Unavailable images: {cur_ui}")

if has_regression:
  print(f"\n  ❌ Regressions detected")
  sys.exit(2)
else:
  print(f"\n  ✅ No regressions detected")
  sys.exit(0)
PYEOF
COMPARE_EXIT=$?

# ============================================================
# 3. Summary
# ============================================================
echo ""
echo "========================================================"
echo "  Done."
echo "  Output:      $OUTPUT_DIR"
echo "  Manifest:    $MANIFEST"
echo "  Baseline:    $BASELINE"
echo "  Result:      $( [ $COMPARE_EXIT -eq 0 ] && echo '✅ OK' || echo '❌ Issues' )"
echo "========================================================"

exit $COMPARE_EXIT
