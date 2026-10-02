"""Shared HTML admission. Transport success is not content success."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

_PROMPT = re.compile(r'just a (?:moment|second)|checking your browser|verify (?:that )?you are human|enable javascript|请稍候', re.I)


def classify_html(html, http_status=None):
    result = dict(admitted=False, reason=None, protection_type=None, signals=[],
                  page_title=None, content_length=len(html) if isinstance(html, str) else 0,
                  http_status=http_status)
    if not isinstance(html, str) or not html.strip():
        return {**result, 'reason': 'empty_content'}
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('title')
    result['page_title'] = title.get_text(' ', strip=True)[:200] if title else None
    for node in soup.select('pre, code, template'):
        node.decompose()
    challenge_structure = bool(soup.select('[id^="cf-chl"], #challenge-form, #challenge-running'))
    for script in soup.find_all('script'):
        src = script.get('src', '')
        if '/challenge-platform/' in src or '_cf_chl_opt' in script.get_text():
            challenge_structure = True
    headings = ' '.join(n.get_text(' ', strip=True) for n in soup.select('h1, h2, [role="heading"]'))
    presentation = bool(_PROMPT.search((result['page_title'] or '') + ' ' + headings))
    if challenge_structure and presentation:
        return {**result, 'reason': 'challenge_page', 'protection_type': 'cloudflare-managed',
                'signals': ['challenge_structure', 'verification_presentation']}
    if http_status is not None and http_status >= 400:
        return {**result, 'reason': 'http_error'}
    return {**result, 'admitted': True}


def admit_html_file(filename, http_status=None):
    try:
        html = Path(filename).read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        reason = 'missing_output' if isinstance(error, FileNotFoundError) else 'unreadable_output'
        return {**classify_html(None, http_status), 'reason': reason}
    return classify_html(html, http_status)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('filename')
    parser.add_argument('--http-status', type=int)
    args = parser.parse_args()
    print(json.dumps(admit_html_file(args.filename, args.http_status)))


if __name__ == '__main__':
    main()
