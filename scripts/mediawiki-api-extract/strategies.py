"""Strategy Protocols and default implementations for MediaWiki API extraction."""

import logging
import re
import time
from typing import Protocol, runtime_checkable
from urllib.parse import quote as url_quote

from .client import ApiClient

log = logging.getLogger("mediawiki-api-extract")


# ===========================================================================
# Protocol definitions
# ===========================================================================

@runtime_checkable
class DiscoveryStrategy(Protocol):
    """Page and category discovery, page classification."""

    @property
    def required_capabilities(self) -> set[str]:
        ...

    def discover_pages(self, client: ApiClient, strategy: dict) -> list[dict]:
        ...

    def discover_categories(self, client: ApiClient, page_titles: list[str]) -> dict[str, list[str]]:
        ...

    def classify_page(self, page_title: str, categories: list[str],
                      list_pages: dict[str, str],
                      page_categories: dict[str, str] | None = None,
                      category_filters: list[str] | None = None) -> str:
        ...

    def fetch_list_pages(self, client: ApiClient, list_pages: dict[str, str]) -> dict[str, str]:
        ...


@runtime_checkable
class ContentAcquisitionStrategy(Protocol):
    """Content source fetching (wikitext, rendered HTML, images)."""

    @property
    def required_capabilities(self) -> set[str]:
        ...

    def fetch_page_content(self, client: ApiClient, title: str, strategy: dict) -> dict:
        ...


@runtime_checkable
class LinkResolver(Protocol):
    """Wiki link to Markdown relative path resolution."""

    def convert_links(self, text: str, manifest_pages: list[dict], source_dir: str) -> str:
        ...

    def resolve(self, target: str, display: str, source_dir: str, manifest_pages: list[dict]) -> str:
        ...


@runtime_checkable
class TemplateProcessor(Protocol):
    """Frontmatter extraction, template expansion, cleanup."""

    def extract_frontmatter(self, wikitext: str, fields: list[str]) -> dict:
        ...

    def expand_templates(self, text: str, template_map: dict[str, str]) -> tuple[str, list[str]]:
        ...

    def remove_infobox(self, wikitext: str, fields: list[str]) -> str:
        ...

    def clean_remaining_templates(self, text: str) -> str:
        ...


@runtime_checkable
class ListPageAssembler(Protocol):
    """Index page assembly (DPL table replacement, directory index)."""

    def assemble_index(self, list_page_title: str, pages_in_dir: list[dict],
                       list_content: str | None, frontmatter_fields: list[str],
                       domain: str) -> str:
        ...


# ===========================================================================
# Default implementations
# ===========================================================================

