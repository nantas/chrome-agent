"""CLI sub-command routing for MediaWiki API extraction pipeline."""

import argparse
import logging
import sys

from .pipeline import run_pipeline, EXIT_INVALID_ARGS
from .standalone import fetch_and_convert, reprocess_pages

log = logging.getLogger("mediawiki-api-extract")


def cmd_pipeline(args):
    """Run the full extraction pipeline (default)."""
    try:
        import yaml  # noqa: F401
    except ImportError:
        print("ERROR: 'pyyaml' package is required. Install with: pip install pyyaml", file=sys.stderr)
        return EXIT_INVALID_ARGS
    return run_pipeline(args)


def cmd_fetch(args):
    """Fetch and convert a single page."""
    try:
        result = fetch_and_convert(
            url=args.url,
            domain=args.domain,
            output=args.output,
            mode=args.mode,
        )
        print(f"Output: {result}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 10


def cmd_reprocess(args):
    """Incrementally reprocess specified pages."""
    pages = [p.strip() for p in args.pages.split(",") if p.strip()]
    if not pages:
        print("ERROR: --pages requires at least one page title", file=sys.stderr)
        return EXIT_INVALID_ARGS

    result = reprocess_pages(
        page_titles=pages,
        api_base_url=args.api_url or f"https://{args.domain}/api.php",
        domain=args.domain,
        output_dir=args.output,
        manifest_path=args.manifest,
    )

    print(f"Reprocessed: {result['success']}/{result['total']} success")
    if result['errors']:
        for err in result['errors']:
            print(f"  FAILED: {err['title']}: {err['error']}", file=sys.stderr)

    if result['failure'] > 0 and result['success'] == 0:
        return 10
    elif result['failure'] > 0:
        return 1
    return 0


def cmd_fix_links(args):
    """Fix links in output directory."""
    from .converters.link_fixer import fix_links_in_dir
    import json
    import os

    manifest_pages = []
    if args.manifest and os.path.exists(args.manifest):
        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest_pages = manifest.get("pages", [])

    result = fix_links_in_dir(args.directory, args.domain, manifest_pages)
    print(f"Fixed: {result['fixed']}, Skipped: {result['skipped']}, Unchanged: {result['unchanged']}")
    return 0


def cmd_reconvert(args):
    """Re-convert an existing file."""
    from .standalone import reconvert_file
    try:
        content = reconvert_file(args.file, args.domain)
        print(f"Reconverted: {args.file}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 10


def main():
    parser = argparse.ArgumentParser(
        description="MediaWiki API extraction pipeline for chrome-agent",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- pipeline (default) ---
    pipe_p = subparsers.add_parser("pipeline", help="Run full extraction pipeline")
    _add_pipeline_args(pipe_p)

    # --- fetch ---
    fetch_p = subparsers.add_parser("fetch", help="Fetch and convert a single page")
    fetch_p.add_argument("url", help="Full wiki page URL")
    fetch_p.add_argument("--domain", required=True, help="Wiki domain")
    fetch_p.add_argument("--mode", choices=["html", "wikitext"], default="html")
    fetch_p.add_argument("--output", required=True, help="Output file path")

    # --- reprocess ---
    reproc_p = subparsers.add_parser("reprocess", help="Incrementally reprocess pages")
    reproc_p.add_argument("url", help="Target wiki URL (for domain resolution)")
    reproc_p.add_argument("--domain", required=True, help="Wiki domain")
    reproc_p.add_argument("--pages", required=True, help="Comma-separated page titles")
    reproc_p.add_argument("--manifest", help="Path to page_manifest.json")
    reproc_p.add_argument("--output", required=True, help="Output directory")
    reproc_p.add_argument("--api-url", help="Override API base URL")

    # --- fix-links ---
    fix_p = subparsers.add_parser("fix-links", help="Fix links in output directory")
    fix_p.add_argument("directory", help="Output directory to fix")
    fix_p.add_argument("--domain", required=True, help="Wiki domain")
    fix_p.add_argument("--manifest", help="Path to page_manifest.json")

    # --- reconvert ---
    reconv_p = subparsers.add_parser("reconvert", help="Re-convert a single file")
    reconv_p.add_argument("file", help="File to reconvert")
    reconv_p.add_argument("--domain", required=True, help="Wiki domain")

    # If no subcommand detected, inject 'pipeline' as default
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] not in ("pipeline", "fetch", "reprocess", "fix-links", "reconvert", "-h", "--help"):
        _sys.argv = [_sys.argv[0], "pipeline"] + _sys.argv[1:]

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return EXIT_INVALID_ARGS

    import os
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.command == "pipeline":
        return cmd_pipeline(args)
    elif args.command == "fetch":
        return cmd_fetch(args)
    elif args.command == "reprocess":
        return cmd_reprocess(args)
    elif args.command == "fix-links":
        return cmd_fix_links(args)
    elif args.command == "reconvert":
        return cmd_reconvert(args)
    else:
        parser.print_help()
        return EXIT_INVALID_ARGS


def _add_pipeline_args(parser):
    """Add standard pipeline arguments to a parser."""
    parser.add_argument("url", help="Target wiki URL (used for domain resolution)")
    parser.add_argument("--strategy", required=True, help="Path to site strategy file")
    parser.add_argument("--output", required=True, help="Output directory for extracted content")
    parser.add_argument("--concurrency", type=int, default=None,
                        help="Max concurrent API requests")
    parser.add_argument("--batch-delay-ms", type=int, default=None,
                        help="Delay in ms between request batches")
    parser.add_argument("--max-retries", type=int, default=None,
                        help="Max retries per failed request")
    parser.add_argument("--backoff-multiplier", type=float, default=None,
                        help="Exponential backoff multiplier")
    parser.add_argument("--jitter", action="store_true", default=None,
                        help="Enable jitter on retry delays")
    parser.add_argument("--phase", nargs="+",
                        choices=["A", "B", "C", "homepage", "all"],
                        default=["all"], help="Phases to run")
    parser.add_argument("--no-api-probe", action="store_true",
                        help="Skip API endpoint probing")
    parser.add_argument("--resume", action="store_true", default=True,
                        help="Enable resume from checkpoint (default: on)")
    parser.add_argument("--no-resume", action="store_true", default=None,
                        help="Disable resume, start fresh")
    parser.add_argument("--resume-flush-interval", type=int, default=100,
                        help="Pages processed between state file flushes (default: 100)")
    parser.add_argument("--no-auto-fix-links", action="store_true",
                        help="Skip automatic link fixing after pipeline completion")
    parser.add_argument("--validate", action="store_true",
                        help="Run L6 validation on output")
    parser.add_argument("--exclude-category", action="append", default=None,
                        help="Category to exclude from Phase 0 (repeatable)")
