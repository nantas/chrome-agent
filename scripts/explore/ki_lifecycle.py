"""KI Lifecycle — Known Issue classification, prioritization, status tracking, and fix batching.

This module implements the KI Lifecycle Phase (Phase 3) of the explore workflow,
which runs AFTER the Architecture Gate passes.

Core functions:
- classify_ki: Map self-check failures to owner domains
- assign_priority: Assign P0-P3 priority levels
- transition_status: Manage KI status state machine
- generate_ki_table: Produce Markdown KI table for strategy.md
- update_strategy_ki_table: Replace KI section in strategy file
- plan_fix_batches: Group KIs by priority for sequential fix iterations
"""

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Valid owner domains
OWNER_STRATEGY = "strategy"
OWNER_PIPELINE = "pipeline"
OWNER_SELF_CHECK = "self_check"

VALID_OWNERS = {OWNER_STRATEGY, OWNER_PIPELINE, OWNER_SELF_CHECK}

# Valid statuses
STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_RESOLVED = "resolved"
STATUS_WONTFIX = "wontfix"
STATUS_OPEN_SYSTEMIC = "open_systemic"

VALID_STATUSES = {STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_WONTFIX, STATUS_OPEN_SYSTEMIC}

# Valid priorities
PRIORITY_P0 = "P0"
PRIORITY_P1 = "P1"
PRIORITY_P2 = "P2"
PRIORITY_P3 = "P3"

VALID_PRIORITIES = {PRIORITY_P0, PRIORITY_P1, PRIORITY_P2, PRIORITY_P3}

# Max fix iterations (priority batches)
MAX_ITERATIONS = 3

# ---------------------------------------------------------------------------
# Default S-check → owner mapping (Task 2.1.3)
# ---------------------------------------------------------------------------

# Maps self-check ID to default owner domain.
# S4 (empty content) and S7 (image wrapper) and S10 (YouTube title) are not
# listed because they are less common; they default to self_check/pipeline
# based on fixable_type heuristics in classify_ki().
_DEFAULT_OWNER_MAP: dict[str, str] = {
    "S1": OWNER_SELF_CHECK,    # Image count methodology
    "S2": OWNER_PIPELINE,      # Link resolution
    "S3": OWNER_PIPELINE,      # Infobox extraction
    "S5": OWNER_SELF_CHECK,    # Text integrity methodology
    "S6": OWNER_SELF_CHECK,    # Table counting methodology
    "S8": OWNER_PIPELINE,      # Section extraction
    "S9": OWNER_PIPELINE,      # Navigation removal
    "S11": OWNER_PIPELINE,     # Relative link conversion
    "S12": OWNER_PIPELINE,     # Infobox semantic quality
}

# ---------------------------------------------------------------------------
# Status transition table
# ---------------------------------------------------------------------------

# Legal transitions: from_status → set of allowed to_statuses
_LEGAL_TRANSITIONS: dict[str, set[str]] = {
    STATUS_OPEN: {STATUS_IN_PROGRESS, STATUS_OPEN_SYSTEMIC, STATUS_WONTFIX},
    STATUS_IN_PROGRESS: {STATUS_RESOLVED, STATUS_WONTFIX},
    # Terminal states — no outgoing transitions
    STATUS_RESOLVED: set(),
    STATUS_WONTFIX: set(),
    STATUS_OPEN_SYSTEMIC: set(),
}


# ---------------------------------------------------------------------------
# KI Classification (Tasks 2.1.1-2.1.4)
# ---------------------------------------------------------------------------