class AllPagesDiscoveryStrategy:
    """Default discovery using action=query&list=allpages."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"page_list", "category_lookup"}

    def discover_pages(self, client: ApiClient, strategy: dict) -> list[dict]:
        api_ns = strategy.get("api", {}).get("namespace", 0)
        pages = []
        continue_token = None
        while True:
            params = {
                "list": "allpages",
                "apnamespace": api_ns,
                "apfilterredir": "nonredirects",
                "aplimit": 500,
            }
            if continue_token:
                params["apcontinue"] = continue_token
            data = client.query(**params)
            result = data.get("query", {}).get("allpages", [])
            pages.extend(result)
            if "continue" in data:
                continue_token = data["continue"].get("apcontinue")
            else:
                break
        return pages

    def discover_categories(self, client: ApiClient, page_titles: list[str], batch_size: int = 50) -> dict[str, list[str]]:
        categories = {}
        for i in range(0, len(page_titles), batch_size):
            batch = page_titles[i:i + batch_size]
            titles_str = "|".join(batch)
            data = client.query(titles=titles_str, prop="categories", cllimit="max")
            pages_data = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages_data.items():
                title = page_info.get("title", "")
                cats = [c["title"].replace("Category:", "") for c in page_info.get("categories", [])]
                categories[title] = cats
            time.sleep(0.2)  # batch delay
        return categories

    def classify_page(self, page_title: str, categories: list[str],
                      list_pages: dict[str, str],
                      page_categories: dict[str, str] | None = None,
                      category_filters: list[str] | None = None) -> str:
        filters = set(category_filters or [])
        page_categories = page_categories or {}

        title_norm = page_title.replace(" ", "_")
        if title_norm in list_pages:
            return list_pages[title_norm]
        if page_title in list_pages:
            return list_pages[page_title]

        filtered_cats = [c for c in categories if c not in filters]
        for cat in filtered_cats:
            if cat in page_categories:
                return page_categories[cat]

        dir_lookup = {}
        for _page, directory in list_pages.items():
            dir_lookup[directory] = directory
            for segment in directory.split("/"):
                norm = segment.replace(" ", "_").lower()
                dir_lookup[norm] = directory

        for directory in page_categories.values():
            dir_lookup[directory] = directory
            for segment in directory.split("/"):
                norm = segment.replace(" ", "_").lower()
                dir_lookup[norm] = directory

        dir_scores: dict[str, int] = {}
        for cat in filtered_cats:
            cat_norm = cat.replace(" ", "_")
            cat_lower = cat_norm.lower()
            for key, directory in dir_lookup.items():
                if cat_norm == key or cat == key:
                    dir_scores[directory] = dir_scores.get(directory, 0) + 2
                elif key.lower() in cat_lower or cat_lower in key.lower():
                    dir_scores[directory] = dir_scores.get(directory, 0) + 1

        if dir_scores:
            best_dir = max(dir_scores, key=dir_scores.get)
            return best_dir

        return "Misc"

    def fetch_list_pages(self, client: ApiClient, list_pages: dict[str, str]) -> dict[str, str]:
        content = {}
        for page_title in list_pages:
            try:
                data = client.parse(page=page_title, prop="wikitext")
                wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                content[page_title] = wikitext
            except RuntimeError as e:
                log.warning("Failed to fetch list page %s: %s", page_title, e)
        return content


class WikitextOnlyAcquisitionStrategy:
    """Default content acquisition fetching prop=wikitext only."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"wikitext_parse"}

    def fetch_page_content(self, client: ApiClient, title: str, strategy: dict) -> dict:
        data = client.parse(page=title, prop="wikitext")
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        return {"wikitext": wikitext, "html": None}


class ExactTitleLinkResolver:
    """Default link resolver using exact title matching."""

    def convert_links(self, text: str, manifest_pages: list[dict], source_dir: str) -> str:
        pages_by_title = {p["title"]: p for p in manifest_pages}

        def replace_link(match):
            target = match.group(1)
            display = match.group(2) if match.group(2) else target
            return self.resolve(target, display, source_dir, manifest_pages)

        text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', replace_link, text)
        text = re.sub(r'\[\[([^\]]+)\]\]', lambda m: self.resolve(m.group(1), m.group(1), source_dir, manifest_pages), text)
        return text

    def resolve(self, target: str, display: str, source_dir: str, manifest_pages: list[dict]) -> str:
        pages_by_title = {p["title"]: p for p in manifest_pages}

        ns_prefixes = ["File:", "Category:", "Template:", "Special:", "Help:", "MediaWiki:"]
        for prefix in ns_prefixes:
            if target.startswith(prefix):
                if prefix == "File:":
                    parts = target[len("File:"):].split("|")
                    image_name = parts[0]
                    alt_text = parts[1] if len(parts) > 1 else image_name
                    alt_text = re.sub(r'\d+px', '', alt_text).strip('|').strip()
                    encoded_name = url_quote(image_name, safe='')
                    return f"![{alt_text}](https://{self._domain}/Special:Redirect/file/{encoded_name})"
                return ""

        page = pages_by_title.get(target)
        if page:
            target_dir = page["target_directory"]
            target_file = page["target_filename"]
            if target_dir != source_dir and target_dir != "Misc":
                if source_dir == "Misc" or "/" not in source_dir:
                    rel_path = f"{target_dir}/{target_file}"
                else:
                    source_depth = source_dir.count("/")
                    prefix = "../" * (source_depth + 1)
                    rel_path = f"{prefix}{target_dir}/{target_file}"
                return f"[{display}]({rel_path})"
            elif target_dir == source_dir:
                return f"[{display}]({target_file})"
            else:
                if source_dir != "Misc" and target_dir == "Misc":
                    return f"[{display}](../Misc/{target_file})"
                return f"[{display}]({target_file})"

        return f"[{display}]({target.replace(' ', '_')}.md)"

    def __init__(self, domain: str = ""):
        self._domain = domain


