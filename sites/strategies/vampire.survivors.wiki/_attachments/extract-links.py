#!/usr/bin/env python3
"""Extract internal wiki links from MediaWiki category pages."""

import argparse
import re
import sys
import urllib.request
from urllib.parse import urljoin, urlparse


def fetch_url(url: str) -> str:
    """Fetch HTML content from a URL."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/135.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_wiki_links(text: str, base_url: str) -> set[str]:
    """Extract internal wiki links from HTML or Markdown text.

    Filters out action links, old revisions, redlinks, and non-content
    namespaces (Template, File, Category, Special).
    """
    links: set[str] = set()

    # Extract href attributes from anchor tags
    href_pattern = re.compile(r'<a[^>]+href=["\']([^"\']+)["\']', re.IGNORECASE)
    for match in href_pattern.finditer(text):
        href = match.group(1)
        absolute = urljoin(base_url, href)
        links.add(absolute)

    # Also catch Markdown links [text](url)
    md_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    for match in md_pattern.finditer(text):
        url = match.group(2)
        absolute = urljoin(base_url, url)
        links.add(absolute)

    filtered: set[str] = set()
    for url in links:
        parsed = urlparse(url)
        path = parsed.path
        query = parsed.query

        # Skip non-wiki paths (Weird Gloop uses /w/, standard uses /wiki/)
        if not (path.startswith("/wiki/") or path.startswith("/w/")):
            continue

        # Skip action links and old revisions
        if "action=" in query or "oldid=" in query:
            continue

        # Skip redlinks
        if "redlink=1" in query:
            continue

        # Skip non-content namespaces
        if path.startswith("/w/"):
            title = path[len("/w/"):]
        else:
            title = path[len("/wiki/"):]
        skip_prefixes = (
            "Template:",
            "File:",
            "Category:",
            "Special:",
            "User:",
            "Help:",
            "MediaWiki:",
        )
        if any(title.startswith(p) for p in skip_prefixes):
            continue

        # Normalize: drop fragment, keep only path
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
        filtered.add(normalized)

    return filtered


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract internal wiki links from a MediaWiki category page."
    )
    parser.add_argument(
        "--url",
        help="Category page URL to fetch and parse",
    )
    parser.add_argument(
        "--base-url",
        help="Base URL for resolving relative links (default: auto-detect from --url)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)",
    )
    args = parser.parse_args()

    base_url = args.base_url or args.url or ""
    if not base_url and args.url:
        base_url = args.url

    if args.url:
        try:
            text = fetch_url(args.url)
        except Exception as exc:
            print(f"Error fetching {args.url}: {exc}", file=sys.stderr)
            return 1
        if not base_url:
            base_url = args.url
    else:
        text = sys.stdin.read()
        if not base_url:
            print(
                "Warning: reading from stdin without --base-url; "
                "relative links may not resolve correctly.",
                file=sys.stderr,
            )
            base_url = ""

    links = extract_wiki_links(text, base_url)

    if not links:
        print("No internal wiki links found.", file=sys.stderr)
        return 0

    out = sys.stdout if args.output is None else open(args.output, "w", encoding="utf-8")
    try:
        for link in sorted(links):
            out.write(link + "\n")
    finally:
        if args.output is not None:
            out.close()

    print(f"Extracted {len(links)} unique wiki links.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
