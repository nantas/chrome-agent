"""Pipeline state management — checkpoint/resume support.

Maintains a ``.pipeline_state.json`` file in the output directory to track
which pages have been successfully extracted, enabling resume after interruption.
"""

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("mediawiki-api-extract")


STATE_FILENAME = ".pipeline_state.json"


def load_state(output_dir: str) -> dict:
    """Load pipeline state from the output directory.

    Args:
        output_dir: Pipeline output directory.

    Returns:
        State dict with keys:
            - ``phase``: Current pipeline phase.
            - ``completed_pages``: List of completed page titles.
            - ``total_pages``: Total page count from manifest.
            - ``last_updated``: ISO 8601 timestamp.
            - ``run_id``: Unique run identifier.
        If no state file exists, returns a default empty state.
    """
    state_path = os.path.join(output_dir, STATE_FILENAME)
    if not os.path.exists(state_path):
        return _default_state()

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        log.info("Loaded pipeline state: %d completed pages, phase=%s, run_id=%s",
                 len(state.get("completed_pages", [])),
                 state.get("phase", "unknown"),
                 state.get("run_id", "unknown"))
        return state
    except (json.JSONDecodeError, IOError) as e:
        log.warning("Failed to load state file '%s': %s — starting fresh", state_path, e)
        return _default_state()


def save_state(output_dir: str, state: dict) -> None:
    """Save pipeline state to the output directory using atomic write.

    Writes to a temporary file first, then renames to ensure atomicity.

    Args:
        output_dir: Pipeline output directory.
        state: State dict to persist.
    """
    state_path = os.path.join(output_dir, STATE_FILENAME)
    os.makedirs(output_dir, exist_ok=True)

    # Update timestamp
    state["last_updated"] = datetime.now(timezone.utc).isoformat()

    # Atomic write
    fd, tmp_path = tempfile.mkstemp(dir=output_dir, prefix=".pipeline_state_tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, state_path)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def mark_completed(output_dir: str, page_title: str) -> None:
    """Add a page title to the completed_pages list and persist.

    Loads current state, appends the title, and saves.

    Args:
        output_dir: Pipeline output directory.
        page_title: Title of the completed page.
    """
    state = load_state(output_dir)
    if page_title not in state.get("completed_pages", []):
        state.setdefault("completed_pages", []).append(page_title)
    save_state(output_dir, state)


def initialize_state(output_dir: str, manifest: dict, phase: str = "B") -> dict:
    """Create or reset pipeline state for a new run.

    Args:
        output_dir: Pipeline output directory.
        manifest: Page manifest dict (must have ``pages`` list).
        phase: Starting phase identifier.

    Returns:
        Initialized state dict.
    """
    import uuid
    pages = manifest.get("pages", [])
    state = {
        "phase": phase,
        "completed_pages": [],
        "total_pages": len(pages),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "run_id": str(uuid.uuid4()),
    }
    save_state(output_dir, state)
    log.info("Initialized pipeline state: %d total pages, run_id=%s",
             len(pages), state["run_id"])
    return state


def _default_state() -> dict:
    """Return a default empty state."""
    return {
        "phase": "",
        "completed_pages": [],
        "total_pages": 0,
        "last_updated": "",
        "run_id": "",
    }


def is_page_completed(state: dict, page_title: str, output_dir: str,
                      target_dir: str, target_filename: str) -> bool:
    """Check if a page is already completed and its output file exists.

    A page is considered completed if:
    1. Its title is in ``completed_pages``
    2. The output ``.md`` file exists at the expected path

    Args:
        state: Pipeline state dict.
        page_title: Page title to check.
        output_dir: Output directory root.
        target_dir: Page's target subdirectory.
        target_filename: Page's output filename.

    Returns:
        ``True`` if the page is completed and its file exists.
    """
    if page_title not in state.get("completed_pages", []):
        return False

    # Verify output file exists
    if target_dir:
        filepath = os.path.join(output_dir, target_dir, target_filename)
    else:
        filepath = os.path.join(output_dir, target_filename)

    exists = os.path.exists(filepath)
    if not exists:
        log.info("Page '%s' in completed_pages but output file missing — will re-extract",
                 page_title)
        return False

    return True