def classify_ki(failure: dict, override_owner: Optional[str] = None) -> dict:
    """Classify a self-check failure into a Known Issue with owner domain.

    Args:
        failure: A self-check result dict with keys:
            - check: str (e.g. "S1", "S5")
            - status: str (must be "fail")
            - detail: str (human-readable description)
            - fixable_type: Optional[str]
        override_owner: Explicit owner override. When provided, takes precedence
            over the default mapping (Task 2.1.4 — fixed_via override).

    Returns:
        Enriched dict with additional keys:
            - owner: str (strategy / pipeline / self_check)
            - priority: str (P0-P3, initially unset — call assign_priority())
            - ki_status: str (initially "open")

    Note:
        `priority` is set to None initially; call assign_priority() separately,
        or use run_ki_lifecycle() for the full classify→prioritize→batch workflow.
    """
    if failure.get("status") != "fail":
        raise ValueError(f"Cannot classify non-failure: {failure}")

    check_id = failure.get("check", "")
    detail = failure.get("detail", "")
    fixable_type = failure.get("fixable_type")

    # Task 2.1.4: Support explicit override
    if override_owner:
        if override_owner not in VALID_OWNERS:
            raise ValueError(f"Invalid owner: {override_owner}. Must be one of {VALID_OWNERS}")
        owner = override_owner
    else:
        # Task 2.1.2-2.1.3: Decision tree + predefined mapping
        owner = _infer_owner(check_id, detail, fixable_type)

    return {
        **failure,
        "owner": owner,
        "ki_status": STATUS_OPEN,
        "priority": None,  # Assigned later by assign_priority()
    }


def _infer_owner(check_id: str, detail: str, fixable_type: Optional[str]) -> str:
    """Infer owner domain from check ID, detail, and fixable_type.

    Decision tree (Task 2.1.2):
    1. If fixable_type suggests a pipeline fix → pipeline
    2. If check_id has a predefined mapping → use it
    3. Default to self_check
    """
    # Pipeline fixable types — indicate the converter/pipeline needs fixing
    pipeline_fixable_types = {
        "infobox_html_residue",
        "section_loss",
        "nav_leak",
        "relative_image_url",
        "relative_link",
        "infobox_mismatch",
        "id_navigation_leak",
    }

    if fixable_type in pipeline_fixable_types:
        return OWNER_PIPELINE

    # Check predefined mapping
    if check_id in _DEFAULT_OWNER_MAP:
        return _DEFAULT_OWNER_MAP[check_id]

    # Heuristic: check detail for pipeline-related keywords
    pipeline_keywords = ["extraction", "convert", "pipeline", "infobox", "nav"]
    if any(kw in detail.lower() for kw in pipeline_keywords):
        return OWNER_PIPELINE

    # Strategy-related keywords
    strategy_keywords = ["selector", "skip_pattern", "config", "cleanup_selectors"]
    if any(kw in detail.lower() for kw in strategy_keywords):
        return OWNER_STRATEGY

    # Default: self_check (methodology issue)
    return OWNER_SELF_CHECK


# ---------------------------------------------------------------------------
# Priority Assignment (Tasks 2.2.1-2.2.5)
# ---------------------------------------------------------------------------

def assign_priority(ki: dict) -> str:
    """Assign a priority level P0-P3 to a KI.

    Priority rules:
    - P0: Data corruption (wrong field values, broken links/images, navigation text in IDs)
    - P1: Quality impact (readability reduction, minor pollution, self_check false positive)
    - P2: Check methodology issues (scope/precision, no output impact)
    - P3: Skip/cosmetic (check already skipped, negligible visual impact)

    Args:
        ki: KI dict with 'check', 'detail', 'owner', etc.
            If 'priority_override' is set, that value is returned directly
            (for contextual overrides when the agent determines the default
            classification doesn't match session context).

    Returns:
        Priority string: "P0", "P1", "P2", or "P3"
    """

    # Support contextual override (e.g., template artifacts, conditional triggers)
    override = ki.get("priority_override")
    if override and override in VALID_PRIORITIES:
        return override
    check_id = ki.get("check", "")
    detail = ki.get("detail", "").lower()
    fixable_type = ki.get("fixable_type")
    owner = ki.get("owner", "")

    # P0: Data corruption (Task 2.2.2)
    if _is_p0(check_id, detail, fixable_type, owner):
        return PRIORITY_P0

    # P1: Quality impact (Task 2.2.3)
    if _is_p1(check_id, detail, fixable_type, owner):
        return PRIORITY_P1

    # P2: Check methodology (Task 2.2.4)
    if _is_p2(check_id, detail, fixable_type, owner):
        return PRIORITY_P2

    # P3: Skip/cosmetic (Task 2.2.5)
    return PRIORITY_P3


