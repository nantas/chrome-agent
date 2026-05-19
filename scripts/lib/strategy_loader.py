"""Shared strategy loading utilities."""

from __future__ import annotations

import re
from typing import Optional

import yaml


def parse_strategy(strategy_path: str) -> dict:
    """Parse a site strategy file and return frontmatter as dict."""
    with open(strategy_path, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Strategy file missing YAML frontmatter: {strategy_path}")

    frontmatter = yaml.safe_load(parts[1])
    return frontmatter


def parse_frontmatter_from_content(content: str) -> Optional[dict]:
    """Parse YAML frontmatter from raw content string using regex.

    Placeholder utility for future use by explore-side modules.

    Args:
        content: Raw file content potentially containing YAML frontmatter.

    Returns:
        Parsed frontmatter dict, or None if no frontmatter markers found.
    """
    match = re.match(r"^---\n(.*?)\n---", content, re.S | re.M)
    if not match:
        return None
    return yaml.safe_load(match.group(1))
