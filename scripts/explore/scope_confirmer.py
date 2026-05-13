"""ScopeConfirmer — generate structured confirmation prompts for 4-round ask_user flow.

Consumes deep discovery JSON and produces question/option structures for the
chrome-agent workflow skill layer to present via ask_user.

Round 1: Content scope (all / specific sections / to be specified)
Round 2: Page granularity (summary+individual / individual only / summary only)
Round 3: Sample selection (agent recommends 4-8, user confirms or adjusts)
Round 4: Output format (Markdown+frontmatter / pure Markdown / JSON)
"""

import random
from typing import Optional


def confirm_scope(discovery: dict) -> list[dict]:
    """Generate the 4-round confirmation question structure.

    Args:
        discovery: Deep discovery result containing structure_mapping, api_discovery, etc.

    Returns:
        List of 4 question dicts, each with id, label, prompt, type, options.
    """
    structure = discovery.get("structure_mapping", {})
    nav_sections = structure.get("nav_sections", [])
    page_type = structure.get("page_type", "article")
    content_structure = structure.get("content_structure", {})

    questions = []

    # Round 1: Content scope
    scope_options = [
        {"label": "全部内容（所有栏目）", "value": "all"},
        {"label": "指定栏目（后续选择）", "value": "specific"},
        {"label": "暂不指定，后续补充", "value": "unspecified"},
    ]
    if nav_sections:
        # Add detected sections as a preview
        preview = ", ".join(nav_sections[:5])
        if len(nav_sections) > 5:
            preview += f" 等共 {len(nav_sections)} 个栏目"
        scope_prompt = (
            f"检测到以下栏目：{preview}\n"
            "请选择要抓取的内容范围："
        )
    else:
        scope_prompt = "未检测到明确的栏目结构。请选择内容范围："

    questions.append({
        "id": "scope",
        "label": "内容范围",
        "prompt": scope_prompt,
        "type": "single",
        "options": scope_options,
    })

    # Round 2: Page granularity
    granularity_options = [
        {"label": "汇总页 + 独立条目页", "value": "summary_and_individual"},
        {"label": "仅独立条目页", "value": "individual_only"},
        {"label": "仅汇总页", "value": "summary_only"},
    ]

    # Check if any nav sections look like they only have list/summary pages
    has_summary_only = page_type == "list" and not content_structure.get("has_infobox")
    granularity_prompt = "请选择页面粒度："
    if has_summary_only:
        granularity_prompt += "\n⚠️ 注意：当前页面看起来是汇总页，可能没有独立的详细条目页。"

    questions.append({
        "id": "granularity",
        "label": "页面粒度",
        "prompt": granularity_prompt,
        "type": "single",
        "options": granularity_options,
    })

    # Round 3: Output format
    questions.append({
        "id": "format",
        "label": "输出格式",
        "prompt": "请选择输出格式：",
        "type": "single",
        "options": [
            {"label": "Markdown + YAML frontmatter", "value": "markdown_frontmatter"},
            {"label": "纯 Markdown（无 frontmatter）", "value": "markdown_plain"},
            {"label": "JSON", "value": "json"},
        ],
    })

    return questions


