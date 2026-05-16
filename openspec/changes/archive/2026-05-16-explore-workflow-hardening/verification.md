# Verification

## Evidence Checklist

### Doctor Check
- [ ] `chrome-agent doctor --format json` output includes `explore_deps` check item
- [ ] `explore_deps` shows `ok: true` when `bs4` and `yaml` are installed
- [ ] `explore_deps` shows `ok: false` with installation instructions when missing

### Explore Preflight
- [ ] `chrome-agent explore <wiki-url>` with missing deps returns `result: "failure"` with install command
- [ ] `chrome-agent explore <wiki-url>` with deps present proceeds to deep discovery (may succeed or fail based on target)
- [ ] Explore no longer has silent try/catch — pipeline failures produce clear error output

### Converter Parameterization
- [ ] `HtmlToMarkdownConverter()` without `wiki_domain` raises `TypeError`
- [ ] `HtmlToMarkdownConverter(wiki_domain="test.wiki.gg")` works correctly
- [ ] StS strategy provides `cleanup_selectors` and `image_filtering.skip_patterns`
- [ ] Converter reads from `extraction_config` parameter instead of hardcoded patterns
- [ ] Isaac wiki strategy has `cleanup_selectors` and `image_filtering.skip_patterns`

### Governance
- [ ] AGENTS.md contains "Explore→Crawl Confirmation Gate" section
- [ ] SKILL.md contains Gate 1-4 definitions
- [ ] SKILL.md contains "Explore Result Interpretation" section with field mapping table

## Post-Implementation Smoke Tests

```bash
# 1. Doctor check
chrome-agent doctor --format json | python3 -c "import json,sys; d=json.load(sys.stdin); ec=[c for c in d['extra']['checks'] if c['name']=='explore_deps']; assert ec, 'explore_deps check missing'; print('explore_deps:', ec[0])"

# 2. Converter TypeError check
python3 -c "from scripts.mediawiki_api_extract.converters.html_to_markdown import HtmlToMarkdownConverter; HtmlToMarkdownConverter()" 2>&1 | grep -i typeerror

# 3. Converter with config
python3 -c "
from scripts.mediawiki_api_extract.converters.html_to_markdown import HtmlToMarkdownConverter
c = HtmlToMarkdownConverter('test.wiki.gg', extraction_config={'cleanup_selectors': ['.test'], 'image_filtering': {'skip_patterns': ['logo.png']}})
print('cleanup:', c._REMOVAL_SELECTORS)
print('config:', c.config)
"

# 4. Syntax checks
node --check scripts/chrome-agent-cli.mjs
python3 -c "import ast; [ast.parse(open(f).read()) for f in ['scripts/explore/main.py', 'scripts/mediawiki-api-extract/converters/html_to_markdown.py', 'scripts/mediawiki-api-extract/pipeline/phase_b.py', 'scripts/mediawiki-api-extract/standalone.py']]"
```
