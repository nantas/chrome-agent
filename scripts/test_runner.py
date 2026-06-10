#!/usr/bin/env python3
"""Unified test runner for chrome-agent.

Subcommands:
    all             Run stdlib discover tests + site sample regression
    site-samples    Run site sample regression only
    unit            Run stdlib discover tests only

Usage:
    python3 scripts/test_runner.py all
    python3 scripts/test_runner.py site-samples [--domain <domain>] [--update-golden]
    python3 scripts/test_runner.py unit
"""

from __future__ import annotations

import argparse
import difflib
import glob
import os
import re
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Repo root detection
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

# Ensure repo root is on sys.path for imports like `scripts.*`
_str_root = str(REPO_ROOT)
if _str_root not in sys.path:
    sys.path.insert(0, _str_root)

# ---------------------------------------------------------------------------
# Strategy discovery
# ---------------------------------------------------------------------------


def _discover_strategies(strategies_dir: Path) -> List[Tuple[str, Path]]:
    """Return [(domain, strategy_path), ...] for all strategy.md files."""
    results = []
    if not strategies_dir.exists():
        return results
    for entry in sorted(strategies_dir.iterdir()):
        if entry.is_dir():
            strat = entry / "strategy.md"
            if strat.exists():
                results.append((entry.name, strat))
    return results


def _parse_samples_field(strategy_path: Path) -> List[Dict[str, str]]:
    """Extract ``samples`` list from strategy frontmatter.

    Delegates to ``strategy_loader.parse_strategy()`` for consistent parsing.
    Returns empty list if the field is missing or empty.
    """
    from scripts.lib.strategy_loader import parse_strategy

    try:
        frontmatter = parse_strategy(str(strategy_path))
    except (ValueError, OSError):
        return []

    if not isinstance(frontmatter, dict):
        return []

    samples = frontmatter.get("samples", [])
    if not isinstance(samples, list):
        return []

    return [s for s in samples if isinstance(s, dict) and "page" in s]


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

_CDP_PLATFORM = "chrome-cdp"


def _resolve_cache_path(page: str, domain: str) -> Optional[Path]:
    """Resolve a sample page to its cache file path.

    Checks ``chrome-cdp`` platform.  The cache key for CDP pages replaces
    ``/`` with ``_`` to produce a flat filename.
    """
    cache_dir = REPO_ROOT / ".cache" / _CDP_PLATFORM / domain
    if not cache_dir.exists():
        return None

    # CDP safe-path: / → _
    safe = page.replace("/", "_")
    # Collapse consecutive underscores
    while "__" in safe:
        safe = safe.replace("__", "_")
    safe = safe.strip("_")

    # Cache filename: spaces→underscores + .json
    safe = safe.replace(" ", "_")
    while "__" in safe:
        safe = safe.replace("__", "_")
    safe = safe.strip("_")

    candidate = cache_dir / f"{safe}.json"
    if candidate.exists():
        return candidate

    return None


def _load_cached_html(cache_path: Path) -> Optional[str]:
    """Load HTML content from a cache JSON entry."""
    import json

    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return data.get("html")
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Golden file helpers
# ---------------------------------------------------------------------------


def _golden_path(domain: str, page: str) -> Path:
    """Return the golden file path for a sample page."""
    # Use the page basename (without extension) for the golden filename
    base = page.replace("/", "_")
    while "__" in base:
        base = base.replace("__", "_")
    base = base.strip("_")
    # Remove .html extension if present
    if base.endswith(".html"):
        base = base[:-5]
    return REPO_ROOT / "sites" / "strategies" / domain / "samples" / f"{base}.md"


def _load_golden(path: Path) -> Optional[str]:
    """Load golden file content."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _save_golden(path: Path, content: str) -> None:
    """Write golden file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Structural assertions
# ---------------------------------------------------------------------------


def _run_structural_assertions(md_text: str) -> List[str]:
    """Run all built-in structural assertions.  Return list of failure messages."""
    from scripts.lib.test_assertions import (
        assert_links_resolved,
        assert_no_raw_html_tags,
        assert_valid_md_tables,
    )

    failures = []
    for name, fn in [
        ("no_raw_html_tags", assert_no_raw_html_tags),
        ("links_resolved", assert_links_resolved),
        ("valid_md_tables", assert_valid_md_tables),
    ]:
        try:
            fn(md_text)
        except AssertionError as e:
            failures.append(f"[{name}] {e}")
    return failures


# ---------------------------------------------------------------------------
# Dynamic TestCase generation (I2)
# ---------------------------------------------------------------------------


