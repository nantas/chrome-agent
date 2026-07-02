"""Capability gate — checks if explore scaffold requirements are covered by the registry.

Usage:
    from scripts.explore.capability_gate import check_requirements
    gaps = check_requirements(scaffold_dict, registry_dict)
    if gaps:
        for g in gaps:
            print(f"Gap: {g['capability']} / {g['issue']} / {g['detail']}")
"""
from __future__ import annotations


def check_requirements(scaffold: dict, registry: dict) -> list[dict]:
    """Check scaffold capabilities against the registry.

    Args:
        scaffold: Strategy scaffold dict (containing extraction config).
        registry: Loaded capability-registry.yaml dict.

    Returns:
        List of gap dicts, each with keys: capability, issue, detail.
        Empty list if all scaffold requirements are covered by the registry.
    """
    gaps = []

    # Check cleanup ops
    known_ops = {
        op["name"]
        for op in registry.get("convert", {}).get("cleanup_ops", [])
    }
    for op in scaffold.get("extraction", {}).get("cleanup", []):
        if op not in known_ops:
            gaps.append({
                "capability": "convert",
                "issue": "new_cleanup_op",
                "detail": f"Unknown cleanup op: {op}",
            })

    # Check infobox handlers
    known_handlers = {
        h["name"]
        for h in registry.get("extract", {}).get("infobox_handlers", [])
    }
    for handler_name in scaffold.get("extraction", {}).get("infobox_field_handlers", {}).keys():
        if handler_name not in known_handlers:
            gaps.append({
                "capability": "extract",
                "issue": "new_infobox_handler",
                "detail": f"Unknown handler: {handler_name}",
            })

    return gaps
