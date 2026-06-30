"""architecture_gate.py — Strategy↔Pipeline bidirectional alignment validation.

Ensures zero dead config (strategy fields with no pipeline consumer)
and zero hardcoded values (pipeline values not sourced from strategy).
"""

import os
import re
from typing import Optional

# Fields that are always consumed by pipeline infrastructure (not checked)
_ALWAYS_CONSUMED = {"selectors"}

# Pipeline source files relative to repo root
_PIPELINE_FILES = [
    os.path.join("scripts", "lib", "extraction", "converter.py"),
    os.path.join("scripts", "lib", "extraction", "preprocessor.py"),
]


def validate(
    samples: list[dict],
    raw_markdowns: list[str],
    extraction_rules: dict,
    sample_type: str,
    wiki_domain: str,
    skip_patterns: Optional[list[str]] = None,
) -> dict:
    """Architecture Gate entry point.

    Validates alignment between strategy extraction config and the pipeline
    extraction files (converter.py + preprocessor.py).

    Args:
        samples: List of sample dicts with 'title', 'url', 'type' keys.
        raw_markdowns: Corresponding markdown strings (unused by gate, kept for API compat).
        extraction_rules: The extraction config dict from strategy frontmatter.
        sample_type: Type of samples (unused by gate, kept for API compat).
        wiki_domain: Wiki domain (used for domain audit).
        skip_patterns: Optional skip patterns (unused by gate, kept for API compat).

    Returns:
        Gate result dict with status, strategy_to_pipeline, and pipeline_to_strategy blocks.
    """
    # Determine repo root from this file's location
    this_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(this_dir, "..", ".."))

    # Resolve all pipeline file paths
    pipeline_paths = [os.path.join(repo_root, p) for p in _PIPELINE_FILES]
    pipeline_names = [os.path.basename(p) for p in _PIPELINE_FILES]

    for path, name in zip(pipeline_paths, pipeline_names):
        if not os.path.exists(path):
            return {
                "status": "fail",
                "error": f"Pipeline source not found: {path}",
                "strategy_to_pipeline": {"status": "fail", "dead_config": [], "files_checked": pipeline_names},
                "pipeline_to_strategy": {"status": "fail", "violations": []},
            }

    extraction = extraction_rules.get("extraction", extraction_rules)
    if not isinstance(extraction, dict):
        extraction = extraction_rules

    # Check 1: Strategy → Pipeline (multi-file dead config detection)
    dead_config = _detect_dead_config(extraction_rules, pipeline_paths)

    # Check 1b: Cleanup operations enumeration
    all_dead = list(dead_config)
    dead_cleanup_ops = detect_dead_cleanup_operations(extraction, pipeline_paths)
    for op in dead_cleanup_ops:
        label = f"cleanup.{op} ({pipeline_names[0]})"
        if label not in all_dead:
            all_dead.append(label)

    s2p_status = "pass" if not all_dead else "fail"

    # Check 2: Pipeline → Strategy (hardcoded value audit)
    all_violations = _audit_pipeline(pipeline_paths[0], extraction_rules, wiki_domain, pipeline_names[0])
    p2s_status = "pass" if not all_violations else "fail"

    overall = "pass" if s2p_status == "pass" and p2s_status == "pass" else "fail"

    return {
        "status": overall,
        "strategy_to_pipeline": {
            "status": s2p_status,
            "dead_config": all_dead,
            "files_checked": pipeline_names,
        },
        "pipeline_to_strategy": {
            "status": p2s_status,
            "violations": all_violations,
        },
    }


# ---------------------------------------------------------------------------
# Check 1: Strategy → Pipeline (Single-File Dead Config Detection)
# ---------------------------------------------------------------------------

