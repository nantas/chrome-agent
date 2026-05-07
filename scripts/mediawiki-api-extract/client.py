"""Low-level MediaWiki API client with retry logic."""

import json
import logging
import time
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    raise ImportError("'requests' package is required. Install with: pip install requests")

log = logging.getLogger("mediawiki-api-extract")


class ApiClient:
    """Low-level MediaWiki API client with retry logic."""

    def __init__(self, base_url: str, timeout: int = 5, max_retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "chrome-agent/mediawiki-api-extract"})

    def _request(self, params: dict) -> dict:
        """Make an API request with exponential backoff retry."""
        url = f"{self.base_url}?{urlencode(params)}"
        delay = 1.0
        last_error = None
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 429:
                    last_error = f"HTTP 429 rate limited (attempt {attempt + 1})"
                    time.sleep(delay + (attempt * 0.1))  # jitter
                    delay *= 2
                    continue
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    raise RuntimeError(f"API error: {data['error']}")
                return data
            except (requests.RequestException, json.JSONDecodeError) as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
        raise RuntimeError(f"API request failed after {self.max_retries} retries: {last_error}")

    def query(self, **params) -> dict:
        """action=query request."""
        p = {"action": "query", "format": "json", **params}
        return self._request(p)

    def parse(self, page: str, prop: str = "wikitext") -> dict:
        """action=parse request."""
        p = {"action": "parse", "page": page, "prop": prop, "format": "json"}
        return self._request(p)


def probe_api_endpoint(origin: str, strategy_base_url: str | None = None) -> str | None:
    """Probe candidate API endpoints. Returns working base URL or None."""
    candidates = []
    if strategy_base_url:
        candidates.append(strategy_base_url)
    candidates.extend([
        f"{origin}/api.php",
        f"{origin}/w/api.php",
    ])

    for candidate in candidates:
        try:
            url = f"{candidate}?action=query&meta=siteinfo&format=json"
            resp = requests.get(url, timeout=5, headers={"User-Agent": "chrome-agent/mediawiki-api-extract"})
            if resp.status_code == 200:
                data = resp.json()
                if "query" in data:
                    log.info("API endpoint resolved: %s", candidate)
                    return candidate
        except (requests.RequestException, json.JSONDecodeError):
            continue
    return None
