"""Strategy Protocols and default implementations for MediaWiki API extraction."""

import json
import logging
import os
import re
import time
from typing import Optional, Protocol, runtime_checkable
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
                      page_categories: Optional[dict[str, str]] = None,
                      category_filters: Optional[list[str]] = None) -> str:
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
                       list_content: Optional[str], frontmatter_fields: list[str],
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
        api = strategy.get("api", {})
        namespaces = api.get("namespaces", [api.get("namespace", 0)])
        if not isinstance(namespaces, list):
            namespaces = [namespaces]

        all_pages = []
        for ns in namespaces:
            pages = []
            continue_token = None
            while True:
                params = {
                    "list": "allpages",
                    "apnamespace": ns,
                    "apfilterredir": "nonredirects",
                    "aplimit": 500,
                }
                if continue_token:
                    params["apcontinue"] = continue_token
                data = client.query(**params)
                result = data.get("query", {}).get("allpages", [])
                for p in result:
                    p["ns"] = ns
                pages.extend(result)
                if "continue" in data:
                    continue_token = data["continue"].get("apcontinue")
                else:
                    break
            all_pages.extend(pages)

        # Deduplicate by pageid
        seen = set()
        deduped = []
        for p in all_pages:
            pid = p.get("pageid")
            if pid and pid not in seen:
                seen.add(pid)
                deduped.append(p)
            elif not pid:
                deduped.append(p)
        return deduped

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
                      page_categories: Optional[dict[str, str]] = None,
                      category_filters: Optional[list[str]] = None,
                      namespace: int = 0) -> str:
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
                       list_content: Optional[str], frontmatter_fields: list[str],
                       domain: str) -> str:
        # Support dict input from HybridListPageAssembler
        if isinstance(list_content, dict):
            list_content = list_content.get("wikitext", "")
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
                                      link_resolver: Optional[LinkResolver] = None) -> str:
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
                            link_resolver: Optional[LinkResolver] = None) -> str:
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
                        link_resolver: Optional[LinkResolver] = None) -> str:
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

# ===========================================================================
# StS2-specific strategy implementations (Change 2)
# ===========================================================================

class CategoryMembersDiscoveryStrategy:
    """Discovery using action=query&list=categorymembers with namespace support."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"page_list", "category_lookup"}

    def discover_pages(self, client: ApiClient, strategy: dict) -> list[dict]:
        api = strategy.get("api", {})
        taxonomy = api.get("taxonomy", {})
        page_categories = taxonomy.get("page_categories", {})
        namespaces = api.get("namespaces", [api.get("namespace", 0)])
        if not isinstance(namespaces, list):
            namespaces = [namespaces]

        all_pages = []
        for ns in namespaces:
            ns_pages = self._discover_for_namespace(client, page_categories, ns)
            for p in ns_pages:
                p["namespace"] = ns
            all_pages.extend(ns_pages)

        # Deduplicate by pageid
        seen = set()
        deduped = []
        for p in all_pages:
            pid = p.get("pageid")
            if pid and pid not in seen:
                seen.add(pid)
                deduped.append(p)
            elif not pid:
                deduped.append(p)
        return deduped

    def _discover_for_namespace(self, client: ApiClient, page_categories: dict, ns: int) -> list[dict]:
        pages = []
        for category in page_categories:
            cmtitle = f"Category:{category}"
            continue_token = None
            while True:
                params = {
                    "list": "categorymembers",
                    "cmtitle": cmtitle,
                    "cmnamespace": ns,
                    "cmlimit": 500,
                }
                if continue_token:
                    params["cmcontinue"] = continue_token
                data = client.query(**params)
                result = data.get("query", {}).get("categorymembers", [])
                pages.extend(result)
                if "continue" in data:
                    continue_token = data["continue"].get("cmcontinue")
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
            time.sleep(0.2)
        return categories

    def classify_page(self, page_title: str, categories: list[str],
                      list_pages: dict[str, str],
                      page_categories: Optional[dict[str, str]] = None,
                      category_filters: Optional[list[str]] = None,
                      namespace: int = 0) -> str:
        filters = set(category_filters or [])
        page_categories = page_categories or {}

        title_norm = page_title.replace(" ", "_")
        if title_norm in list_pages:
            result = list_pages[title_norm]
        elif page_title in list_pages:
            result = list_pages[page_title]
        else:
            filtered_cats = [c for c in categories if c not in filters]
            for cat in filtered_cats:
                if cat in page_categories:
                    result = page_categories[cat]
                    break
            else:
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
                    result = max(dir_scores, key=dir_scores.get)
                else:
                    result = "Misc"

        # Namespace-based directory prefix is handled by title_to_filepath
        # in phase_a.py; classify_page returns only the content-type subdir.
        return result

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


class HybridAcquisitionStrategy:
    """Content acquisition fetching wikitext, and optionally rendered HTML + images."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"wikitext_parse", "html_parse", "imageinfo_query"}

    def fetch_page_content(self, client: ApiClient, title: str, strategy: dict) -> dict:
        # Primary: wikitext
        data = client.parse(page=title, prop="wikitext")
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")

        result = {"wikitext": wikitext, "rendered_html": None, "images": None}

        if not wikitext:
            return result

        # Detect dynamic content indicators
        has_dynamic = bool(re.search(r'\{\{\s*#\s*(invoke|dpl|lst|if|ifeq)\s*[:|]', wikitext, re.IGNORECASE))

        if has_dynamic:
            log.debug("Dynamic content detected for %s, fetching rendered HTML and images", title)
            try:
                html_data = client.parse(page=title, prop="text")
                rendered = html_data.get("parse", {}).get("text", {}).get("*", "")
                result["rendered_html"] = rendered
            except RuntimeError as e:
                log.warning("Failed to fetch rendered HTML for %s: %s", title, e)

            try:
                img_data = client.parse(page=title, prop="images")
                images = img_data.get("parse", {}).get("images", [])
                result["images"] = images
            except RuntimeError as e:
                log.warning("Failed to fetch images for %s: %s", title, e)

        return result


