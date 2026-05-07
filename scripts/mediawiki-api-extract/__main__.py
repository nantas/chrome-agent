"""CLI entry point for MediaWiki API extraction pipeline."""

import argparse
import logging
import sys

from .pipeline import run_pipeline

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mediawiki-api-extract")


def main():
    parser = argparse.ArgumentParser(
        description="MediaWiki API extraction pipeline for chrome-agent",
        epilog="Phases: A=Page Discovery, B=Content Extraction, C=Output Assembly. "
               "Default: all phases.",
    )
    parser.add_argument("url", help="Target wiki URL (used for domain resolution)")
    parser.add_argument("--strategy", required=True, help="Path to site strategy file")
    parser.add_argument("--output", required=True, help="Output directory for extracted content")
    parser.add_argument("--concurrency", type=int, default=5,
                        help="Max concurrent API requests (default: 5)")
    parser.add_argument("--phase", nargs="+", choices=["A", "B", "C", "all"],
                        default=["all"], help="Phases to run (default: all)")
    parser.add_argument("--no-api-probe", action="store_true",
                        help="Skip API endpoint probing, use strategy base_url directly")

    args = parser.parse_args()

    try:
        import yaml  # noqa: F401 — verify yaml is available
    except ImportError:
        print("ERROR: 'pyyaml' package is required. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(20)

    exit_code = run_pipeline(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