class SimpleSubstitutionTemplateProcessor:
    """Default template processor using simple string substitution."""

    def extract_frontmatter(self, wikitext: str, fields: list[str]) -> dict:
        frontmatter = {}
        if not fields:
            return frontmatter

        templates = _split_templates(wikitext)
        for tmpl in templates:
            inner = tmpl[2:-2]
            pipe_idx = inner.find("|")
            if pipe_idx < 0:
                continue
            params_str = inner[pipe_idx + 1:]

            found_any = False
            for field in fields:
                pattern = rf'\|\s*{re.escape(field)}\s*=\s*'
                m = re.search(pattern, params_str)
                if m:
                    start = m.end()
                    depth = 0
                    i = start
                    while i < len(params_str):
                        if params_str[i:i+2] == '{{':
                            depth += 1
                            i += 2
                        elif params_str[i:i+2] == '}}':
                            if depth > 0:
                                depth -= 1
                                i += 2
                            else:
                                break
                        elif params_str[i] == '|' and depth == 0:
                            rest = params_str[i+1:]
                            if re.match(r'\s*[\w. -]+\s*=', rest):
                                break
                            i += 1
                        else:
                            i += 1
                    value = params_str[start:i].strip()
                    if value:
                        for _ in range(3):
                            value = re.sub(r'\{\{([^|{}]*?)\|([^{}]*?)\}\}', r'\2', value)
                            value = re.sub(r'\{\{([^{}]*?)\}\}', r'\1', value)
                        value = re.sub(r'\[\[[^|\]]*?\|([^\]]*?)\]\]', r'\1', value)
                        value = re.sub(r'\[\[([^\]]*?)\]\]', r'\1', value)
                        value = re.sub(r'<[^>]+>', '', value)
                        value = re.sub(r'\b\w+\|', '', value) if '|' in value and not any(c in value for c in '[]{}') else value
                        value = value.replace('<br>', ' ').replace('<br/>', ' ').strip()
                        value = value.strip()
                        if value:
                            frontmatter[field] = value
                            found_any = True
            if found_any:
                break
        return frontmatter

    def expand_templates(self, text: str, template_map: dict[str, str]) -> tuple[str, list[str]]:
        unrecognized = []
        if not template_map:
            return text, unrecognized

        def replace_template(match):
            full_match = match.group(0)
            inner = match.group(1)
            parts = inner.split("|")
            template_name = parts[0].strip()
            args = [p.strip() for p in parts[1:]] if len(parts) > 1 else []

            if template_name in template_map:
                fmt = template_map[template_name]
                if args:
                    try:
                        return fmt % args[0]
                    except (TypeError, ValueError):
                        return fmt
                return fmt
            else:
                unrecognized.append(template_name)
                return full_match

        expanded = re.sub(r'\{\{([^}]+)\}\}', replace_template, text)
        return expanded, unrecognized

    def remove_infobox(self, wikitext: str, fields: list[str]) -> str:
        if not fields:
            return wikitext
        templates = _split_templates(wikitext)
        for tmpl in templates:
            inner = tmpl[2:-2]
            pipe_idx = inner.find("|")
            if pipe_idx < 0:
                continue
            params_str = inner[pipe_idx + 1:]
            for field in fields:
                if re.search(rf'\|\s*{re.escape(field)}\s*=', params_str):
                    wikitext = wikitext.replace(tmpl, "")
                    break
        return wikitext

    def clean_remaining_templates(self, text: str) -> str:
        text = re.sub(r'\{\{for\|[^}]*\}\}', '', text)
        text = re.sub(r'\{\{Main\|([^}]*)\}\}', r'See also: \1', text)
        text = re.sub(r'\{\{See also\|([^}]*)\}\}', r'See also: \1', text)
        text = re.sub(r'\{\{([^|{}]*?)\|([^{}]*?)\}\}', r'\2', text)
        text = re.sub(r'\{\{([^{}]*?)\}\}', r'\1', text)
        return text