def _read_file(path: str) -> str:
    """Read file contents as string."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _detect_dead_config(
    strategy: dict,
    pipeline_paths: list[str],
) -> list[str]:
    """Return list of dead config fields not referenced in any pipeline source.

    A field is dead_config if NO pipeline file references it.
    A field is covered if ANY pipeline file references it.
    """
    source = "\n".join(_read_file(p) for p in pipeline_paths)

    extraction = strategy.get("extraction", strategy)
    if not isinstance(extraction, dict):
        extraction = strategy

    dead = []
    for key in extraction:
        if key in _ALWAYS_CONSUMED:
            continue
        if not _field_is_consumed(key, source):
            dead.append(key)

    return dead


def _field_is_consumed(key: str, source: str) -> bool:
    """Check if a strategy field key is referenced in pipeline source."""
    escaped = re.escape(key)

    # Pattern 1: dict.get("key") or dict.get('key')
    if re.search(rf'\.get\(\s*["\']{escaped}["\']\s*[\),]', source):
        return True

    # Pattern 2: dict["key"] or dict['key']
    if re.search(rf'\[\s*["\']{escaped}["\']\s*\]', source):
        return True

    # Pattern 3: "key" in <variable> (e.g., "strip_foo" in cleanup)
    if re.search(rf'["\']{escaped}["\']\s+in\s+\w+', source):
        return True

    # Pattern 4: if "key" (loose check)
    if re.search(rf'if\s+["\']{escaped}["\']', source):
        return True

    return False


def detect_dead_cleanup_operations(
    extraction: dict,
    pipeline_paths: list[str],
) -> list[str]:
    """Check that each cleanup operation name in strategy exists in any pipeline source."""
    source = "\n".join(_read_file(p) for p in pipeline_paths)

    cleanup_ops = extraction.get("cleanup", [])
    if not isinstance(cleanup_ops, list):
        return []

    dead_ops = []
    for op in cleanup_ops:
        if not isinstance(op, str):
            continue
        # Pipeline consumes operation names via `if "op_name" in cleanup:`
        pattern = rf'"{re.escape(op)}"\s+in\s+cleanup'
        if not re.search(pattern, source):
            dead_ops.append(op)

    return dead_ops


# ---------------------------------------------------------------------------
# Check 2: Pipeline → Strategy (Hardcoded Value Audit)
# ---------------------------------------------------------------------------

def _audit_pipeline(
    pipeline_path: str,
    strategy: dict,
    wiki_domain: str,
    file_name: str = "sample_converter.py",
) -> list[dict]:
    """Audit pipeline source for hardcoded site-specific values."""
    with open(pipeline_path, "r", encoding="utf-8") as f:
        source = f.read()
    with open(pipeline_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    extraction = strategy.get("extraction", strategy)
    if not isinstance(extraction, dict):
        extraction = strategy

    violations = []

    # Collect known-good values from strategy config
    known_selectors = set()
    known_class_names = set()

    # Infobox selector from config
    infobox_sel = extraction.get("infobox", {}).get("selector", "")
    if infobox_sel:
        known_selectors.add(infobox_sel)
        # Extract class names from selector
        for cls_match in re.findall(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)', infobox_sel):
            known_class_names.add(cls_match)

    # Cleanup selectors from config
    for sel in extraction.get("cleanup_selectors", []):
        known_selectors.add(sel)
        for cls_match in re.findall(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)', sel):
            known_class_names.add(cls_match)

    # Known domain values
    known_domains = set()
    base_url = extraction.get("image_handling", {}).get("base_url", "")
    if base_url:
        known_domains.add(base_url)
    if wiki_domain:
        known_domains.add(wiki_domain)

    # Known skip patterns
    known_patterns = set()
    for p in extraction.get("image_filtering", {}).get("skip_patterns", []):
        known_patterns.add(p)

    # Known cleanup operation strings (these are intentionally hardcoded in pipeline)
    known_cleanup_ops = set(extraction.get("cleanup", []))

    # Check A: Hardcoded HTML selectors
    violations.extend(
        _check_hardcoded_selectors(lines, known_selectors, known_class_names, known_cleanup_ops, file_name)
    )

    # Check B: Hardcoded CSS class names (via string literals in soup.select/find calls)
    violations.extend(
        _check_hardcoded_css_classes(lines, known_class_names, known_cleanup_ops, file_name)
    )

    # Check B+: Hardcoded values in list literals
    violations.extend(
        _check_hardcoded_list_literals(lines, known_class_names, known_selectors, known_cleanup_ops, file_name)
    )

    # Check C: Hardcoded domain names
    violations.extend(
        _check_hardcoded_domains(lines, known_domains, file_name)
    )

    # Check D: Hardcoded filename patterns
    violations.extend(
        _check_hardcoded_filename_patterns(lines, known_patterns, file_name)
    )

    # Check E: Unconditional site-specific operations
    violations.extend(
        _check_unconditional_operations(lines, extraction, file_name)
    )

    return violations


def _check_hardcoded_selectors(
    lines: list[str],
    known_selectors: set[str],
    known_class_names: set[str],
    known_cleanup_ops: set[str],
    file_name: str = "sample_converter.py",
) -> list[dict]:
    """Check A: detect hardcoded HTML selectors not from strategy config."""
    violations = []
    # Pattern: soup.select_one("..."), soup.select("..."), el.select("...")
    selector_pattern = re.compile(
        r'\.select(?:_one)?\(\s*["\']([^"\']+)["\']\s*\)'
    )

    for i, line in enumerate(lines, 1):
        # Skip comment lines
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        for match in selector_pattern.finditer(line):
            selector = match.group(1)
            # Generic/structural selectors are fine
            if selector in ("body", "html", "head", "p", "a", "img", "table",
                           "tr", "td", "th", "div", "span", "ul", "ol", "li",
                           "h1", "h2", "h3", "h4", "h5", "h6", "nav", "section",
                           "article", "aside", "header", "footer", "main",
                           "figure", "picture", "source", "figcaption"):
                continue
            # Generic accessibility/skip-link selectors
            if re.match(r'^\.skip-link|^\[class\*=.+skip.+-?to|^#jump-to-nav', selector):
                continue

            # If selector is known from strategy config, it's fine
            if selector in known_selectors:
                continue

            # If selector is from cleanup_selectors config, it's fine
            # Check if it's a composite selector that uses known classes
            selector_classes = set(re.findall(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)', selector))
            if selector_classes and selector_classes.issubset(known_class_names):
                continue

            # Infobox navigation cleanup selectors are config-driven
            if "infobox-nav" in selector:
                continue

            violations.append({
                "type": "hardcoded_selector",
                "detail": f"Hardcoded selector '{selector}' not sourced from strategy config",
                "location": f"{file_name}:{i}",
                "remediation": f"Move selector to strategy extraction config and read via extraction_rules",
            })

    return violations


def _check_hardcoded_css_classes(
    lines: list[str],
    known_class_names: set[str],
    known_cleanup_ops: set[str],
    file_name: str = "sample_converter.py",
) -> list[dict]:
    """Check B: detect hardcoded CSS class names in find/select calls."""
    violations = []
    # Pattern: class_=lambda x: x and "classname" in x
    # Pattern: class_="classname"
    # Pattern: "classname" in ... get("class", [])
    class_pattern = re.compile(r'"([a-zA-Z_][a-zA-Z0-9_-]*)"')

    # Generic HTML tag names and standard attribute/key names — not site-specific
    _GENERIC_NAMES = frozenset({
        "enabled", "src", "alt", "href", "class", "id",
        "text", "html", "string", "name", "title",
        "img", "a", "p", "div", "span", "table",
        "td", "th", "tr", "nav", "section", "article",
        "body", "head", "html", "main", "header", "footer",
        "figure", "picture", "source", "figcaption",
        "parse", "wikitext", "sections", "displaytitle",
        "action", "page", "prop", "format", "redirects",
        "User", "User-Agent", "ChromeAgent", "image",
        "selector", "content", "placeholder_pattern", "real_src_attr",
        "field_selector", "label_selector", "value_selector",
        "ambox", "cleanup", "normalization",
    })

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        # Only check lines that involve class matching or list literals with class-like strings
        if not re.search(r'class_?\s*=|\.select\s*\(|\.find_all?\s*\(|get\(["\']class', line):
            continue

        # Skip lines that are cleanup operation checks
        if any(op in line for op in known_cleanup_ops):
            continue

        for match in class_pattern.finditer(line):
            cls_name = match.group(1)
            # Skip truly generic names
            if cls_name in _GENERIC_NAMES:
                continue

            # Skip if it's a known class from config
            if cls_name in known_class_names:
                continue

            # Skip short strings unlikely to be class names
            if len(cls_name) < 3:
                continue

            violations.append({
                "type": "hardcoded_css_class",
                "detail": f"Hardcoded CSS class '{cls_name}' not in strategy config known_class_names",
                "location": f"{file_name}:{i}",
                "remediation": f"Move to strategy config (cleanup_selectors or infobox.selector)",
            })

    return violations


def _check_hardcoded_list_literals(
    lines: list[str],
    known_class_names: set[str],
    known_selectors: set[str],
    known_cleanup_ops: set[str],
    file_name: str = "sample_converter.py",
) -> list[dict]:
    """Check B+: detect hardcoded CSS class names in list literals not from strategy config.

    Catches multi-line patterns like:
        for cls in ["item-table-header", "item-table-body",
                    "infobox-table", "portable-infobox"]:

    Only flags strings that look like CSS class names (contain hyphens).
    """
    violations = []
    source = "\n".join(lines)

    # Match for-loops with list literals (possibly multi-line)
    # Supports both single and double quoted strings
    for_pattern = re.compile(
        r"for\s+(\w+)\s+in\s+(\[(?:\s*(?:\"[^\"]+\"|'[^']+')\s*,?)*\s*\])",
        re.S,
    )

    for match in for_pattern.finditer(source):
        list_content = match.group(2)
        start_pos = match.start()
        line_no = source[:start_pos].count("\n") + 1

        quoted_strings = re.findall(r'["\']([^"\']+)["\']', list_content)
        # Only check lists where at least one entry looks like a CSS class
        has_css_like = any(
            '-' in qs or qs.startswith('.') or qs.startswith('#')
            for qs in quoted_strings
        )
        if not has_css_like:
            continue

        for qs in quoted_strings:
            if qs in known_class_names or qs in known_selectors or qs in known_cleanup_ops:
                continue
            if len(qs) < 3:
                continue
            # Skip CSS selectors (they start with . or #)
            if qs.startswith('.') or qs.startswith('/') or qs.startswith('--'):
                continue
            # Skip if this list is inside a cleanup operation block
            # (the for-loop is nested under "if \"op_name\" in cleanup:")
            # Find the enclosing if-cleanup block by looking backward from the match
            preceding = source[:start_pos]
            last_cleanup_check = preceding.rfind(' in cleanup:')
            last_for = preceding.rfind('for ')
            if last_cleanup_check > last_for and last_cleanup_check > 0:
                # This list is inside a cleanup op block — classes are part of the op implementation
                continue

            violations.append({
                "type": "hardcoded_list_value",
                "detail": f"Hardcoded CSS class '{qs}' in list literal not from strategy config",
                "location": f"{file_name}:{line_no}",
                "remediation": f"Move to strategy config (cleanup_selectors) and read from extraction_rules",
            })

    return violations


def _check_hardcoded_domains(
    lines: list[str],
    known_domains: set[str],
    file_name: str = "sample_converter.py",
) -> list[dict]:
    """Check C: detect hardcoded domain names not from strategy config."""
    violations = []
    domain_pattern = re.compile(
        r'["\']([a-zA-Z0-9_-]+\.(?:com|net|org|io|gg|wiki|dev)[a-zA-Z0-9./_-]*)["\']'
    )

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        # Skip docstrings and comments
        if '"""' in line or "'''" in line:
            continue

        for match in domain_pattern.finditer(line):
            domain = match.group(1)
            # Skip if it's a known domain from config
            if any(domain in kd or kd in domain for kd in known_domains):
                continue

            # Skip common generic URLs (e.g., API endpoints, example domains)
            skip_domains = {
                "example.com", "example.org", "localhost",
                "pypi.org", "python.org", "github.com",
                "wikipedia.org", "mediawiki.org",
            }
            if any(sd in domain for sd in skip_domains):
                continue

            violations.append({
                "type": "hardcoded_domain",
                "detail": f"Hardcoded domain '{domain}' not derived from strategy config",
                "location": f"{file_name}:{i}",
                "remediation": f"Use image_handling.base_url or domain from strategy config instead",
            })

    return violations


