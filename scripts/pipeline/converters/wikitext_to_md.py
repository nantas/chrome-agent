"""Wikitext to Markdown converter — independent of pipeline internals.

Can be imported and used standalone:
    from scripts.pipeline.converters.wikitext_to_md import convert_wikitext_to_markdown
"""

import logging
import re
from typing import Optional

log = logging.getLogger("pipeline.converters")


# ===========================================================================
# Template helpers
# ===========================================================================

def _split_templates(text: str) -> list[str]:
    """Extract top-level {{...}} template calls, respecting nesting."""
    results = []
    i = 0
    while i < len(text):
        if text[i:i+2] == '{{':
            depth = 0
            start = i
            while i < len(text):
                if text[i:i+2] == '{{':
                    depth += 1
                    i += 2
                elif text[i:i+2] == '}}':
                    depth -= 1
                    i += 2
                    if depth == 0:
                        results.append(text[start:i])
                        break
                else:
                    i += 1
        else:
            i += 1
    return results


def _replace_dpl_template(text: str) -> str:
    """Replace all {{#dpl:...}} template calls with DPL_TABLE_PLACEHOLDER."""
    marker = '{{#dpl:'
    while True:
        idx = text.find(marker)
        if idx < 0:
            break
        depth = 0
        i = idx
        while i < len(text):
            if text[i:i+2] == '{{':
                depth += 1
                i += 2
            elif text[i:i+2] == '}}':
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1
        text = text[:idx] + '\n<!-- DPL_TABLE_PLACEHOLDER -->\n' + text[i:]
    return text


def _split_template_args(inner: str) -> list[str]:
    """Split template inner content by | respecting nesting."""
    parts = []
    current = ""
    depth = 0
    i = 0
    while i < len(inner):
        if inner[i:i+2] == '{{':
            depth += 1
            current += inner[i:i+2]
            i += 2
        elif inner[i:i+2] == '}}':
            depth -= 1
            current += inner[i:i+2]
            i += 2
        elif inner[i] == '|' and depth == 0:
            parts.append(current)
            current = ""
            i += 1
        else:
            current += inner[i]
            i += 1
    if current or parts:
        parts.append(current)
    return parts


# ===========================================================================
# Wikitable conversion
# ===========================================================================

def convert_wikitable_to_markdown(text: str, manifest_pages: list[dict], source_dir: str,
                                  link_resolver=None) -> str:
    """Convert MediaWiki table syntax ({| ... |}) to Markdown tables."""
    text = re.sub(r'(==+\s*[^=]+?\s*==+)\s*\n\{\|', r'\1\n\n{|', text)

    result_parts = []
    i = 0
    while i < len(text):
        table_start = text.find('\n{|', i)
        if table_start == -1 and text.startswith('{|'):
            table_start = 0
        if table_start == -1:
            result_parts.append(text[i:])
            break

        depth = 0
        j = table_start
        while j < len(text):
            if text[j:j+2] == '{|':
                depth += 1
                j += 2
            elif text[j:j+2] == '|}':
                depth -= 1
                j += 2
                if depth == 0:
                    break
            else:
                j += 1

        if depth != 0:
            result_parts.append(text[i:j])
            break

        before = text[i:table_start]
        if before and not before.endswith('\n'):
            before += '\n'
        result_parts.append(before)

        table_block = text[table_start:j]
        md_table = _parse_wikitable_block(table_block, manifest_pages, source_dir, link_resolver)
        if md_table:
            md_table = '\n' + md_table + '\n'
        result_parts.append(md_table)

        i = j

    return ''.join(result_parts)


