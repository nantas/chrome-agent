"""Application-layer crawl mirror: JSON/file bridge to the shared HTML kernel."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from scripts.lib.content_admission import admit_html_file
from scripts.lib.extraction.converter import convert_page_full
from scripts.lib.extraction.schema import require_valid_extraction


def convert_request(request: dict) -> dict:
    rules = request.get('extraction', {})
    require_valid_extraction(rules)
    admission = admit_html_file(request['html_path'])
    if not admission['admitted']:
        return {'ok': False, 'error': admission['reason'], 'admission': admission}
    html = Path(request['html_path']).read_text(encoding='utf-8')
    markdown = convert_page_full(html, rules)
    Path(request['output_path']).write_text(markdown, encoding='utf-8')
    return {'ok': True, 'output_path': request['output_path']}


def main() -> None:
    try:
        result = convert_request(json.load(sys.stdin))
    except Exception as exc:
        result = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}
    print(json.dumps(result))
    sys.exit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