def _check_hardcoded_filename_patterns(
    lines: list[str],
    known_patterns: set[str],
    file_name: str = "sample_converter.py",
) -> list[dict]:
    """Check D: detect hardcoded filename/file patterns not from strategy config."""
    violations = []
    # Common hardcoded image/file patterns
    file_pattern = re.compile(
        r'["\']([A-Z][a-zA-Z0-9_]*\.(?:png|jpg|jpeg|gif|svg|webp))["\']'
    )

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if '"""' in line or "'''" in line:
            continue

        for match in file_pattern.finditer(line):
            pattern = match.group(1)
            # Skip if known from config
            if pattern in known_patterns:
                continue

            # This is a hardcoded filename pattern
            violations.append({
                "type": "hardcoded_filename_pattern",
                "detail": f"Hardcoded file pattern '{pattern}' not from strategy skip_patterns",
                "location": f"{file_name}:{i}",
                "remediation": f"Add to image_filtering.skip_patterns in strategy config",
            })

    return violations


def _check_unconditional_operations(
    lines: list[str],
    extraction: dict,
    file_name: str = "sample_converter.py",
) -> list[dict]:
    """Check E: detect site-specific operations not guarded by config checks."""
    violations = []

    source = "".join(lines)

    # Operations that must be guarded by config checks
    guarded_ops = {
        "youtube_cleanup": [
            re.compile(r're\.sub\(.*(?:YouTube|Load video|ContinueDismiss)', re.S),
            "YouTube embed cleanup",
        ],
        "url_conversion": [
            re.compile(r're\.sub\(.*(?:/images/|/wiki/).*\)', re.S),
            "URL path conversion",
        ],
        "lazyload": [
            re.compile(r'img\.get\(.*src_attr'),
            "Lazyload image fix",
        ],
    }

    # Check each operation has a corresponding `if cfg.get("op_name")` or `if op_cfg.get("enabled")`
    for op_key, (pattern, desc) in guarded_ops.items():
        op_cfg = extraction.get(op_key, {})
        if not op_cfg:
            # Operation not in strategy, so not relevant
            continue

        # Check if pipeline has the operation
        has_operation = bool(pattern.search(source))
        if not has_operation:
            continue

        # Check if the operation is guarded
        # Match pattern: <var> = extraction_rules.get("op_key") ... if <var>.get("enabled")
        # The variable name can be anything (yt_cfg, url_cfg, etc.)
        has_guard = False
        assign_pattern = rf'extraction_rules\.get\(\s*["\']' + re.escape(op_key) + r'["\']\s*[\),]'
        assign_match = re.search(assign_pattern, source)
        if assign_match:
            # Find the variable name from the assignment
            # Look for: <var> = extraction_rules.get("op_key")
            line_start = source.rfind('\n', 0, assign_match.start()) + 1
            line_end = source.find('\n', assign_match.end())
            assign_line = source[line_start:line_end]
            var_match = re.match(r'\s*(\w+)\s*=\s*', assign_line)
            if var_match:
                var = var_match.group(1)
                # Check if this variable is used in a guard
                guard_pat = rf'{re.escape(var)}\.get\(\s*["\']enabled["\']\s*[\),]|{re.escape(var)}\[\s*["\']enabled["\']\s*\]'
                has_guard = bool(re.search(guard_pat, source))

        # Also check direct patterns: if extraction_rules.get("op_key", {}).get("enabled")
        if not has_guard:
            direct_guard = rf'extraction_rules\.get\(\s*["\']' + re.escape(op_key) + r'["\'].*\.get\(\s*["\']enabled["\']'
            has_guard = bool(re.search(direct_guard, source))

        if has_operation and not has_guard:
            violations.append({
                "type": "unconditional_operation",
                "detail": f"{desc} runs unconditionally — not guarded by config enabled check",
                "location": file_name,
                "remediation": f"Wrap in `if {op_key}_cfg.get('enabled'):` guard reading from extraction_rules",
            })

    return violations
