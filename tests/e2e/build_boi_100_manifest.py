#!/usr/bin/env python3
"""Rebuild the curated 100-page manifest for the BOI baseline test.

Run after discovery completes to produce a fresh tests/fixtures/boi-crawl-100-manifest.json.

Usage:
    python3 tests/e2e/build_boi_100_manifest.py <full-manifest.json> [output-path]
    
    If output-path is omitted, writes to tests/fixtures/boi-crawl-100-manifest.json
"""

import json
import sys
import os

# Correct list page directories per the strategy
LIST_PAGE_DIRS = {
    "Items": "items",
    "Attributes": "attributes",
    "Chapters": "chapters",
    "Challenges": "challenges",
    "Achievements": "achievements",
    "Completion Marks": "completion_marks",
    "Trinkets": "trinkets",
    "Characters": "characters",
    "Rooms": "rooms",
    "Transformations": "transformations",
    "Bosses": "bosses",
    "Monsters": "monsters",
    "Pickups": "pickups",
    "Curses": "curses",
    "Seeds": "seeds",
    "Effects": "effects",
    "Endings": "endings",
    "Cards": "cards",
    "Modes": "modes",
    "Objects": "objects",
    "Mechanics": "mechanics",
}


def build_manifest(full_manifest_path: str, output_path: str):
    with open(full_manifest_path) as f:
        manifest = json.load(f)

    pages = manifest["pages"]

    # Fix list page directories
    for p in pages:
        if p.get("is_list_page"):
            title = p["title"]
            if title in LIST_PAGE_DIRS:
                p["target_directory"] = LIST_PAGE_DIRS[title]
            elif title.startswith("Category:"):
                cat_name = title.replace("Category:", "")
                if cat_name in LIST_PAGE_DIRS:
                    p["target_directory"] = LIST_PAGE_DIRS[cat_name]

    # Group by directory
    from collections import defaultdict
    by_dir = defaultdict(list)
    for p in pages:
        by_dir[p.get("target_directory", "(root)")].append(p)

    # Selection strategy
    selected_titles = set()

    # 1. All list pages (19)
    for p in pages:
        if p.get("is_list_page"):
            selected_titles.add(p["title"])

    # 2. Entity pages per directory, proportional
    entity_targets = {
        'items': 20,
        'characters': 8,
        'monsters': 8,
        'bosses': 8,
        'trinkets': 8,
        'challenges': 3,
        'achievements': 3,
        'rooms': 3,
        'transformations': 3,
        'curses': 2,
        'objects': 2,
        'endings': 2,
        'seeds': 2,
        'effects': 2,
        'modes': 1,
        'chapters': 1,
        '': 0,
    }

    for dir_name, count in entity_targets.items():
        pool = [p for p in by_dir.get(dir_name, [])
                if p["title"] not in selected_titles]

        # Interestingness heuristic for boundary testing
        def interesting(p):
            score = 0
            t = p["title"]
            if '(' in t: score += 3
            if '?' in t or '&' in t or "'" in t: score += 1
            if len(t) > 20: score += 1
            cats = len(p.get("source_categories", []))
            if cats > 1: score += cats
            return score

        pool.sort(key=interesting, reverse=True)
        for p in pool[:count]:
            selected_titles.add(p["title"])

    # 3. Additional boundary / disambiguation pages
    extras = [
        "Poop (Disambiguation)",
        "Tech (Disambiguation)",
        "Penny (Disambiguation)",
        "Odd Mushroom (Disambiguation)",
        "Jacob & Esau",
        "0 - The Fool",
        "The Sad Onion",
    ]
    for title in extras:
        matches = [p for p in pages if p["title"] == title]
        if matches and title not in selected_titles:
            selected_titles.add(title)

    # Build and sort
    curated = [p for p in pages if p["title"] in selected_titles]
    list_sel = sorted(
        [p for p in curated if p.get("is_list_page")], key=lambda p: p["title"]
    )
    entity_sel = sorted(
        [p for p in curated if not p.get("is_list_page")],
        key=lambda p: (p.get("target_directory", ""), p["title"]),
    )
    curated = list_sel + entity_sel

    curated_manifest = {
        "pages": curated,
        "list_page_content": manifest.get("list_page_content", {}),
        "phase": "homepage",
        "source": "homepage-driven-discovery (curated 100-page baseline)",
        "total_pages": len(curated),
        "categories_discovered": manifest.get("categories_discovered", 0),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(curated_manifest, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(curated)} pages to {output_path}")
    from collections import Counter
    dirs = Counter(p.get("target_directory", "(root)") for p in curated)
    for d, c in sorted(dirs.items(), key=lambda x: -x[1]):
        print(f"  {d:20s}: {c}")

    return curated_manifest


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    full_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else (
        os.path.join(
            os.path.dirname(__file__), "..", "fixtures", "boi-crawl-100-manifest.json"
        )
    )
    output_path = os.path.abspath(output_path)
    build_manifest(full_path, output_path)