class ShortNameLinkResolver:
    """Link resolver using short-name index with balanced-bracket parsing and relpath."""

    def __init__(self, domain: str = "", manifest_pages: Optional[list[dict]] = None):
        self._domain = domain
        self._pages_by_title: dict[str, dict] = {}
        self._short_title_index: dict[str, list[dict]] = {}
        if manifest_pages:
            self._build_index(manifest_pages)

    def _build_index(self, manifest_pages: list[dict]):
        self._pages_by_title = {p["title"]: p for p in manifest_pages}
        for p in manifest_pages:
            short = p["title"].split(":")[-1]
            self._short_title_index.setdefault(short, []).append(p)

    def convert_links(self, text: str, manifest_pages: list[dict], source_dir: str) -> str:
        # Rebuild index if manifest changed
        if manifest_pages and not self._pages_by_title:
            self._build_index(manifest_pages)

        # First handle [[target|display]]
        def replace_pipe_link(match):
            target = match.group(1)
            display = match.group(2)
            return self.resolve(target, display, source_dir, manifest_pages)

        text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', replace_pipe_link, text)

        # Then handle [[target]]
        text = re.sub(r'\[\[([^\]]+)\]\]', lambda m: self.resolve(m.group(1), m.group(1), source_dir, manifest_pages), text)
        return text

    def resolve(self, target: str, display: str, source_dir: str, manifest_pages: list[dict]) -> str:
        if not self._pages_by_title and manifest_pages:
            self._build_index(manifest_pages)

        pages_by_title = self._pages_by_title

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

        # Try exact match first
        page = pages_by_title.get(target)
        if page:
            return self._make_link(page, display, source_dir)

        # Try short name match
        short = target.split(":")[-1]
        candidates = self._short_title_index.get(short, [])
        if candidates:
            # Prefer same namespace if possible
            source_ns = self._guess_namespace(source_dir)
            same_ns = [c for c in candidates if self._guess_namespace(c["target_directory"]) == source_ns]
            if same_ns:
                page = same_ns[0]
            else:
                page = candidates[0]
            return self._make_link(page, display, source_dir)

        # Try namespace-prefixed match
        for full_title in pages_by_title:
            if full_title.endswith(f":{target}") or full_title.endswith(f":{short}"):
                return self._make_link(pages_by_title[full_title], display, source_dir)

        return f"[{display}]({target.replace(' ', '_')}.md)"

    def _guess_namespace(self, target_dir: str) -> str:
        """Guess namespace from target_directory."""
        if target_dir.startswith("StS2") or target_dir.startswith("Slay the Spire 2"):
            return "sts2"
        if target_dir.startswith("StS1") or target_dir.startswith("Slay the Spire"):
            return "sts1"
        return ""

    def _make_link(self, page: dict, display: str, source_dir: str) -> str:
        target_dir = page["target_directory"]
        target_file = page["target_filename"]
        if target_dir == source_dir:
            return f"[{display}]({target_file})"
        # Use os.path.relpath for cross-directory links
        source_path = source_dir.replace("/", os.sep)
        target_path = os.path.join(target_dir.replace("/", os.sep), target_file)
        rel = os.path.relpath(target_path, source_path).replace(os.sep, "/")
        return f"[{display}]({rel})"


class StructuredTemplateProcessor:
    """Template processor supporting positional and named arguments, with Lua awareness."""

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
            parts = _split_template_args(inner)
            template_name = parts[0].strip()
            args = parts[1:] if len(parts) > 1 else []
            kwargs = {}
            positional = []
            for arg in args:
                if '=' in arg:
                    k, v = arg.split('=', 1)
                    kwargs[k.strip()] = v.strip()
                else:
                    positional.append(arg.strip())

            # Lua module call
            if template_name.startswith("#invoke:"):
                unrecognized.append(f"Lua module: {template_name}")
                return full_match

            if template_name in template_map:
                fmt = template_map[template_name]
                # Try positional first, then kwargs
                if positional:
                    try:
                        return fmt % positional[0]
                    except (TypeError, ValueError):
                        pass
                if kwargs:
                    try:
                        # Simple named parameter substitution
                        result = fmt
                        for k, v in kwargs.items():
                            result = result.replace(f"%({k})s", v)
                        return result
                    except (TypeError, ValueError):
                        pass
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
        # Remove Lua invocations (keep as comment or remove)
        text = re.sub(r'\{\{#invoke:[^}]+\}\}', '', text)
        # Generic parameter templates
        text = re.sub(r'\{\{([^|{}]*?)\|([^{}]*?)\}\}', r'\2', text)
        text = re.sub(r'\{\{([^{}]*?)\}\}', r'\1', text)
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


