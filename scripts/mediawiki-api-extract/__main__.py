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
    parser.add_argument("--concurrency", type=int, default=None,
                        help="Max concurrent API requests (default: use strategy config or 1)")
    parser.add_argument("--batch-delay-ms", type=int, default=None,
                        help="Delay in ms between request batches (default: use strategy config or 1000)")
    parser.add_argument("--max-retries", type=int, default=None,
                        help="Max retries per failed request (default: use strategy config or 5)")
    parser.add_argument("--backoff-multiplier", type=float, default=None,
                        help="Exponential backoff multiplier (default: use strategy config or 2.0)")
    parser.add_argument("--jitter", action="store_true", default=None,
                        help="Enable jitter on retry delays (default: use strategy config or enabled)")
    parser.add_argument("--phase", nargs="+", choices=["A", "B", "C", "all"],
                        default=["all"], help="Phases to run (default: all)")
    parser.add_argument("--no-api-probe", action="store_true",
                        help="Skip API endpoint probing, use strategy base_url directly")
    parser.add_argument("--validate", action="store_true",
                        help="Run L6 validation on existing output (skip extraction)")

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