def _parse_wikitable_block(block: str, manifest_pages: list[dict], source_dir: str,
                           link_resolver=None) -> str:
    """Parse a single {| ... |} block into a Markdown table."""
    lines = block.split('\n')
    rows = []
    current_row = []
    is_header_row = False
    first_row_done = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('{|') or stripped == '|}':
            continue
        if stripped.startswith('|-'):
            if current_row:
                rows.append((is_header_row and not first_row_done, current_row))
                first_row_done = True
                current_row = []
                is_header_row = False
            continue
        if stripped.startswith('!'):
            is_header_row = True
            cells = _split_table_cells(stripped[1:], '!')
            current_row.extend(cells)
            continue
        if stripped.startswith('|'):
            content = stripped[1:]
            attr_pipe = content.find(' |')
            if attr_pipe >= 0 and attr_pipe < 30:
                maybe_attr = content[:attr_pipe].strip()
                if (re.match(r'^[a-zA-Z]+="?[^"]*"?$|^[a-zA-Z]+$|^\d+$', maybe_attr)
                        or maybe_attr.startswith('colspan')
                        or maybe_attr.startswith('rowspan')
                        or maybe_attr.startswith('class')
                        or maybe_attr.startswith('style')
                        or maybe_attr.startswith('align')):
                    content = content[attr_pipe + 2:].strip()
            cells = _split_table_cells(content, '|')
            current_row.extend(cells)
            continue
        if current_row and stripped:
            current_row[-1] += ' ' + stripped

    if current_row:
        rows.append((is_header_row and not first_row_done, current_row))

    if not rows:
        return ''

    max_cols = max(len(row) for _, row in rows)
    normalized = []
    for is_header, row in rows:
        while len(row) < max_cols:
            row.append('')
        normalized.append((is_header, row[:max_cols]))

    cleaned_rows = []
    for is_header, row in normalized:
        cleaned = [_clean_table_cell(cell, manifest_pages, source_dir, link_resolver) for cell in row]
        cleaned_rows.append((is_header, cleaned))

    md_lines = []
    if cleaned_rows:
        _, header = cleaned_rows[0]
        md_lines.append('| ' + ' | '.join(header) + ' |')
        md_lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
        for _, row in cleaned_rows[1:]:
            md_lines.append('| ' + ' | '.join(row) + ' |')

    return '\n'.join(md_lines)


def _split_table_cells(content: str, separator: str) -> list[str]:
    if separator == '!':
        parts = re.split(r'!!', content)
    else:
        parts = re.split(r'\|\|', content)
    return [p.strip() for p in parts if p.strip()]


def _clean_table_cell(cell: str, manifest_pages: list[dict], source_dir: str,
                      link_resolver=None) -> str:
    for _ in range(3):
        cell = re.sub(r'\{\{([^|{}]*?)\|([^{}]*?)\}\}', r'\2', cell)
        cell = re.sub(r'\{\{([^{}]*?)\}\}', r'\1', cell)
    if link_resolver is not None:
        cell = link_resolver.convert_links(cell, manifest_pages, source_dir)
    cell = re.sub(r"'''([^']+)'''", r'**\1**', cell)
    cell = re.sub(r"''([^']+)''", r'*\1*', cell)
    cell = re.sub(r'<[^>]+>', '', cell)
    cell = re.sub(r'\s+', ' ', cell).strip()
    cell = cell.replace('|', '\\|')
    return cell


# ===========================================================================
# Main wikitext-to-markdown converter
# ===========================================================================

def convert_wikitext_to_markdown(wikitext: str, title: str, source_url: str,
                                  manifest_pages: list[dict], source_dir: str,
                                  frontmatter_fields: list[str],
                                  template_map: dict[str, str],
                                  link_resolver,
                                  template_processor,
                                  domain: str) -> tuple[str, list[str], dict]:
    """Convert wikitext to Markdown.

    Args:
        link_resolver: An object satisfying the LinkResolver protocol (has convert_links/resolve methods).
        template_processor: An object satisfying the TemplateProcessor protocol (has extract_frontmatter,
            expand_templates, remove_infobox, clean_remaining_templates methods).

    Returns:
        (markdown_content, warnings, frontmatter_dict)
    """
    warnings = []

    fm = template_processor.extract_frontmatter(wikitext, frontmatter_fields)
    fm["title"] = title
    fm["source_url"] = source_url

    text = template_processor.remove_infobox(wikitext, frontmatter_fields)
    text, unrecognized = template_processor.expand_templates(text, template_map)
    for tmpl in set(unrecognized):
        warnings.append(f"Unrecognized template: {tmpl}")

    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<dpl>.*?</dpl>', '\n<!-- DPL_TABLE_PLACEHOLDER -->\n', text, flags=re.DOTALL)
    text = _replace_dpl_template(text)
    text = template_processor.clean_remaining_templates(text)
    text = re.sub(r'^\s*\[\[Category:[^\]]*\]\]\s*$', '', text, flags=re.MULTILINE)
    text = convert_wikitable_to_markdown(text, manifest_pages, source_dir, link_resolver)
    text = link_resolver.convert_links(text, manifest_pages, source_dir)
    text = re.sub(r"'''([^']+)'''", r"**\1**", text)
    text = re.sub(r"''([^']+)''", r"*\1*", text)
    text = re.sub(r'^====\s*(.+?)\s*====$', r'#### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^===\s*(.+?)\s*===$', r'### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^==\s*(.+?)\s*==$', r'## \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\s+', '- ', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)

    fm_lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, str) and ('\n' in value or ':' in value or '"' in value):
            fm_lines.append(f'{key}: "{value}"')
        else:
            fm_lines.append(f"{key}: {value}")
    fm_lines.append("---\n")

    body = text.strip()
    if not body.startswith('#'):
        body = f"# {title}\n\n{body}"

    return "\n".join(fm_lines) + body + "\n", warnings, fm