class HybridListPageAssembler:
    """List page assembler preferring rendered HTML tables, with frontmatter fallback."""

    def assemble_index(self, list_page_title: str, pages_in_dir: list[dict],
                       list_content: Optional[str], frontmatter_fields: list[str],
                       domain: str) -> str:
        # Check if rendered_html is available in list_content (passed as dict by phase_b)
        rendered_html = None
        if isinstance(list_content, dict):
            rendered_html = list_content.get("rendered_html")
            list_content = list_content.get("wikitext", "")

        if rendered_html:
            # Try to extract table from rendered HTML
            table_md = self._extract_table_from_html(rendered_html, pages_in_dir, frontmatter_fields, domain)
            if table_md:
                if "<!-- DPL_TABLE_PLACEHOLDER -->" in (list_content or ""):
                    body = list_content.replace("<!-- DPL_TABLE_PLACEHOLDER -->", table_md)
                else:
                    body = (list_content or "") + "\n\n" + table_md
                body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
                return body

        # Fallback to frontmatter-driven assembly
        fallback = FrontmatterDrivenListPageAssembler()
        return fallback.assemble_index(list_page_title, pages_in_dir, list_content, frontmatter_fields, domain)

    def _extract_table_from_html(self, html: str, pages_in_dir: list[dict],
                                  frontmatter_fields: list[str], domain: str) -> Optional[str]:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Check for cardsContainer (StS2 card grid)
        cards_container = soup.find(id="cardsContainer")
        if cards_container:
            card_boxes = cards_container.find_all("div", class_="card-box")
            if card_boxes:
                lines = ["| Card | Rarity | Type | Color |", "| --- | --- | --- | --- |"]
                for box in card_boxes:
                    name = box.get("data-name", "")
                    rarity = box.get("data-rarity", "")
                    ctype = box.get("data-type", "")
                    color = box.get("data-color", "")
                    # Try to extract name from image alt or link title
                    if not name:
                        img = box.find("img")
                        if img:
                            name = img.get("alt", "").replace(".png", "").replace("StS2_", "").replace("_", " ")
                        a = box.find("a")
                        if a:
                            name = a.get("title", "").split(":")[-1]
                    lines.append(f"| {name} | {rarity} | {ctype} | {color} |")
                return "\n".join(lines)

        tables = soup.find_all("table")
        if not tables:
            return None

        # Find the most data-rich table
        best_table = None
        best_rows = 0
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) > best_rows:
                best_rows = len(rows)
                best_table = table

        if not best_table or best_rows < 2:
            return None

        # Convert to Markdown
        md_lines = []
        rows = best_table.find_all("tr")
        max_cols = 0
        parsed_rows = []

        for row in rows:
            cells = []
            for th in row.find_all("th"):
                text = th.get_text(strip=True)
                cells.append(text)
            for td in row.find_all("td"):
                text = td.get_text(strip=True)
                cells.append(text)
            if cells:
                max_cols = max(max_cols, len(cells))
                parsed_rows.append(cells)

        if not parsed_rows:
            return None

        for cells in parsed_rows:
            while len(cells) < max_cols:
                cells.append("")
            md_lines.append("| " + " | ".join(cells) + " |")
            if len(md_lines) == 1:
                md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

        return "\n".join(md_lines) if md_lines else None


# ===========================================================================
# L6 Validation layer
# ===========================================================================

