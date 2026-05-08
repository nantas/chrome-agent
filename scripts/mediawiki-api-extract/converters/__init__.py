"""Converters sub-package — independent conversion utilities.

All converters can be imported without pulling in ApiClient or pipeline internals.
"""

from .html_to_markdown import HtmlToMarkdownConverter
from .wikitext_to_md import (
    convert_wikitext_to_markdown,
    convert_wikitable_to_markdown,
    _split_templates,
    _replace_dpl_template,
    _split_template_args,
)
from .card_stats import extract_card_stats, split_card_list_pages

__all__ = [
    "HtmlToMarkdownConverter",
    "convert_wikitext_to_markdown",
    "convert_wikitable_to_markdown",
    "extract_card_stats",
    "split_card_list_pages",
    "_split_templates",
    "_replace_dpl_template",
    "_split_template_args",
]
