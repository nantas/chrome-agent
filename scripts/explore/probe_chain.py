"""ProbeChain — sequentially attempt engines until one succeeds.

Engine order: scrapling-get → obscura-fetch → cloakbrowser-fetch → chrome-devtools-mcp
Records per engine: {engine, status, http_status, error_type, page_title, content_length}
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

ENGINES = [
    "scrapling-get",
    "obscura-fetch",
    "cloakbrowser-fetch",
    "chrome-devtools-mcp",
]


def _run_scrapling_get(repo_root: str, url: str, output_path: str) -> dict:
    """Run scrapling-get via scrapling CLI."""
    preflight = _scrapling_preflight(repo_root)
    if not preflight.get("ok") or not preflight.get("resolvedCliPath"):
        return {
            "engine": "scrapling-get",
            "status": "failure",
            "error_type": "preflight_failed",
            "detail": preflight.get("stderr", "Scrapling CLI not available"),
        }

    cli = preflight["resolvedCliPath"]
    result = subprocess.run(
        [cli, "extract", "get", url, output_path],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    if result.returncode == 0 and os.path.exists(output_path):
        html = _read_html(output_path)
        return {
            "engine": "scrapling-get",
            "status": "success",
            "http_status": 200,
            "page_title": _extract_title(html),
            "content_length": len(html) if html else 0,
            "output_path": output_path,
        }

    stderr = result.stderr.strip()
    http_status = _extract_http_status(stderr)
    return {
        "engine": "scrapling-get",
        "status": "failure",
        "http_status": http_status,
        "error_type": _classify_error(stderr, http_status),
        "detail": stderr[:500],
    }


def _run_obscura_fetch(repo_root: str, url: str, output_path: str) -> dict:
    """Run obscura-fetch via Obscura CLI."""
    preflight = _obscura_preflight(repo_root)
    if not preflight.get("ok") or not preflight.get("path"):
        return {
            "engine": "obscura-fetch",
            "status": "failure",
            "error_type": "preflight_failed",
            "detail": "Obscura CLI not available",
        }

    cli = preflight["path"]
    result = subprocess.run(
        [cli, "fetch", url, "--dump", "html", "--quiet", "--output", output_path],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    if result.returncode == 0 and os.path.exists(output_path):
        html = _read_html(output_path)
        return {
            "engine": "obscura-fetch",
            "status": "success",
            "http_status": 200,
            "page_title": _extract_title(html),
            "content_length": len(html) if html else 0,
            "output_path": output_path,
        }

    stderr = result.stderr.strip()
    http_status = _extract_http_status(stderr)
    return {
        "engine": "obscura-fetch",
        "status": "failure",
        "http_status": http_status,
        "error_type": _classify_error(stderr, http_status),
        "detail": stderr[:500],
    }


def _run_cloakbrowser_fetch(repo_root: str, url: str, output_path: str) -> dict:
    """Run cloakbrowser-fetch via Python script."""
    script = os.path.join(repo_root, "scripts", "cloakbrowser_fetcher.py")
    if not os.path.exists(script):
        return {
            "engine": "cloakbrowser-fetch",
            "status": "failure",
            "error_type": "preflight_failed",
            "detail": "cloakbrowser_fetcher.py not found",
        }

    result = subprocess.run(
        ["python3", script, url, "--output", output_path, "--json"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    try:
        parsed = json.loads(result.stdout)
        if parsed.get("ok"):
            html = _read_html(output_path)
            return {
                "engine": "cloakbrowser-fetch",
                "status": "success",
                "http_status": 200,
                "page_title": _extract_title(html),
                "content_length": len(html) if html else 0,
                "output_path": output_path,
            }
    except json.JSONDecodeError:
        pass

    stderr = result.stderr.strip()
    http_status = _extract_http_status(stderr)
    return {
        "engine": "cloakbrowser-fetch",
        "status": "failure",
        "http_status": http_status,
        "error_type": _classify_error(stderr, http_status),
        "detail": stderr[:500] or result.stdout[:500],
    }


def _run_chrome_devtools_mcp(repo_root: str, url: str, output_path: str) -> dict:
    """chrome-devtools-mcp is handled by the Node.js CLI layer as a fallback.
    This Python module records it as pending fallback.
    """
    return {
        "engine": "chrome-devtools-mcp",
        "status": "pending",
        "error_type": "cli_fallback_required",
        "detail": "Requires Node.js MCP gateway; handled by CLI layer if earlier engines fail.",
    }


def _scrapling_preflight(repo_root: str) -> dict:
    result = subprocess.run(
        ["./scripts/scrapling-cli.sh", "preflight", "--no-install"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    status_map = {}
    for line in (result.stdout + result.stderr).split("\n"):
        m = re.match(r"^([A-Z_]+)=(.*)$", line)
        if m:
            status_map[m.group(1)] = m.group(2)
    return {
        "ok": result.returncode == 0,
        "status": status_map.get("STATUS"),
        "resolvedCliPath": status_map.get("RESOLVED_CLI_PATH"),
        "source": status_map.get("SOURCE"),
        "stderr": result.stderr,
    }


def _obscura_preflight(repo_root: str) -> dict:
    managed_dir = Path.home() / ".cache" / "chrome-agent-obscura" / "bin"
    managed_bin = managed_dir / "obscura"
    env_path = os.environ.get("OBSCURA_CLI_PATH")

    for candidate, source in [(env_path, "env"), (str(managed_bin), "managed")]:
        if candidate and os.path.exists(candidate):
            v = subprocess.run([candidate, "--help"], capture_output=True, text=True)
            if v.returncode == 0:
                return {"ok": True, "path": candidate, "source": source}

    install_script = os.path.join(repo_root, "scripts", "obscura-cli-preflight.sh")
    if os.path.exists(install_script):
        install = subprocess.run(["bash", install_script], capture_output=True, text=True, cwd=repo_root)
        if install.returncode == 0 and managed_bin.exists():
            v = subprocess.run([str(managed_bin), "--help"], capture_output=True, text=True)
            if v.returncode == 0:
                return {"ok": True, "path": str(managed_bin), "source": "installed"}

    return {"ok": False, "path": None}


def _read_html(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _extract_title(html: Optional[str]) -> Optional[str]:
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    return title_tag.get_text(strip=True) if title_tag else None


def _extract_http_status(text: str) -> Optional[int]:
    m = re.search(r"\b(4\d{2}|5\d{2}|3\d{2}|200)\b", text)
    if m:
        return int(m.group(1))
    return None


def _classify_error(stderr: str, http_status: Optional[int]) -> str:
    s = stderr.lower()
    if http_status == 403 or "just a moment" in s:
        return "cloudflare-managed"
    if http_status == 403 or "turnstile" in s or "cf-turnstile" in s:
        return "cloudflare-turnstile"
    if http_status == 429 or "rate limit" in s or "too many requests" in s:
        return "rate-limit"
    if "login" in s or "unauthorized" in s or http_status == 401:
        return "login-wall"
    if "timeout" in s or "timed out" in s:
        return "timeout"
    return "unknown"


def probe(repo_root: str, url: str, run_dir: str) -> dict:
    """Run the full probe chain.

    Returns:
        {
            "results": [engine_results...],
            "success_engine": engine_name or None,
            "html_path": path to fetched HTML or None,
            "html_content": raw HTML or None,
        }
    """
    results = []
    success_engine = None
    html_path = None
    html_content = None

    for engine in ENGINES:
        output_path = os.path.join(run_dir, f"probe_{engine.replace('-', '_')}.html")

        if engine == "scrapling-get":
            res = _run_scrapling_get(repo_root, url, output_path)
        elif engine == "obscura-fetch":
            res = _run_obscura_fetch(repo_root, url, output_path)
        elif engine == "cloakbrowser-fetch":
            res = _run_cloakbrowser_fetch(repo_root, url, output_path)
        elif engine == "chrome-devtools-mcp":
            res = _run_chrome_devtools_mcp(repo_root, url, output_path)
        else:
            continue

        results.append(res)

        if res.get("status") == "success":
            success_engine = engine
            html_path = res.get("output_path")
            html_content = _read_html(html_path)
            break

    return {
        "results": results,
        "success_engine": success_engine,
        "html_path": html_path,
        "html_content": html_content,
    }
