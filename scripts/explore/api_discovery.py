"""ApiDiscovery — probe known API endpoints and record capabilities."""

import json
import urllib.request
from typing import Optional

ENDPOINTS = [
    ("/api.php", "mediawiki"),
    ("/wp-json", "wordpress"),
    ("/graphql", "graphql"),
    ("/sitemap.xml", "sitemap"),
    ("/robots.txt", "robots"),
]


def _fetch_json(url: str, timeout: int = 10) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "chrome-agent-explore/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            return json.loads(data)
    except Exception:
        return None


def _fetch_text(url: str, timeout: int = 10) -> Optional[str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "chrome-agent-explore/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _probe_mediawiki(base_url: str) -> Optional[dict]:
    siteinfo_url = f"{base_url}?action=query&meta=siteinfo&siprop=general|statistics&format=json"
    data = _fetch_json(siteinfo_url)
    if not data or "query" not in data:
        return None

    general = data["query"].get("general", {})
    statistics = data["query"].get("statistics", {})

    return {
        "type": "mediawiki",
        "base_url": base_url,
        "version": general.get("generator", ""),
        "capabilities": [
            "read",
            "parse",
            "query",
        ],
        "site_name": general.get("sitename", ""),
        "lang": general.get("lang", ""),
        "pages": statistics.get("pages"),
        "articles": statistics.get("articles"),
    }


def _probe_wordpress(base_url: str) -> Optional[dict]:
    data = _fetch_json(base_url)
    if not data or "name" not in data:
        return None
    return {
        "type": "wordpress",
        "base_url": base_url,
        "version": data.get("namespaces", [{}])[0].get("_links", {}).get("collection", [{}])[0].get("href", ""),
        "capabilities": ["read"],
        "site_name": data.get("name", ""),
    }


def _probe_graphql(base_url: str) -> Optional[dict]:
    introspection = '{"query": "{ __schema { queryType { name } } }"}'
    try:
        req = urllib.request.Request(
            base_url,
            data=introspection.encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "chrome-agent-explore/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            if data.get("data", {}).get("__schema"):
                return {
                    "type": "graphql",
                    "base_url": base_url,
                    "version": "",
                    "capabilities": ["read"],
                }
    except Exception:
        pass
    return None


def _probe_sitemap(url: str) -> Optional[dict]:
    text = _fetch_text(url)
    if text and "<urlset" in text:
        url_count = text.count("<url>")
        return {
            "type": "sitemap",
            "base_url": url,
            "version": "",
            "capabilities": ["index"],
            "url_count": url_count,
        }
    return None


def _probe_robots(url: str) -> Optional[dict]:
    text = _fetch_text(url)
    if text and "User-agent" in text:
        return {
            "type": "robots",
            "base_url": url,
            "version": "",
            "capabilities": ["crawl_rules"],
        }
    return None


def discover(url: str) -> list[dict]:
    """Probe API endpoints for a given base URL.

    Args:
        url: The target URL (e.g., https://example.com/wiki/Page)

    Returns:
        List of detected API descriptors: {type, base_url, version, capabilities[], ...}
    """
    from urllib.parse import urljoin, urlparse

    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    detected = []
    for path, api_type in ENDPOINTS:
        full_url = urljoin(base, path)

        if api_type == "mediawiki":
            result = _probe_mediawiki(full_url)
        elif api_type == "wordpress":
            result = _probe_wordpress(full_url)
        elif api_type == "graphql":
            result = _probe_graphql(full_url)
        elif api_type == "sitemap":
            result = _probe_sitemap(full_url)
        elif api_type == "robots":
            result = _probe_robots(full_url)
        else:
            continue

        if result:
            detected.append(result)

    return detected
