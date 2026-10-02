"""ProbeChain — sequentially attempt engines until one succeeds.

Engine order: scrapling-get → obscura-fetch → cloakbrowser-fetch → chrome-devtools-mcp
Records per engine: {engine, status, http_status, error_type, page_title, content_length}
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from scripts.lib.content_admission import classify_html

ENGINES = [
    "scrapling-get",
    "obscura-fetch",
    "cloakbrowser-fetch",
    "chrome-devtools-mcp",
]


def _build_success(engine, html, output_path, http_status=None):
    admission = classify_html(html, http_status)
    return {
        "engine": engine,
        "status": "success" if admission["admitted"] else "failure",
        "admission": admission,
        "stage": "admission",
        "executed": True,
        "process_exit": 0,
        "error_type": admission["protection_type"] or admission["reason"],
        "http_status": http_status,
        "page_title": _extract_title(html),
        "content_length": len(html) if html else 0,
        "output_path": output_path,
    }


def _build_failure(engine, stderr, http_status=None, stdout="", process_exit=None):
    detail = stderr[:500] or stdout[:500]
    return {
        "engine": engine,
        "status": "failure",
        "process_exit": process_exit,
        "http_status": http_status,
        "error_type": _classify_error(stderr, http_status),
        "detail": detail,
        "stage": "process",
        "executed": True,
    }


def _capture_html(command, output_path, repo_root, stdout_html=False):
    """Only promote the current process's output, never a previous run's file."""
    with tempfile.TemporaryDirectory(prefix='chrome-agent-probe-') as directory:
        temporary = os.path.join(directory, 'page.html')
        command = [temporary if arg == output_path else arg for arg in command]
        try:
            result = subprocess.run(command, capture_output=True, text=True, cwd=repo_root, timeout=120)
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(command, 1, "", "timeout")
        except OSError:
            return subprocess.CompletedProcess(command, 1, '', 'engine_unavailable')
        Path(output_path + ".stderr.txt").write_text(result.stderr or "", encoding="utf-8")
        if result.returncode == 0:
            if stdout_html and result.stdout.strip():
                Path(temporary).write_text(result.stdout, encoding="utf-8")
            if not os.path.isfile(temporary):
                result.output_error = 'missing_output'
                return result
            Path(output_path).write_bytes(Path(temporary).read_bytes())
        return result


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
    result = _capture_html([cli, "extract", "get", url, output_path], output_path, repo_root)

    if getattr(result, 'output_error', None):
        return _build_failure("scrapling-get", result.output_error, process_exit=result.returncode)
    if result.returncode == 0 and os.path.exists(output_path):
        html = _read_html(output_path)
        return _build_success("scrapling-get", html, output_path)

    stderr = result.stderr.strip()
    http_status = _extract_http_status(stderr)
    return _build_failure("scrapling-get", stderr, http_status, process_exit=result.returncode)


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
    result = _capture_html([cli, "fetch", url, "--dump", "html", "--quiet"], output_path, repo_root, stdout_html=True)

    if getattr(result, 'output_error', None):
        return _build_failure("obscura-fetch", result.output_error, process_exit=result.returncode)
    if result.returncode == 0 and os.path.exists(output_path):
        html = _read_html(output_path)
        return _build_success("obscura-fetch", html, output_path)

    stderr = result.stderr.strip()
    http_status = _extract_http_status(stderr)
    return _build_failure("obscura-fetch", stderr, http_status, process_exit=result.returncode)


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

    preflight = _cloakbrowser_preflight(repo_root)
    if not preflight["ok"]:
        return {"engine": "cloakbrowser-fetch", "status": "failure", "stage": "preflight",
                "error_type": "preflight_failed", "process_exit": preflight.get("process_exit"),
                "detail": preflight["detail"][:500]}
    try:
        result = subprocess.run(
            [preflight["path"], script, url, "--json"],
            capture_output=True, text=True, cwd=repo_root, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return _build_failure("cloakbrowser-fetch", "timeout")
    except OSError as exc:
        return _build_failure("cloakbrowser-fetch", "engine_unavailable", stdout=str(exc))
    Path(output_path + ".stderr.txt").write_text(result.stderr or "", encoding="utf-8")

    try:
        parsed = json.loads(result.stdout)
        if not isinstance(parsed, dict) or not isinstance(parsed.get("success"), bool):
            raise ValueError("Missing boolean success field")
        if parsed["success"] and not isinstance(parsed.get("html"), str):
            raise ValueError("Missing HTML string")
    except (ValueError, TypeError):
        return _build_failure("cloakbrowser-fetch", "invalid_response", stdout=result.stdout, process_exit=result.returncode)
    if parsed["success"] and result.returncode == 0:
        html = parsed["html"]
        Path(output_path).write_text(html, encoding="utf-8")
        return _build_success("cloakbrowser-fetch", html, output_path, parsed.get("http_status"))

    stderr = result.stderr.strip()
    error = parsed.get("error") or {}
    if not stderr:
        stderr = str(error.get("message") or error.get("category") or "") if isinstance(error, dict) else str(error)
    http_status = parsed.get("http_status")
    return _build_failure("cloakbrowser-fetch", stderr, http_status, result.stdout, result.returncode)


def _run_chrome_devtools_mcp(repo_root: str, url: str, output_path: str) -> dict:
    """chrome-devtools-mcp is handled by the Node.js CLI layer as a fallback.
    This Python module records it as pending fallback.
    """
    return {
        "engine": "chrome-devtools-mcp",
        "status": "pending",
        "error_type": "cli_fallback_required",
        "detail": "Not executed. Requires explicit browser authorization before manual fallback.",
    }


def _cloakbrowser_preflight(repo_root: str) -> dict:
    try:
        result = subprocess.run(["bash", "./scripts/cloakbrowser-cli.sh", "preflight"],
                                cwd=repo_root, capture_output=True, text=True, timeout=180)
        fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        executable = fields.get("RESOLVED_CLI_PATH", "").strip()
        ok = (result.returncode == 0 and fields.get("STATUS") in ("available", "repaired")
              and os.path.isabs(executable) and os.path.isfile(executable) and os.access(executable, os.X_OK))
        return {"ok": ok, "path": executable, "process_exit": result.returncode,
                "detail": (result.stderr or result.stdout or "Invalid CloakBrowser preflight output")[:500]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "path": None, "detail": str(exc)[:500]}


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
    if "unexpected argument" in s or "unrecognized arguments" in s:
        return "invalid_invocation"
    if s in ("missing_output", "engine_unavailable", "invalid_response", "internal_error"):
        return s
    if "just a moment" in s:
        return "cloudflare-managed"
    if "turnstile" in s or "cf-turnstile" in s:
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
    os.makedirs(run_dir, exist_ok=True)
    results = []
    success_engine = None
    html_path = None
    html_content = None

    for engine in ENGINES:
        output_path = os.path.join(run_dir, f"probe_{engine.replace('-', '_')}.html")

        try:
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
        except Exception as exc:
            res = _build_failure(engine, "internal_error", stdout=str(exc))


        if res.get("status") == "success":
            res = _build_success(engine, _read_html(res.get("output_path", "")), res.get("output_path"), res.get("http_status"))
        res.setdefault("stage", "pending" if res.get("status") == "pending" else "preflight" if res.get("error_type") == "preflight_failed" else "process")
        res.setdefault("executed", res.get("status") != "pending")
        res.setdefault("process_exit", None)
        stderr_path = output_path + ".stderr.txt"
        if os.path.isfile(stderr_path):
            res["stderr_path"] = stderr_path
        res["diagnostic_path"] = output_path + ".attempt.json"
        Path(res["diagnostic_path"]).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append(res)

        if res.get("status") == "success":
            success_engine = engine
            html_path = res.get("output_path")
            html_content = _read_html(html_path)
            break

    diagnostic_path = os.path.join(run_dir, "probe-chain.json")
    Path(diagnostic_path).write_text(json.dumps({"results": results, "success_engine": success_engine}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "diagnostic_path": diagnostic_path,
        "results": results,
        "success_engine": success_engine,
        "html_path": html_path,
        "html_content": html_content,
    }