def recommend_samples(
    discovery: dict,
    scope_result: Optional[dict] = None,
    count: int = 6,
) -> dict:
    """Recommend sample pages based on discovery results.

    Args:
        discovery: Deep discovery result.
        scope_result: Optional result from Round 1 scope confirmation.
        count: Number of samples to recommend (default 6, range 4-8).

    Returns:
        {
            "question": ask_user question dict for Round 3,
            "recommendations": list of recommended sample URLs/titles,
        }
    """
    structure = discovery.get("structure_mapping", {})
    nav_sections = structure.get("nav_sections", [])
    page_type = structure.get("page_type", "article")
    content_structure = structure.get("content_structure", {})
    api_config = discovery.get("api_discovery", [{}])[0] if discovery.get("api_discovery") else None
    domain = discovery.get("target_url", "")

    # Build recommendations
    recommendations = []
    seen_types = set()

    # Strategy: cover different content types
    candidates = []

    # Add home/main page if available
    if page_type == "home":
        candidates.append({
            "title": "Home Page",
            "url": domain,
            "type": "home",
            "reason": "首页，了解站点整体结构",
        })
        seen_types.add("home")

    # Add a list/category page
    if nav_sections:
        candidates.append({
            "title": nav_sections[0],
            "url": f"{domain}/wiki/{nav_sections[0].replace(' ', '_')}",
            "type": "list",
            "reason": "栏目汇总页",
        })
        seen_types.add("list")

    # Add an article page (prefer one with infobox)
    if content_structure.get("has_infobox") and nav_sections:
        candidates.append({
            "title": f"{nav_sections[0]} Example",
            "url": f"{domain}/wiki/{nav_sections[0].replace(' ', '_')}_Example",
            "type": "article_infobox",
            "reason": "含 infobox 的典型条目页",
        })
        seen_types.add("article_infobox")

    # Add a plain article page
    if nav_sections:
        candidates.append({
            "title": f"{nav_sections[0]} Overview",
            "url": f"{domain}/wiki/{nav_sections[0].replace(' ', '_')}_Overview",
            "type": "article",
            "reason": "普通条目页（无 infobox）",
        })
        seen_types.add("article")

    # Add gallery page if images detected
    if content_structure.get("has_card_pattern") or content_structure.get("has_tables"):
        candidates.append({
            "title": "Gallery or Table Page",
            "url": f"{domain}/wiki/Gallery",
            "type": "gallery",
            "reason": "含图片/表格的特殊页面",
        })
        seen_types.add("gallery")

    # Add edge case: page from a different section
    if len(nav_sections) > 1:
        candidates.append({
            "title": nav_sections[1],
            "url": f"{domain}/wiki/{nav_sections[1].replace(' ', '_')}",
            "type": "list_alt",
            "reason": "不同栏目的页面",
        })
        seen_types.add("list_alt")

    # Deduplicate and limit
    seen_titles = set()
    for c in candidates:
        if c["title"] not in seen_titles and len(recommendations) < min(count, 8):
            recommendations.append(c)
            seen_titles.add(c["title"])

    # Ensure minimum count
    while len(recommendations) < max(count, 4):
        idx = len(recommendations)
        recommendations.append({
            "title": f"Sample Page {idx + 1}",
            "url": f"{domain}/wiki/Sample_{idx + 1}",
            "type": "article",
            "reason": "补充样本",
        })

    # Build question
    rec_lines = []
    for i, rec in enumerate(recommendations, 1):
        rec_lines.append(f"{i}. {rec['title']} — {rec['reason']}")

    question = {
        "id": "samples",
        "label": "样本确认",
        "prompt": (
            f"根据发现结果，推荐以下 {len(recommendations)} 个样本页面:\n"
            + "\n".join(rec_lines)
            + "\n\n请确认这些样本是否合适，或提供需要调整的说明。"
        ),
        "type": "single",
        "options": [
            {"label": "确认推荐样本", "value": "confirm"},
            {"label": "需要调整（请说明）", "value": "adjust"},
        ],
    }

    return {
        "question": question,
        "recommendations": recommendations,
    }


def build_confirmation_payload(discovery: dict) -> dict:
    """Build the full confirmation payload for the skill layer.

    Returns:
        {
            "rounds": [Round1, Round2, Round4 question dicts],
            "sample_round": Round3 payload with recommendations,
        }
    """
    scope_questions = confirm_scope(discovery)
    sample_payload = recommend_samples(discovery)

    return {
        "rounds": scope_questions,  # Rounds 1, 2, 4
        "sample_round": sample_payload,  # Round 3
        "discovery_summary": {
            "page_type": discovery.get("structure_mapping", {}).get("page_type"),
            "nav_sections": discovery.get("structure_mapping", {}).get("nav_sections", []),
            "protection": discovery.get("protection", {}).get("type"),
            "api_detected": [a.get("type") for a in discovery.get("api_discovery", [])],
        },
    }


def main():
    """CLI helper: read discovery JSON from stdin and output confirmation payload."""
    import json
    import sys

    discovery = json.load(sys.stdin)
    payload = build_confirmation_payload(discovery)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