def _make_site_sample_test(
    domain: str,
    page: str,
    label: str,
    update_golden: bool = False,
) -> type:
    """Create a ``unittest.TestCase`` class for a single (domain, page) sample."""

    # Import converter
    from scripts.lib.extraction.html_to_markdown import html_to_markdown

    class SiteSampleTest(unittest.TestCase):
        """Dynamically generated test for one site sample."""

        def test_sample(self) -> None:  # noqa: N802
            cache_path = _resolve_cache_path(page, domain)
            if cache_path is None:
                self.skipTest(f"No cache entry for {domain}/{page}")
                return

            html = _load_cached_html(cache_path)
            if not html:
                self.fail(f"Cache entry exists but contains no HTML: {cache_path}")
                return

            # Convert
            md_output = html_to_markdown(html)

            # Collect structural assertion failures (don't abort)
            assertion_failures = _run_structural_assertions(md_output)

            # Golden diff — run regardless of assertion results
            golden_file = _golden_path(domain, page)
            golden_text = _load_golden(golden_file)

            if update_golden:
                _save_golden(golden_file, md_output)
                # Report assertion failures as warnings but don't fail
                if assertion_failures:
                    print(f"  [WARN] Structural assertions (update mode):")
                    for msg in assertion_failures:
                        print(f"    {msg}")
                return

            # Build combined failure message
            failures = []

            for failure_msg in assertion_failures:
                failures.append(f"[structural] {failure_msg}")

            if golden_text is None:
                failures.append(
                    f"[golden] No golden file at {golden_file}. "
                    f"Run with --update-golden to create it."
                )
            elif md_output != golden_text:
                diff_lines = list(difflib.unified_diff(
                    golden_text.splitlines(keepends=True),
                    md_output.splitlines(keepends=True),
                    fromfile="golden",
                    tofile="output",
                ))
                diff_text = "".join(diff_lines)
                failures.append(
                    f"[golden] Diff mismatch for {domain}/{page}:\n{diff_text}"
                )

            if failures:
                self.fail(
                    f"{len(failures)} issue(s) for {domain}/{page}:\n" +
                    "\n".join(failures)
                )

    # Set meaningful class/method name
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", f"{domain}_{page}")
    SiteSampleTest.__name__ = f"Test_{safe_name}"
    SiteSampleTest.__qualname__ = f"Test_{safe_name}"
    SiteSampleTest.test_sample.__doc__ = (
        f"Sample: {domain} — {label} ({page})"
    )

    return SiteSampleTest


# ---------------------------------------------------------------------------
# Subcommand: unit
# ---------------------------------------------------------------------------


def cmd_unit(args: argparse.Namespace) -> int:
    """Run stdlib discover tests under ``tests/``."""
    loader = unittest.TestLoader()
    suite = loader.discover("tests", top_level_dir=str(REPO_ROOT))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


# ---------------------------------------------------------------------------
# Subcommand: site-samples
# ---------------------------------------------------------------------------


def cmd_site_samples(args: argparse.Namespace) -> int:
    """Run site sample regression tests."""
    strategies_dir = REPO_ROOT / "sites" / "strategies"
    strategies = _discover_strategies(strategies_dir)

    suite = unittest.TestSuite()
    total_samples = 0

    for domain, strat_path in strategies:
        # Domain filter
        if args.domain and domain != args.domain:
            continue

        samples = _parse_samples_field(strat_path)
        if not samples:
            print(f"  {domain}: 0 samples — skipped")
            continue

        for sample in samples:
            page = sample["page"]
            label = sample.get("label", page)
            test_cls = _make_site_sample_test(
                domain, page, label,
                update_golden=getattr(args, "update_golden", False),
            )
            # Add the single test method to the suite
            suite.addTest(test_cls("test_sample"))
            total_samples += 1

        print(f"  {domain}: {len(samples)} sample(s)")

    if total_samples == 0:
        print("No sample test cases generated.")
        return 0

    print(f"\nRunning {total_samples} site sample test(s)...\n")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


# ---------------------------------------------------------------------------
# Subcommand: all
# ---------------------------------------------------------------------------


def cmd_all(args: argparse.Namespace) -> int:
    """Run unit tests + site sample regression."""
    # Build a synthetic args for site-samples subcommand
    sample_args = argparse.Namespace(
        domain=None,
        update_golden=False,
    )

    print("=" * 60)
    print("Phase 1: Unit tests (stdlib discover)")
    print("=" * 60)
    rc1 = cmd_unit(args)

    print()
    print("=" * 60)
    print("Phase 2: Site sample regression")
    print("=" * 60)
    rc2 = cmd_site_samples(sample_args)

    return rc1 or rc2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="chrome-agent unified test runner",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("unit", help="Run stdlib discover tests")

    sp_samples = sub.add_parser("site-samples", help="Run site sample regression")
    sp_samples.add_argument("--domain", help="Only test samples for this domain")
    sp_samples.add_argument(
        "--update-golden",
        action="store_true",
        help="Overwrite golden files with current conversion output",
    )

    sub.add_parser("all", help="Run unit tests + site samples")

    args = parser.parse_args()

    if args.command == "unit":
        return cmd_unit(args)
    elif args.command == "site-samples":
        return cmd_site_samples(args)
    elif args.command == "all":
        return cmd_all(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
