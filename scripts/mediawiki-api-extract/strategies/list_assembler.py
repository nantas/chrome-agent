"""List page assembler strategy implementations."""

import logging
import re
from typing import Optional
from urllib.parse import quote as url_quote

log = logging.getLogger("mediawiki-api-extract")


class FrontmatterDrivenListPageAssembler:
    """Default list page assembler building index.md from frontmatter data."""

    def assemble_index(self, list_page_title: str, pages_in_dir: list[dict],
                       list_content: Optional[str], frontmatter_fields: list[str],
                       domain: str) -> str:
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


class HybridListPageAssembler:
    """List page assembler preferring rendered HTML tables, with frontmatter fallback."""

    def assemble_index(self, list_page_title: str, pages_in_dir: list[dict],
                       list_content: Optional[str], frontmatter_fields: list[str],
                       domain: str) -> str:
        rendered_html = None
        if isinstance(list_content, dict):
            rendered_html = list_content.get("rendered_html")
            list_content = list_content.get("wikitext", "")

        if rendered_html:
            table_md = self._extract_table_from_html(rendered_html, pages_in_dir, frontmatter_fields, domain)
            if table_md:
                if "<!-- DPL_TABLE_PLACEHOLDER -->" in (list_content or ""):
                    body = list_content.replace("<!-- DPL_TABLE_PLACEHOLDER -->", table_md)
                else:
                    body = (list_content or "") + "\n\n" + table_md
                body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
                return body

        fallback = FrontmatterDrivenListPageAssembler()
        return fallback.assemble_index(list_page_title, pages_in_dir, list_content, frontmatter_fields, domain)

    def _extract_table_from_html(self, html: str, pages_in_dir: list[dict],
                                  frontmatter_fields: list[str], domain: str) -> Optional[str]:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return None

        soup = BeautifulSoup(html, "html.parser")

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

        best_table = None
        best_rows = 0
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) > best_rows:
                best_rows = len(rows)
                best_table = table

        if not best_table or best_rows < 2:
            return None

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