def _is_p0(check_id: str, detail: str, fixable_type: Optional[str], owner: str) -> bool:
    """P0: Critical data corruption."""
    # ID field contains navigation text or is completely wrong
    if check_id == "S12" and ("id_navigation_leak" in (fixable_type or "") or "navigation text" in detail):
        return True
    # Infobox field values completely wrong
    if "infobox" in detail and ("wrong" in detail or "corrupt" in detail):
        return True
    # Broken images or links
    if check_id == "S2" and "unresolved" in detail:
        return True
    # Fixable types indicating data corruption
    if fixable_type in {"id_navigation_leak", "infobox_mismatch"}:
        return True
    return False


def _is_p1(check_id: str, detail: str, fixable_type: Optional[str], owner: str) -> bool:
    """P1: Quality impact but not blocking."""
    # Self-check false positive (wastes debugging time)
    if owner == OWNER_SELF_CHECK and "false" in detail:
        return True
    # Readability issues (missing spaces, concatenation)
    if fixable_type == "space_normalization":
        return True
    # Image-link concatenation (missing space between image and link)
    if "concatenat" in detail or "without space" in detail:
        return True
    # Infobox field value concatenation in body
    if check_id == "S12" and "concatenat" in detail:
        return True
    # S5 version regex false positive — detail text doesn't contain "false"
    # but is a genuine self_check false positive (e.g. image URL hash matched as version)
    if check_id == "S5" and owner == OWNER_SELF_CHECK:
        return True
    # Any pipeline fixable that's not P0
    if fixable_type in {"infobox_html_residue", "section_loss", "nav_leak"}:
        return True
    return False


def _is_p2(check_id: str, detail: str, fixable_type: Optional[str], owner: str) -> bool:
    """P2: Check methodology issue, no output impact."""
    # Self-check scope/precision problems
    if owner == OWNER_SELF_CHECK:
        # Count mismatches that don't affect output
        if "count" in detail or "mismatch" in detail:
            return True
        # Image count methodology (template folding, scope issues)
        if check_id == "S1" and ("images" in detail or "found" in detail):
            return True
        # Regex false positive not already caught by P1
        if "regex" in detail or "false positive" in detail:
            return True
    return False


# ---------------------------------------------------------------------------
# Status Machine (Tasks 2.3.1-2.3.2)
# ---------------------------------------------------------------------------

def transition_status(ki: dict, new_status: str) -> dict:
    """Transition a KI to a new status.

    Args:
        ki: KI dict with 'ki_status' key.
        new_status: Target status.

    Returns:
        Updated KI dict with new ki_status.

    Raises:
        ValueError: If the transition is illegal.
    """
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {VALID_STATUSES}")

    current = ki.get("ki_status", STATUS_OPEN)
    allowed = _LEGAL_TRANSITIONS.get(current, set())

    if new_status not in allowed:
        raise ValueError(
            f"Illegal transition: {current} → {new_status}. "
            f"Allowed from {current}: {allowed}"
        )

    ki = dict(ki)  # shallow copy
    ki["ki_status"] = new_status
    return ki


# ---------------------------------------------------------------------------
# KI Table Generation (Tasks 2.4.1-2.4.2)
# ---------------------------------------------------------------------------

_KI_TABLE_HEADER = "| ID | Issue | Status | Priority | Owner | Impact | Resolution |"
_KI_TABLE_SEPARATOR = "|----|-------|--------|----------|-------|--------|------------|"


