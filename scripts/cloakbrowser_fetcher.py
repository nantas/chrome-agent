#!/usr/bin/env python3
"""
cloakbrowser_fetcher.py — CloakBrowser page fetcher for chrome-agent

Wraps the CloakBrowser Python package to provide a standardized fetch
interface compatible with the chrome-agent pipeline.

Usage:
    python3 scripts/cloakbrowser_fetcher.py <url> [options]

Exit codes:
    0 — Success
    1 — Network error (unreachable host, DNS failure)
    2 — Timeout
    3 — Block/challenge detected
    4 — Browser crash
    5 — Binary/module not found
    6 — Other error
"""

import argparse
import json
import os
import platform
import random
import sys
import time


def check_cloakbrowser_available():
    """Verify CloakBrowser module is importable."""
    try:
        from cloakbrowser import launch  # noqa: F401
        return True
    except ImportError:
        return False


def fetch_page(
    url,
    headless=True,
    wait_until="domcontentloaded",
    timeout=30,
    proxy=None,
    stealth_args=True,
    humanize=False,
    fingerprint_seed=None,
    timezone=None,
    locale=None,
    geoip=False,
    persistent_context=None,
    extra_args=None,
    verbose=False,
):
    """
    Fetch a page using CloakBrowser.

    Returns dict with: title, url, html, content, success, error, timing
    """
    from cloakbrowser import launch

    browser = None
    start_time = time.time()

    try:
        # --- Fingerprint seed ---
        if fingerprint_seed is None:
            fingerprint_seed = random.randint(10000, 99999)

        # --- Platform-aware fingerprint ---
        fp_platform = None
        if platform.system() == "Linux":
            fp_platform = "windows"  # Linux spoofs Windows by default (more common)

        # --- Build extra_args with fingerprint seed + platform ---
        chrome_extra = list(extra_args or [])
        chrome_extra.append(f"--fingerprint={fingerprint_seed}")
        if fp_platform:
            chrome_extra.append(f"--fingerprint-platform={fp_platform}")

        # --- Persistent context via --user-data-dir ---
        if persistent_context:
            os.makedirs(persistent_context, exist_ok=True)
            chrome_extra.append(f"--user-data-dir={persistent_context}")

        # --- Proxy: pass via launch() proxy parameter ---
        # CloakBrowser handles string proxy URLs natively

        launch_args = {
            "headless": headless,
            "stealth_args": stealth_args,
            "args": chrome_extra if chrome_extra else None,
        }
        if proxy:
            launch_args["proxy"] = proxy
        if timezone:
            launch_args["timezone"] = timezone
        if locale:
            launch_args["locale"] = locale
        if geoip:
            launch_args["geoip"] = True
        if humanize:
            launch_args["humanize"] = True

        if verbose:
            safe_args = {k: v for k, v in launch_args.items() if k != "proxy"}
            print(f"[cloakbrowser] Launch args: {safe_args}", file=sys.stderr)

        browser = launch(**launch_args)
        context = browser.new_context()
        page = context.new_page()

        if verbose:
            print(
                f"[cloakbrowser] Navigating to {url} "
                f"(wait_until={wait_until}, timeout={timeout}s)",
                file=sys.stderr,
            )

        # --- Navigate ---
        response = page.goto(url, wait_until=wait_until, timeout=timeout * 1000)

        # --- Challenge detection loop (Turnstile etc.) ---
        max_challenge_wait = min(timeout, 15)
        challenge_start = time.time()
        challenge_indicators = [
            "just a moment",
            "请稍候",
            "attention",
            "checking your browser",
            "enable javascript",
            "cloudflare",
        ]
        while time.time() - challenge_start < max_challenge_wait:
            title = page.title()
            if any(ind in title.lower() for ind in challenge_indicators):
                if verbose:
                    elapsed = time.time() - challenge_start
                    print(
                        f"[cloakbrowser] Challenge detected, waiting... ({elapsed:.1f}s)",
                        file=sys.stderr,
                    )
                page.wait_for_timeout(2000)
            else:
                break

        # --- Post-challenge network settle ---
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        # --- Check if still on challenge page after wait ---
        final_title = page.title()
        if any(ind in final_title.lower() for ind in challenge_indicators):
            elapsed = time.time() - start_time
            return {
                "title": final_title,
                "url": page.url,
                "html": page.content(),
                "content": None,
                "success": False,
                "error": {
                    "category": "challenge",
                    "type": "ChallengeNotResolved",
                    "message": (
                        f"Challenge page still present after {max_challenge_wait}s: "
                        f"title='{final_title}'"
                    ),
                },
                "timing": {"total_seconds": round(elapsed, 2)},
                "_exit_code": 3,
            }

        # --- Check for block pages (CAPTCHA wall / WAF block) ---
        content_text = page.evaluate("""() => {
            const body = document.body;
            if (!body) return '';
            return body.innerText || '';
        }""")
        html_content = page.content()

        block_signatures = [
            "access denied",
            "blocked",
            "your request has been blocked",
            "ray id",
            "error 1020",
            "error 1015",
        ]
        is_block = (
            len(content_text) < 500
            and any(sig in content_text.lower() for sig in block_signatures)
        )
        if is_block:
            elapsed = time.time() - start_time
            return {
                "title": final_title,
                "url": page.url,
                "html": html_content,
                "content": content_text,
                "success": False,
                "error": {
                    "category": "block",
                    "type": "BlockPageDetected",
                    "message": f"Target returned a block page: title='{final_title}'",
                },
                "timing": {"total_seconds": round(elapsed, 2)},
                "_exit_code": 3,
            }

        # --- Success path ---
        final_url = page.url
        elapsed = time.time() - start_time

        return {
            "title": final_title,
            "url": final_url,
            "html": html_content,
            "content": content_text,
            "success": True,
            "error": None,
            "timing": {"total_seconds": round(elapsed, 2)},
        }

    except ImportError as e:
        elapsed = time.time() - start_time
        return {
            "title": None,
            "url": url,
            "html": None,
            "content": None,
            "success": False,
            "error": {
                "category": "binary",
                "type": type(e).__name__,
                "message": f"CloakBrowser module or binary unavailable: {e}",
            },
            "timing": {"total_seconds": round(elapsed, 2)},
            "_exit_code": 5,
        }

    except Exception as e:
        elapsed = time.time() - start_time
        error_type = type(e).__name__
        error_msg = str(e)

        # --- Error classification ---
        error_category = "other"
        exit_code = 6

        if "Timeout" in error_type or "timeout" in error_msg.lower():
            error_category = "timeout"
            exit_code = 2
        elif "net::" in error_msg or "ERR_" in error_msg:
            error_category = "network"
            exit_code = 1
        elif "crash" in error_msg.lower() or "disconnected" in error_msg.lower():
            error_category = "browser"
            exit_code = 4
        elif "license" in error_msg.lower() or "redistribut" in error_msg.lower():
            error_category = "license"
            exit_code = 6

        return {
            "title": None,
            "url": url,
            "html": None,
            "content": None,
            "success": False,
            "error": {
                "category": error_category,
                "type": error_type,
                "message": error_msg,
            },
            "timing": {"total_seconds": round(elapsed, 2)},
            "_exit_code": exit_code,
        }

    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="CloakBrowser page fetcher")
    parser.add_argument("url", help="Target URL to fetch")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument(
        "--timeout", "-t", type=int, default=30, help="Timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--headless", action="store_true", default=True, help="Run in headless mode (default)"
    )
    parser.add_argument(
        "--no-headless", dest="headless", action="store_false", help="Run in headed mode"
    )
    parser.add_argument(
        "--wait-until",
        default="domcontentloaded",
        choices=["load", "domcontentloaded", "networkidle"],
        help="Page lifecycle wait condition (default: domcontentloaded)",
    )
    parser.add_argument("--proxy", help="Proxy URL (http/https/socks5)")
    parser.add_argument(
        "--no-stealth-args",
        dest="stealth_args",
        action="store_false",
        help="Disable default stealth fingerprint args",
    )
    parser.add_argument(
        "--humanize", action="store_true", help="Enable human-like mouse/keyboard/scroll behavior"
    )
    parser.add_argument(
        "--fingerprint-seed", type=int, default=None, help="Deterministic fingerprint seed (10000-99999)"
    )
    parser.add_argument("--timezone", help="IANA timezone (e.g. America/New_York)")
    parser.add_argument("--locale", help="BCP 47 locale (e.g. en-US)")
    parser.add_argument(
        "--geoip", action="store_true", help="Auto-detect timezone/locale from proxy IP"
    )
    parser.add_argument(
        "--persistent-context", help="Path to persistent user data directory for cookie/session reuse"
    )
    parser.add_argument(
        "--extra-args",
        nargs="*",
        help="Additional Chromium CLI arguments (e.g. --extra-args --disable-gpu --disable-extensions)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    # Check availability — classify as 'binary' error
    if not check_cloakbrowser_available():
        print(
            "ERROR: cloakbrowser module not found. Install with: pip install cloakbrowser",
            file=sys.stderr,
        )
        sys.exit(5)

    result = fetch_page(
        url=args.url,
        headless=args.headless,
        wait_until=args.wait_until,
        timeout=args.timeout,
        proxy=args.proxy,
        stealth_args=args.stealth_args,
        humanize=args.humanize,
        fingerprint_seed=args.fingerprint_seed,
        timezone=args.timezone,
        locale=args.locale,
        geoip=args.geoip,
        persistent_context=args.persistent_context,
        extra_args=args.extra_args,
        verbose=args.verbose,
    )

    if args.json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        if result["success"]:
            lines = [
                f"Title: {result['title']}",
                f"URL: {result['url']}",
                f"Content length: {len(result['content'] or '')} chars",
                f"HTML length: {len(result['html'] or '')} chars",
                f"Time: {result['timing']['total_seconds']}s",
                "",
                "--- Content ---",
                result["content"] or "(empty)",
            ]
            output = "\n".join(lines)
        else:
            err = result["error"]
            output = f"ERROR [{err['category']}]: {err['message']}"
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output)
            else:
                print(output, file=sys.stderr)
            sys.exit(result.get("_exit_code", 6))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        if args.verbose:
            print(f"[cloakbrowser] Output written to {args.output}", file=sys.stderr)
    else:
        print(output)

    if not result["success"]:
        sys.exit(result.get("_exit_code", 6))


if __name__ == "__main__":
    main()