def validate_links(output_dir: str) -> list[dict]:
    """Scan all .md files for [text](path) links and verify targets exist."""
    broken = []
    link_pattern = re.compile(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)')

    for root, _dirs, files in os.walk(output_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            for match in link_pattern.finditer(content):
                display = match.group(1)
                path = match.group(2)
                # Skip external links and anchors
                if path.startswith("http") or path.startswith("#"):
                    continue
                # Resolve relative to the file's directory
                target = os.path.normpath(os.path.join(os.path.dirname(filepath), path))
                if not os.path.exists(target):
                    broken.append({
                        "file": os.path.relpath(filepath, output_dir),
                        "display": display,
                        "target": path,
                        "resolved": os.path.relpath(target, output_dir) if os.path.isabs(target) else target,
                    })
    return broken


def validate_content_integrity(output_dir: str) -> list[dict]:
    """Detect files that are empty or contain only frontmatter."""
    empty = []
    for root, _dirs, files in os.walk(output_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            # Strip frontmatter
            body = content
            if body.startswith("---"):
                end = body.find("\n---", 3)
                if end >= 0:
                    body = body[end + 4:].strip()
            # Strip headings
            body = re.sub(r'^#+\s.*$', '', body, flags=re.MULTILINE).strip()
            if not body:
                empty.append({
                    "file": os.path.relpath(filepath, output_dir),
                    "reason": "empty_or_frontmatter_only",
                })
    return empty


def validate_images(output_dir: str, client: Optional[ApiClient] = None) -> list[dict]:
    """Extract ![alt](url) images and optionally verify via API."""
    unavailable = []
    image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    images_to_check: dict[str, list[str]] = {}  # url -> list of files referencing it

    for root, _dirs, files in os.walk(output_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            for match in image_pattern.finditer(content):
                url = match.group(2)
                if url.startswith("http"):
                    images_to_check.setdefault(url, []).append(os.path.relpath(filepath, output_dir))

    if client:
        # Batch check via API (extract File: names from URLs)
        file_names = []
        url_to_name = {}
        for url in images_to_check:
            # Extract filename from Special:Redirect/file/NAME or /images/.../NAME
            if "Special:Redirect/file/" in url:
                name = url.split("Special:Redirect/file/")[-1]
                name = name.split("?")[0]
                file_names.append(f"File:{name}")
                url_to_name[url] = f"File:{name}"
            else:
                # Try to extract from path
                name = url.split("/")[-1]
                if name:
                    file_names.append(f"File:{name}")
                    url_to_name[url] = f"File:{name}"

        # Batch in groups of 50
        batch_size = 50
        unavailable_names = set()
        for i in range(0, len(file_names), batch_size):
            batch = file_names[i:i + batch_size]
            try:
                data = client.query(titles="|".join(batch), prop="imageinfo", iiprop="url|size")
                pages = data.get("query", {}).get("pages", {})
                for pid, pinfo in pages.items():
                    if "missing" in pinfo:
                        unavailable_names.add(pinfo.get("title", ""))
                    elif not pinfo.get("imageinfo"):
                        unavailable_names.add(pinfo.get("title", ""))
            except Exception as e:
                log.warning("Image validation API query failed for batch %d-%d: %s", i, i + batch_size, e)

        for url, files in images_to_check.items():
            name = url_to_name.get(url)
            if name and name in unavailable_names:
                unavailable.append({
                    "url": url,
                    "files": files,
                    "reason": "api_missing",
                })
    else:
        # Without client, just list all external images (no validation possible)
        for url, files in images_to_check.items():
            unavailable.append({
                "url": url,
                "files": files,
                "reason": "unchecked_external",
            })

    return unavailable


def run_validation(output_dir: str, client: Optional[ApiClient] = None) -> dict:
    """Run full L6 validation suite and write report."""
    report = {
        "broken_links": validate_links(output_dir),
        "empty_content": validate_content_integrity(output_dir),
        "unavailable_images": validate_images(output_dir, client),
    }
    report_path = os.path.join(output_dir, "validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log.info("Validation report saved to %s", report_path)
    log.info("L6: %d broken links, %d empty files, %d unavailable images",
             len(report["broken_links"]), len(report["empty_content"]), len(report["unavailable_images"]))
    return report


# ===========================================================================
# HTML Rendered Acquisition Strategy (Change: html-rendered-wiki-crawl)
# ===========================================================================

class HtmlRenderedAcquisitionStrategy:
    """Content acquisition fetching server-rendered HTML via action=parse&prop=text."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"html_parse"}

    def fetch_page_content(self, client: ApiClient, title: str, strategy: dict) -> dict:
        # Primary: rendered HTML
        data = client.parse(page=title, prop="text")
        html = data.get("parse", {}).get("text", {}).get("*", "")

        result = {"wikitext": None, "html": html, "rendered_html": html, "images": None}

        if not html:
            # Fallback to wikitext
            log.warning("Empty HTML for %s, falling back to wikitext", title)
            try:
                wt_data = client.parse(page=title, prop="wikitext")
                wikitext = wt_data.get("parse", {}).get("wikitext", {}).get("*", "")
                result["wikitext"] = wikitext
            except RuntimeError as e:
                log.warning("Wikitext fallback failed for %s: %s", title, e)

        # Also fetch images list for potential frontmatter injection
        try:
            img_data = client.parse(page=title, prop="images")
            images = img_data.get("parse", {}).get("images", [])
            result["images"] = images
        except RuntimeError as e:
            log.debug("Failed to fetch images for %s: %s", title, e)

        return result


# ===========================================================================
# Semantic Directory Mapping (Change: html-rendered-wiki-crawl)
# ===========================================================================

def title_to_filepath(title: str, ns: int) -> tuple[str, str]:
    """Map a wiki page title to (target_directory, target_filename).

    Rules:
      - ns=0 (main/StS1):  root / {slug}.md
      - ns=3000 (StS2):    Slay_the_Spire_2 / {slug}.md
      - ns=14 (Category):  {slug} / index.md
    """
    slug = title.replace(" ", "_").replace(":", "_").replace("/", "_")

    if ns == 14:
        # Category page
        name = title.removeprefix("Category:")
        dir_name = name.replace(" ", "_").replace(":", "_").replace("/", "_")
        return (dir_name, "index.md")
    elif ns == 3000:
        # StS2 namespace
        name = title.removeprefix("Slay the Spire 2:")
        slug = name.replace(" ", "_").replace(":", "_").replace("/", "_")
        return ("Slay_the_Spire_2", f"{slug}.md")
    else:
        # ns=0 and anything else
        return ("", f"{slug}.md")


# ===========================================================================
# HTML to Markdown Converter (Change: html-rendered-wiki-crawl)
# ===========================================================================

class HtmlToMarkdownConverter:
    """Convert MediaWiki server-rendered HTML to standard Markdown.

    Based on wiki.gg project experience (cross-repo reference:
    /Users/nantasmac/projects/personal/wiki.gg/src/wiki_gg/convert/markdown.py
    and clean/html.py).
    """

    _REMOVAL_SELECTORS = (
        ".mw-editsection",
        ".toc",
        "#toc",
        ".hatnote",
        ".druid-infobox",
    )

    _BLOCK_TAGS = {
        "blockquote", "div", "h1", "h2", "h3", "h4", "h5", "h6",
        "hr", "ol", "p", "pre", "table", "ul",
    }

    def __init__(self, wiki_domain: str = "slaythespire.wiki.gg"):
        self.wiki_domain = wiki_domain
        self.title_to_path: dict[str, tuple[str, str]] = {}

    def build_link_index(self, manifest_pages: list[dict]):
        """Build title -> (target_directory, target_filename) index."""
        self.title_to_path = {
            p["title"]: (p["target_directory"], p["target_filename"])
            for p in manifest_pages
        }

    def clean_html(self, html: str) -> str:
        """Remove wiki UI noise and hidden elements."""
        try:
            from selectolax.parser import HTMLParser
        except ImportError:
            # Fallback: simple regex-based cleaning
            return self._regex_clean(html)

        parser = HTMLParser(html)

        # Remove by selectors
        for selector in self._REMOVAL_SELECTORS:
            for node in parser.css(selector):
                node.decompose()

        # Remove infobox edit icons
        for node in parser.css('img[src*="ModuleEditIcon"]'):
            parent = node.parent
            if parent:
                parent.decompose()

        # Remove DRUID card frame images (composed parts, not the full art)
        for node in parser.css('img[src*="StS2_Bg"], img[src*="StS2_Frame"], img[src*="StS2_Banner"], img[src*="StS2_Type"]'):
            node.decompose()
        for node in parser.css('img[src*="StS2_Card"][src*="Orb"]'):
            node.decompose()
        # Remove card art illustration (art-only, not the complete card)
        for node in parser.css('img[src*="Art.png"]'):
            node.decompose()

        # Remove display:none elements
        for node in parser.css("[style]"):
            style = node.attributes.get("style", "")
            if "display:none" in style.replace(" ", ""):
                node.decompose()

        # Extract body or mw-parser-output
        body = parser.body
        if body is not None:
            return body.html
        root = parser.css_first(".mw-parser-output")
        if root is not None:
            return root.html
        return parser.html

    def _regex_clean(self, html: str) -> str:
        """Fallback cleaning without selectolax."""
        # Remove edit sections
        html = re.sub(r'<div class="mw-editsection"[^\u003e]*>.*?</div>', '', html, flags=re.DOTALL)
        # Remove TOC
        html = re.sub(r'<div[^\u003e]*id="toc"[^\u003e]*>.*?</div>', '', html, flags=re.DOTALL)
        html = re.sub(r'<div[^\u003e]*class="toc"[^\u003e]*>.*?</div>', '', html, flags=re.DOTALL)
        # Remove hatnotes
        html = re.sub(r'<div[^\u003e]*class="hatnote"[^\u003e]*>.*?</div>', '', html, flags=re.DOTALL)
        # Remove DRUID card frame images
        html = re.sub(r'<img[^>]*src="[^"]*StS2_Bg[^"]*"[^>]*/?>', '', html)
        html = re.sub(r'<img[^>]*src="[^"]*StS2_Frame[^"]*"[^>]*/?>', '', html)
        html = re.sub(r'<img[^>]*src="[^"]*StS2_Banner[^"]*"[^>]*/?>', '', html)
        html = re.sub(r'<img[^>]*src="[^"]*StS2_Type[^"]*"[^>]*/?>', '', html)
        html = re.sub(r'<img[^>]*src="[^"]*StS2_Card[^"]*Orb[^"]*"[^>]*/?>', '', html)
        html = re.sub(r'<img[^>]*src="[^"]*Art.png[^"]*"[^>]*/?>', '', html)
        # Remove display:none elements
        html = re.sub(r'<[^\u003e]*style="[^"]*display:\s*none[^"]*"[^\u003e]*>.*?</\w+\u003e', '', html, flags=re.DOTALL)
        return html

    def convert(self, html: str, source_dir: str = "") -> str:
        """Convert cleaned HTML to Markdown."""
        try:
            from selectolax.parser import HTMLParser, Node
        except ImportError:
            # Fallback: very basic conversion
            return self._regex_convert(html)

        parser = HTMLParser(f'<div data-wrapper="root">{html}</div>')
        root = parser.css_first('[data-wrapper="root"]')
        if root is None:
            return ""

        rendered = self._render_blocks(self._child_nodes(root), source_dir=source_dir)
        return rendered.strip()

    def _render_blocks(self, nodes, source_dir: str = "") -> str:
        blocks = []
        for node in nodes:
            block = self._render_block(node, source_dir=source_dir)
            if block:
                blocks.append(block.strip("\n"))
        return "\n\n".join(block for block in blocks if block).strip()

    def _render_block(self, node, source_dir: str = "", list_level: int = 0) -> str:
        tag = node.tag

        if tag == "-text":
            return self._normalize_text(node.text(deep=True, separator=" ", strip=False))

        if tag in {"div", "section", "article", "span"}:
            if self._has_block_children(node):
                return self._render_blocks(self._child_nodes(node), source_dir=source_dir)
            return self._render_inline_children(node, source_dir=source_dir)

        if tag in {"p", "dd", "dt"}:
            return self._render_inline_children(node, source_dir=source_dir)

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            if level == 1:
                level = 2
            text = self._render_inline_children(node, source_dir=source_dir)
            return f'{"#" * level} {text}'.strip()

        if tag in {"ul", "ol"}:
            return self._render_list(node, source_dir=source_dir, level=list_level)

        if tag == "blockquote":
            body = self._render_blocks(self._child_nodes(node), source_dir=source_dir) or self._render_inline_children(node, source_dir=source_dir)
            lines = body.splitlines() or [""]
            return "\n".join(
                ">" if not line.strip() else f"> {line}" for line in lines
            ).strip()

        if tag == "pre":
            code = node.text(deep=True, separator="", strip=False).strip("\n")
            if not code:
                return ""
            return f"```\n{code}\n```"

        if tag == "hr":
            return "---"

        if tag == "table":
            return self._render_table(node, source_dir=source_dir)

        if tag == "img":
            return self._render_image(node)

        if tag == "br":
            return ""

        if tag in {"strong", "b", "em", "i", "code", "a"}:
            return self._render_inline(node, source_dir=source_dir)

        if self._has_block_children(node):
            return self._render_blocks(self._child_nodes(node), source_dir=source_dir)

        return self._render_inline_children(node, source_dir=source_dir)

    def _render_list(self, node, source_dir: str = "", level: int = 0) -> str:
        lines = []
        index = 1
        bullet = "1." if node.tag == "ol" else "-"

        for child in self._child_nodes(node):
            if child.tag != "li":
                continue
            item_prefix = f"{index}." if node.tag == "ol" else bullet
            item_lines = self._render_list_item(child, source_dir=source_dir, level=level, prefix=item_prefix)
            if item_lines:
                lines.extend(item_lines)
                if node.tag == "ol":
                    index += 1
        return "\n".join(lines).rstrip()

    def _render_list_item(self, node, source_dir: str = "", level: int = 0, prefix: str = "") -> list[str]:
        indent = "  " * level
        inline_parts = []
        nested_lines = []

        for child in self._child_nodes(node):
            if child.tag in {"ul", "ol"}:
                nested = self._render_list(child, source_dir=source_dir, level=level + 1)
                if nested:
                    nested_lines.extend(nested.splitlines())
                continue
            rendered = self._render_inline(child, source_dir=source_dir)
            if rendered:
                inline_parts.append(rendered)

        if inline_parts:
            header = f"{indent}{prefix} {self._render_inline_part_list(inline_parts)}"
        else:
            header = f"{indent}{prefix}"
        return [header, *nested_lines]

    def _render_table(self, node, source_dir: str = "") -> str:
        rows = [self._extract_row(row, source_dir=source_dir) for row in node.css("tr")]
        rows = [row for row in rows if row]
        if not rows:
            return ""

        if self._is_simple_markdown_table(node, rows):
            header = rows[0]
            separator = ["---"] * len(header)
            body = rows[1:]
            table_lines = [
                self._markdown_table_line(header),
                self._markdown_table_line(separator),
            ]
            table_lines.extend(self._markdown_table_line(row) for row in body)
            return "\n".join(table_lines)

        # Fallback: key-value or flat list
        fallback_lines = []
        for row in rows:
            if len(row) == 2:
                fallback_lines.append(f"- **{row[0]}:** {row[1]}")
            else:
                fallback_lines.append(f"- {' | '.join(row)}")
        return "\n".join(fallback_lines)

    def _extract_row(self, row, source_dir: str = "") -> list[str]:
        cells = []
        for child in self._child_nodes(row):
            if child.tag not in {"th", "td"}:
                continue
            cells.append(self._render_inline_children(child, source_dir=source_dir) or "")
        return cells

    def _is_simple_markdown_table(self, node, rows: list[list[str]]) -> bool:
        if len(rows) < 2:
            return False
        width = len(rows[0])
        if width == 0:
            return False
        if any(len(row) != width for row in rows):
            return False
        first_row = node.css_first("tr")
        if first_row is None:
            return False
        has_header = any(child.tag == "th" for child in self._child_nodes(first_row))
        if not has_header:
            return False
        for cell in node.css("th, td"):
            colspan = cell.attributes.get("colspan")
            rowspan = cell.attributes.get("rowspan")
            if colspan not in {None, "1"} or rowspan not in {None, "1"}:
                return False
        return True

    def _markdown_table_line(self, cells: list[str]) -> str:
        escaped = [cell.replace("|", "\\|") for cell in cells]
        return f"| {' | '.join(escaped)} |"

    def _render_inline_children(self, node, source_dir: str = "") -> str:
        return self._render_inline_part_list(
            self._render_inline(child, source_dir=source_dir) for child in self._child_nodes(node)
        )

    def _render_inline_part_list(self, parts) -> str:
        rendered = self._join_inline_parts(parts)
        return rendered

    def _render_inline(self, node, source_dir: str = "") -> str:
        tag = node.tag

        if tag == "-text":
            return self._normalize_text(node.text(deep=True, separator=" ", strip=False))

        if tag in {"strong", "b"}:
            text = self._render_inline_children(node, source_dir=source_dir)
            return f"**{text}**" if text else ""

        if tag in {"em", "i"}:
            text = self._render_inline_children(node, source_dir=source_dir)
            return f"*{text}*" if text else ""

        if tag == "code":
            text = node.text(deep=True, separator="", strip=False).strip()
            return f"`{text}`" if text else ""

        if tag == "br":
            return "\n"

        if tag == "a":
            text = self._render_inline_children(node, source_dir=source_dir) or self._normalize_text(
                node.text(deep=True, separator=" ", strip=False)
            )
            href = self._normalize_href(node.attributes.get("href"))
            if not text:
                return ""
            if not href:
                return text
            # Check if it's a wiki internal link
            wiki_link = self._to_markdown_link(href, text, source_dir)
            if wiki_link is not None:
                return wiki_link
            return f"[{text}]({href})"

        if tag == "img":
            return self._render_image(node)

        if tag in self._BLOCK_TAGS:
            return self._render_block(node, source_dir=source_dir)

        if not any(True for _ in self._child_nodes(node)):
            return self._normalize_text(node.text(deep=True, separator=" ", strip=False))

        return self._render_inline_children(node, source_dir=source_dir)

    def _render_image(self, node) -> str:
        src = self._normalize_href(node.attributes.get("src"))
        if not src:
            return ""
        alt = self._normalize_text(node.attributes.get("alt") or node.attributes.get("title") or "image")
        return f"![{alt}]({src})"

    def _normalize_href(self, href: Optional[str]) -> Optional[str]:
        if href is None:
            return None
        normalized = href.strip()
        if not normalized:
            return None
        if normalized.startswith("about:/wiki/"):
            normalized = normalized.replace("about:/wiki/", f"https://{self.wiki_domain}/wiki/", 1)
        elif normalized.startswith("/wiki/") or normalized.startswith("/images/"):
            normalized = f"https://{self.wiki_domain}{normalized}"
        elif normalized.startswith("#"):
            return normalized
        elif normalized.startswith("//"):
            normalized = f"https:{normalized}"
        elif normalized.startswith("about:blank#"):
            normalized = normalized.replace("about:blank", "", 1)
        return normalized

    def _to_markdown_link(self, href: str, text: str, source_dir: str) -> Optional[str]:
        """Convert wiki internal /wiki/... links to relative Markdown links."""
        if not href.startswith(f"https://{self.wiki_domain}/wiki/"):
            return None

        title = href[len(f"https://{self.wiki_domain}/wiki/"):]
        # Strip query parameters and fragment from wiki page URLs
        title = title.split("?")[0].split("#")[0]
        title = title.replace("_", " ")

        # Skip non-exportable namespaces
        if title.startswith(("File:", "Category:", "Template:", "Talk:", "Special:", "Help:")):
            return None

        # Look up target path
        target = self.title_to_path.get(title)
        if target is None:
            # Try with underscores
            target = self.title_to_path.get(title.replace(" ", "_"))
        if target is None:
            return None

        target_dir, target_file = target
        if target_dir == source_dir:
            return f"[{text}]({target_file})"

        # Compute relative path
        import os
        source_path = source_dir.replace("/", os.sep) if source_dir else "."
        target_path = os.path.join(target_dir.replace("/", os.sep), target_file) if target_dir else target_file
        rel = os.path.relpath(target_path, source_path).replace(os.sep, "/")
        return f"[{text}]({rel})"

    def _join_inline_parts(self, parts) -> str:
        result = ""
        for part in parts:
            if not part:
                continue
            if part == "\n":
                result = result.rstrip() + "\n"
                continue
            if not result or result.endswith(("\n", " ")):
                result += part
                continue
            if part.startswith(("\n", ".", ",", ";", ":", "!", "?", ")", "]")):
                result += part
                continue
            result += f" {part}"
        return result.strip()

    def _normalize_text(self, text: str) -> str:
        collapsed = re.sub(r"\s+", " ", text)
        return collapsed.strip()

    def _has_block_children(self, node) -> bool:
        return any(child.tag in self._BLOCK_TAGS for child in self._child_nodes(node))

    @staticmethod
    def _child_nodes(node):
        child = node.child
        while child is not None:
            yield child
            child = child.next

    def _regex_convert(self, html: str) -> str:
        """Very basic fallback conversion without selectolax."""
        # Strip tags, preserve some structure
        text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        text = re.sub(r'</p>\s*<p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^\u003e]+>', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


# ===========================================================================
# Card List Page Splitting (Change: html-rendered-wiki-crawl)
# ===========================================================================

def split_card_list_pages(html, output_dir, manifest_pages, domain, list_page_title):
    """Parse Cards_List HTML and generate sub-pages grouped by color and rarity.

    Returns (pages_written, page_info_list).
    """
    try:
        from selectolax.parser import HTMLParser
    except ImportError:
        return 0, []

    if "cardsContainer" not in html and "card-box" not in html:
        return 0, []

    parser = HTMLParser(html)
    container = parser.css_first("#cardsContainer")
    if container is None:
        container = parser.body
    if container is None:
        return 0, []

    cards = container.css(".card-box")
    if not cards:
        return 0, []

    # Group cards by (color, rarity)
    from collections import defaultdict
    groups = defaultdict(list)
    for card in cards:
        color = card.attributes.get("data-color") or "Unknown"
        rarity = card.attributes.get("data-rarity") or "Unknown"
        ctype = card.attributes.get("data-type", "")

        # Get card image and link
        card_link = card.css_first(".img-base a")
        card_img = card.css_first(".img-base img")
        href = card_link.attributes.get("href", "") if card_link else ""
        src = card_img.attributes.get("src", "") if card_img else ""

        # Extract card name from link title or img alt
        name = ""
        if card_link:
            name = card_link.attributes.get("title", "")
        if not name:
            name = card_img.attributes.get("alt", "") if card_img else ""
        if not name:
            name = card.attributes.get("data-name", "")

        # Get description
        desc_el = card.css_first(".card-text .desc-base")
        desc = desc_el.text(deep=True, separator=" ", strip=True) if desc_el else ""

        # Normalize href
        if href.startswith("/wiki/"):
            href = f"https://{domain}{href}"
        if src.startswith("/images/"):
            src = f"https://{domain}{src}"

        groups[(color, rarity)].append({
            "name": name,
            "type": ctype,
            "color": color,
            "rarity": rarity,
            "href": href,
            "img_src": src,
            "description": desc,
        })

    # Build title-to-path mapping
    title_to_path = {}
    for p in manifest_pages:
        title_to_path[p["title"]] = (p["target_directory"], p["target_filename"])

    # Find the base directory from the list page
    base_dir = ""
    for p in manifest_pages:
        if p["title"] == list_page_title:
            base_dir = p["target_directory"]
            break

    pages_written = 0
    page_infos = []

    for (color, rarity), card_list in sorted(groups.items()):
        # Sanitize directory names
        color_dir = color.replace(" ", "_").replace(".", "")
        rarity_file = rarity.replace(" ", "_").replace(".", "") + ".md"
        sub_dir = os.path.join(output_dir, base_dir, color_dir)
        os.makedirs(sub_dir, exist_ok=True)

        lines = ["---"]
        lines.append(f'title: "{list_page_title} - {color} {rarity} Cards"')
        lines.append(f"rarity: {rarity}")
        lines.append(f"color: {color}")
        lines.append(f"card_count: {len(card_list)}")
        lines.append("---")
        lines.append("")
        lines.append(f"# {color} — {rarity} Cards")
        lines.append("")

        for card in card_list:
            # Derive page name from href
            page_title = card["name"]
            page_path = None
            card_href = card.get("href", "")
            if card_href and "/wiki/" in card_href:
                title_from_url = card_href.split("/wiki/")[-1].replace("_", " ")
                if title_from_url in title_to_path:
                    td, tf = title_to_path[title_from_url]
                    rel_dir = td.removeprefix(base_dir).strip("/")
                    page_path = f"{rel_dir}/{tf}" if rel_dir else tf

            # Get card name (use display name without namespace prefix)
            full_name = card["name"] or ""
            display_name = full_name.split(":")[-1].replace("_", " ") if full_name else ""

            # If name still empty, derive from href
            if not display_name and card_href and "/wiki/" in card_href:
                from urllib.parse import unquote
                href_title = card_href.split("/wiki/")[-1].split("#")[0]
                display_name = unquote(href_title).replace("_", " ").split(":")[-1]

            # Get page link target
            if not display_name:
                display_name = "Unknown"
            link_target = page_path if page_path else None
            if not link_target and card_href and "/wiki/" in card_href:
                href_title = card_href.split("/wiki/")[-1].split("#")[0]
                link_target = href_title.replace(" ", "_").replace(":", "_") + ".md"

            # Heading with link
            heading = f"## [{display_name}]({link_target})" if link_target else f"## {display_name}"
            lines.append(heading)
            lines.append("")

            # Image below heading
            if card["img_src"]:
                lines.append(f"![{display_name}]({card['img_src']})")
                lines.append("")

            # Metadata line
            type_str = card['type'] or ''
            lines.append(f"*{card['rarity']} - {card['color']} - {type_str}*")
            lines.append("")

            # Description
            if card["description"]:
                lines.append(card["description"])
                lines.append("")

            # Divider
            lines.append("---")
            lines.append("")

        filepath = os.path.join(sub_dir, rarity_file)
        with open(filepath, "w", encoding="utf-8") as f_out:
            f_out.write("\n".join(lines).strip() + "\n")
        pages_written += 1
        page_infos.append({"color": color, "rarity": rarity, "file": filepath, "count": len(card_list)})

    # Generate index.md for each color directory
    for (color, _), card_list in groups.items():
        color_dir = color.replace(" ", "_").replace(".", "")
        index_path = os.path.join(output_dir, base_dir, color_dir, "index.md")
        idx_lines = ["---"]
        idx_lines.append(f'title: "{color} Cards"')
        idx_lines.append(f"color: {color}")
        idx_lines.append("---")
        idx_lines.append("")
        idx_lines.append(f"# {color} Cards")
        idx_lines.append("")
        idx_lines.append("| Rarity | Count |")
        idx_lines.append("| --- | --- |")
        for (c, r), cl in sorted(groups.items()):
            if c == color:
                rf = r.replace(" ", "_").replace(".", "") + ".md"
                idx_lines.append(f"| [{r}]({rf}) | {len(cl)} |")
        idx_lines.append("")
        with open(index_path, "w", encoding="utf-8") as f_out:
            f_out.write("\n".join(idx_lines) + "\n")

    return pages_written, page_infos


# ===========================================================================
# Card Stats Extraction (Change: html-rendered-wiki-crawl)
# ===========================================================================

def extract_card_stats(html: str, domain: str = "slaythespire.wiki.gg") -> str:
    """Extract DRUID card infobox data and format as structured Markdown."""
    try:
        from selectolax.parser import HTMLParser
    except ImportError:
        return ""
    import re as _re

    parser = HTMLParser(html)
    infobox = parser.css_first(".druid-infobox")
    if infobox is None:
        return ""

    def _get_tab_data(row_sel: str) -> tuple[str, str]:
        """Return (base_value, upgraded_value) from DRUID toggleable rows."""
        row = infobox.css_first(row_sel)
        if row is None:
            return ("", "")
        tabs = row.css(".druid-toggleable-data")
        base_val = ""
        upg_val = ""
        for tab in tabs:
            key = tab.attributes.get("data-druid-tab-key", "")
            txt = tab.text(deep=True, separator=" ", strip=True)
            txt = _re.sub(r'\s+', ' ', txt)
            if "Upgraded" in key:
                upg_val = txt
            else:
                base_val = txt
        return (base_val, upg_val)

    def _get_flat_text(row_sel: str) -> str:
        """Get flat text from a DRUID row."""
        row = infobox.css_first(row_sel)
        if row is None:
            return ""
        txt = row.text(deep=True, separator=" ", strip=True)
        return _re.sub(r'\s+', ' ', txt)

    name_base, name_upg = _get_tab_data(".druid-row-Name")
    cost_base, cost_upg = _get_tab_data(".druid-row-EnergyCost")
    desc_base, desc_upg = _get_tab_data(".druid-row-Description")
    rarity_text = _get_flat_text(".druid-row-RarityClass")
    type_text = _get_flat_text(".druid-row-Type")

    rarity_clean = rarity_text.replace("Card", "").strip()
    rarity_clean = _re.sub(r'\s+', ' ', rarity_clean)

    lines = []
    lines.append("## Card Stats")
    lines.append("")
    lines.append("| | Base | Upgraded |")
    lines.append("| --- | --- | --- |")
    if name_base:
        upg_name = name_upg if name_upg != name_base else name_base
        lines.append(f"| **Name** | {name_base} | {upg_name} |")
    if cost_base:
        upg_cost = cost_upg if cost_upg != cost_base else cost_base
        lines.append(f"| **Cost** | {cost_base} | {upg_cost} |")
    if type_text:
        lines.append(f"| **Type** | {type_text} | {type_text} |")
    lines.append(f"| **Rarity, Color** | {rarity_clean} | {rarity_clean} |")
    lines.append("")

    if desc_base:
        lines.append("### Description")
        lines.append("")
        lines.append(f"**Base {name_base}:** {desc_base}")
        if desc_upg and desc_upg != desc_base:
            lines.append(f"")
            lines.append(f"**Upgraded {name_upg}:** {desc_upg}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)
