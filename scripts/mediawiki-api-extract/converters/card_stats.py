"""Card stats extraction and card list page splitting — independent of pipeline internals.

Can be imported and used standalone:
    from scripts.mediawiki_api_extract.converters.card_stats import extract_card_stats, split_card_list_pages
"""

import logging
import os
import re
from typing import Optional

log = logging.getLogger("mediawiki-api-extract.converters")


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

    from collections import defaultdict
    groups = defaultdict(list)
    for card in cards:
        color = card.attributes.get("data-color") or "Unknown"
        rarity = card.attributes.get("data-rarity") or "Unknown"
        ctype = card.attributes.get("data-type", "")

        card_link = card.css_first(".img-base a")
        card_img = card.css_first(".img-base img")
        href = card_link.attributes.get("href", "") if card_link else ""
        src = card_img.attributes.get("src", "") if card_img else ""

        name = ""
        if card_link:
            name = card_link.attributes.get("title", "")
        if not name:
            name = card_img.attributes.get("alt", "") if card_img else ""
        if not name:
            name = card.attributes.get("data-name", "")

        desc_el = card.css_first(".card-text .desc-base")
        desc = desc_el.text(deep=True, separator=" ", strip=True) if desc_el else ""

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

    title_to_path = {}
    for p in manifest_pages:
        title_to_path[p["title"]] = (p["target_directory"], p["target_filename"])

    base_dir = ""
    for p in manifest_pages:
        if p["title"] == list_page_title:
            base_dir = p["target_directory"]
            break

    pages_written = 0
    page_infos = []

    for (color, rarity), card_list in sorted(groups.items()):
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
            page_title = card["name"]
            page_path = None
            card_href = card.get("href", "")
            if card_href and "/wiki/" in card_href:
                title_from_url = card_href.split("/wiki/")[-1].replace("_", " ")
                if title_from_url in title_to_path:
                    td, tf = title_to_path[title_from_url]
                    rel_dir = td.removeprefix(base_dir).strip("/")
                    page_path = f"{rel_dir}/{tf}" if rel_dir else tf

            full_name = card["name"] or ""
            display_name = full_name.split(":")[-1].replace("_", " ") if full_name else ""

            if not display_name and card_href and "/wiki/" in card_href:
                from urllib.parse import unquote
                href_title = card_href.split("/wiki/")[-1].split("#")[0]
                display_name = unquote(href_title).replace("_", " ").split(":")[-1]

            if not display_name:
                display_name = "Unknown"
            link_target = page_path if page_path else None
            if not link_target and card_href and "/wiki/" in card_href:
                href_title = card_href.split("/wiki/")[-1].split("#")[0]
                link_target = href_title.replace(" ", "_").replace(":", "_") + ".md"

            heading = f"## [{display_name}]({link_target})" if link_target else f"## {display_name}"
            lines.append(heading)
            lines.append("")

            if card["img_src"]:
                lines.append(f"![{display_name}]({card['img_src']})")
                lines.append("")

            type_str = card['type'] or ''
            lines.append(f"*{card['rarity']} - {card['color']} - {type_str}*")
            lines.append("")

            if card["description"]:
                lines.append(card["description"])
                lines.append("")

            lines.append("---")
            lines.append("")

        filepath = os.path.join(sub_dir, rarity_file)
        with open(filepath, "w", encoding="utf-8") as f_out:
            f_out.write("\n".join(lines).strip() + "\n")
        pages_written += 1
        page_infos.append({"color": color, "rarity": rarity, "file": filepath, "count": len(card_list)})

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