class FrontmatterDrivenListPageAssembler:
    """Default list page assembler building index.md from frontmatter data."""

    def assemble_index(self, list_page_title: str, pages_in_dir: list[dict],
                       list_content: str | None, frontmatter_fields: list[str],
                       domain: str) -> str:
        if list_content and "DPL_TABLE_PLACEHOLDER" in list_content:
            table_columns = ["Page"] + [f.capitalize().replace("_", " ") for f in frontmatter_fields if f != "image"]
            table_lines = ["| " + " | ".join(table_columns) + " |",
                           "| " + " | ".join(["---"] * len(table_columns)) + " |"]

            for p in sorted(pages_in_dir, key=lambda x: int(x.get("frontmatter", {}).get("number", 999)) if str(x.get("frontmatter", {}).get("number", 999)).isdigit() else 999):
                fm = p["frontmatter"]
                display_name = p['title'].replace('_', ' ')
                page_link = f"[{display_name}]({p['filename']})"
                img_val = fm.get("image", "")
                if img_val:
                    img_url = f"https://{domain}/Special:Redirect/file/{url_quote(img_val, safe='')}"
                    page_cell = f"![{display_name}]({img_url})<br>{page_link}"
                else:
                    page_cell = page_link
                row_values = [page_cell]
                for field in frontmatter_fields:
                    if field == "image":
                        continue
                    val = fm.get(field, "")
                    val = str(val)
                    for _ in range(3):
                        val = re.sub(r'\{\{[^|{}]*?\|([^{}]*?)\}\}', r'\1', val)
                        val = re.sub(r'\{\{([^{}]*?)\}\}', r'\1', val)
                    val = re.sub(r'\[\[[^|\]]*?\|([^\]]*?)\]\]', r'\1', val)
                    val = re.sub(r'\[\[([^\]]*?)\]\]', r'\1', val)
                    val = val.replace('<br>', ' ').replace('<br/>', ' ').strip()
                    if not val:
                        val = "—"
                    row_values.append(val)
                table_lines.append("| " + " | ".join(row_values) + " |")

            table_md = "\n".join(table_lines)
            body = list_content.replace("<!-- DPL_TABLE_PLACEHOLDER -->", table_md)
            body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
            return body
        else:
            return list_content or ""


# ===========================================================================
# Helper functions (not strategies)
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


def convert_wikitable_to_markdown(text: str, manifest_pages: list[dict], source_dir: str,
                                      link_resolver: LinkResolver | None = None) -> str:
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
                            link_resolver: LinkResolver | None = None) -> str:
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
        cleaned = []
        for cell in row:
            cell = _clean_table_cell(cell, manifest_pages, source_dir, link_resolver)
            cleaned.append(cell)
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
    """Split table row content into cells."""
    if separator == '!':
        parts = re.split(r'!!', content)
    else:
        parts = re.split(r'\|\|', content)
    return [p.strip() for p in parts if p.strip()]


def _clean_table_cell(cell: str, manifest_pages: list[dict], source_dir: str,
                        link_resolver: LinkResolver | None = None) -> str:
    """Clean a single table cell content."""
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


def convert_wikitext_to_markdown(wikitext: str, title: str, source_url: str,
                                   manifest_pages: list[dict], source_dir: str,
                                   frontmatter_fields: list[str],
                                   template_map: dict[str, str],
                                   link_resolver: LinkResolver,
                                   template_processor: TemplateProcessor,
                                   domain: str) -> tuple[str, list[str], dict]:
    """Convert wikitext to Markdown. Returns (markdown_content, warnings, frontmatter_dict)."""
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