def generate_ki_table(kis: list[dict]) -> str:
    """Generate a Markdown KI table from a list of KI dicts.

    Table schema (Task 2.4.2):
    | ID | Issue | Status | Priority | Owner | Impact | Resolution |

    Args:
        kis: List of KI dicts, each with:
            - id: str (e.g. "KI-1")
            - issue: str (one-line description)
            - ki_status: str
            - priority: str (P0-P3)
            - owner: str
            - impact: str
            - resolution: str

    Returns:
        Markdown table string.
    """
    lines = [_KI_TABLE_HEADER, _KI_TABLE_SEPARATOR]

    for ki in kis:
        ki_id = ki.get("id", "?")
        issue = ki.get("issue", ki.get("detail", ""))
        # Truncate issue to one line
        issue = issue.split("\n")[0].strip()
        status = ki.get("ki_status", STATUS_OPEN)
        priority = ki.get("priority", "")
        owner = ki.get("owner", "")
        impact = ki.get("impact", "")
        resolution = ki.get("resolution", "")

        lines.append(f"| {ki_id} | {issue} | {status} | {priority} | {owner} | {impact} | {resolution} |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Strategy KI Table Update (Task 2.4.3)
# ---------------------------------------------------------------------------

def update_strategy_ki_table(strategy_path: str, kis: list[dict]) -> None:
    """Replace the KI table in a strategy file with an updated version.

    Finds the `## Known Issues (Post-Validation)` section and replaces
    the existing table with a new one generated from the provided KIs.

    Args:
        strategy_path: Path to the strategy.md file.
        kis: List of KI dicts for table generation.
    """
    with open(strategy_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_table = generate_ki_table(kis)
    new_section = f"## Known Issues (Post-Validation)\n\n{new_table}"

    # Find and replace the KI section
    # Match from "## Known Issues (Post-Validation)" to next ## heading or EOF
    pattern = re.compile(
        r"## Known Issues \(Post-Validation\)\n.*?(?=\n## |\Z)",
        re.DOTALL,
    )

    match = pattern.search(content)
    if match:
        content = content[:match.start()] + new_section + content[match.end():]
    else:
        # Append at end of file
        content = content.rstrip() + "\n\n" + new_section + "\n"

    with open(strategy_path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Fix Batch Planning (Tasks 2.5.1-2.5.3)
# ---------------------------------------------------------------------------

def plan_fix_batches(kis: list[dict]) -> list[list[dict]]:
    """Group KIs into priority-based fix batches.

    Returns batches in priority order:
    - Batch 0: All P0 KIs
    - Batch 1: All P1 KIs
    - Batch 2: All P2 KIs (P3 are not batched — cosmetic/skip)

    Each batch counts as 1 iteration. Max 3 iterations (MAX_ITERATIONS).

    Args:
        kis: List of KI dicts, each with 'priority' key.

    Returns:
        List of batches: [[P0_ki, ...], [P1_ki, ...], [P2_ki, ...]]
        Empty batches are excluded.
    """
    batches: dict[str, list[dict]] = {
        PRIORITY_P0: [],
        PRIORITY_P1: [],
        PRIORITY_P2: [],
    }

    for ki in kis:
        priority = ki.get("priority", "")
        if priority in batches:
            batches[priority].append(ki)

    # Return non-empty batches, limited to MAX_ITERATIONS
    result = [batch for batch in [batches[PRIORITY_P0], batches[PRIORITY_P1], batches[PRIORITY_P2]] if batch]
    return result[:MAX_ITERATIONS]


# ---------------------------------------------------------------------------
# Convenience: Full KI lifecycle pipeline
# ---------------------------------------------------------------------------

def run_ki_lifecycle(
    failures: list[dict],
    owner_overrides: Optional[dict[str, str]] = None,
) -> list[dict]:
    """Run the full KI lifecycle: classify → prioritize → batch.

    This is the main entry point for Phase 3 of the explore workflow.

    Args:
        failures: List of self-check failure dicts (status="fail").
        owner_overrides: Optional mapping of check_id → owner domain
            for explicit overrides (Task 2.1.4).

    Returns:
        List of enriched KI dicts with owner, priority, ki_status.
    """
    owner_overrides = owner_overrides or {}
    kis = []

    for i, failure in enumerate(failures, 1):
        override = owner_overrides.get(failure.get("check"))
        ki = classify_ki(failure, override_owner=override)
        ki["priority"] = assign_priority(ki)
        ki["id"] = f"KI-{i}"
        kis.append(ki)

    return kis
