"""ProtectionIdentifier — identify protection mechanisms from engine errors and HTML."""

import re
from typing import Optional

from bs4 import BeautifulSoup


def identify(engine_results: list[dict], html_content: Optional[str]) -> dict:
    """Identify protection mechanism based on engine chain results and HTML markers.

    Returns:
        {
            "type": str (cloudflare-managed|cloudflare-turnstile|login-wall|rate-limit|none),
            "detection_basis": str,
            "engine_override": Optional[str],
        }
    """
    # Check engine results for HTTP status codes and error messages
    for result in engine_results:
        status = result.get("http_status")
        detail = (result.get("detail") or "").lower()
        stderr = (result.get("stderr") or "").lower()
        combined = detail + " " + stderr

        if status == 403:
            if "just a moment" in combined or "checking your browser" in combined:
                return {
                    "type": "cloudflare-managed",
                    "detection_basis": f"403 + 'Just a moment...' from {result['engine']}",
                    "engine_override": "cloakbrowser-fetch",
                }
            if "turnstile" in combined or "cf-turnstile" in combined:
                return {
                    "type": "cloudflare-turnstile",
                    "detection_basis": f"403 + turnstile marker from {result['engine']}",
                    "engine_override": "cloakbrowser-fetch",
                }
            if "login" in combined or "sign in" in combined:
                return {
                    "type": "login-wall",
                    "detection_basis": f"403 + login redirect from {result['engine']}",
                    "engine_override": None,
                }

        if status == 429 or "rate limit" in combined or "too many requests" in combined:
            return {
                "type": "rate-limit",
                "detection_basis": f"429 / rate limit from {result['engine']}",
                "engine_override": None,
            }

    # Check HTML content for protection markers
    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ", strip=True).lower()

        if "just a moment" in text or "checking your browser" in text:
            return {
                "type": "cloudflare-managed",
                "detection_basis": "HTML contains 'Just a moment...'",
                "engine_override": "cloakbrowser-fetch",
            }

        if soup.find("iframe", src=re.compile(r"turnstile|challenges\.cloudflare")):
            return {
                "type": "cloudflare-turnstile",
                "detection_basis": "HTML contains Cloudflare Turnstile iframe",
                "engine_override": "cloakbrowser-fetch",
            }

        if "recaptcha" in text or soup.find(class_=re.compile(r"g-recaptcha")):
            return {
                "type": "cloudflare-managed",
                "detection_basis": "HTML contains reCAPTCHA marker (treated as high-protection managed challenge)",
                "engine_override": "cloakbrowser-fetch",
            }

        if "login" in text or "sign in" in text or "log in" in text:
            # Distinguish between login-wall and actual login page
            forms = soup.find_all("form")
            password_inputs = soup.find_all("input", {"type": "password"})
            if password_inputs or any("login" in (f.get("action") or "").lower() for f in forms):
                return {
                    "type": "login-wall",
                    "detection_basis": "HTML contains login form",
                    "engine_override": None,
                }

    # No protection detected
    return {
        "type": "none",
        "detection_basis": "No protection markers found in engine results or HTML",
        "engine_override": None,
    }
