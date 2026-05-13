"""Low-level MediaWiki API client with retry logic."""

import json
import logging
import random
import time
from typing import Optional
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    raise ImportError("'requests' package is required. Install with: pip install requests")

log = logging.getLogger("mediawiki-api-extract")


class PageNotFoundError(Exception):
    """Raised when the MediaWiki API reports a page does not exist.

    Triggered by error codes: 'missingtitle', 'nosuchpage'.
    These are business-level exceptions that can be safely skipped
    during bulk extraction rather than treated as fatal errors.
    """

    def __init__(self, page_title: str, code: str = "missingtitle"):
        self.page_title = page_title
        self.code = code
        super().__init__(f"Page not found: {page_title} (code={code})")


class ApiClient:
    """Low-level MediaWiki API client with retry logic."""

    def __init__(self, base_url: str, timeout: int = 5, rate_limit_config=None):
        self.base_url = base_url
        self.timeout = timeout
        self.rate_limit_config = rate_limit_config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "chrome-agent/mediawiki-api-extract"})

    def _request(self, params: dict) -> dict:
        """Make an API request with exponential backoff retry."""
        url = f"{self.base_url}?{urlencode(params)}"
        
        # Use rate limit config if available, otherwise fall back to safe defaults
        if self.rate_limit_config:
            max_retries = self.rate_limit_config.max_retries
            initial_delay = self.rate_limit_config.initial_delay_sec
            backoff_multiplier = self.rate_limit_config.backoff_multiplier
            max_delay = self.rate_limit_config.max_delay_sec
            jitter = self.rate_limit_config.jitter
        else:
            max_retries = 5
            initial_delay = 1.0
            backoff_multiplier = 2.0
            max_delay = 60.0
            jitter = True
        
        delay = initial_delay
        last_error = None
        for attempt in range(max_retries):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 429:
                    last_error = f"HTTP 429 rate limited (attempt {attempt + 1})"
                    log.warning("Rate limited (429), waiting %.1fs before retry %d/%d", delay, attempt + 1, max_retries)
                    time.sleep(delay)
                    delay = min(delay * backoff_multiplier, max_delay)
                    if jitter:
                        delay = delay * (1 + random.uniform(-0.2, 0.2))
                    continue
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    error_code = data["error"].get("code", "")
                    if error_code in ("missingtitle", "nosuchpage"):
                        # Extract page title from request params for context
                        page_title = params.get("page", "")
                        raise PageNotFoundError(page_title, error_code)
                    raise RuntimeError(f"API error: {data['error']}")
                return data
            except (requests.RequestException, json.JSONDecodeError) as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    log.warning("Request failed (%s), waiting %.1fs before retry %d/%d", last_error, delay, attempt + 1, max_retries)
                    time.sleep(delay)
                    delay = min(delay * backoff_multiplier, max_delay)
                    if jitter:
                        delay = delay * (1 + random.uniform(-0.2, 0.2))
        raise RuntimeError(f"API request failed after {max_retries} retries: {last_error}")

    def query(self, **params) -> dict:
        """action=query request."""
        p = {"action": "query", "format": "json", **params}
        return self._request(p)

    def parse(self, page: str, prop: str = "wikitext") -> dict:
        """action=parse request."""
        p = {"action": "parse", "page": page, "prop": prop, "format": "json"}
        return self._request(p)


def probe_api_endpoint(origin: str, strategy_base_url: Optional[str] = None) -> Optional[str]:
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
