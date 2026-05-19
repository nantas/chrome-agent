# Verification Checklist: split-fetch-convert-phases

## Prerequisites
- Isaac wiki strategy: `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md`
- Test pages (10): The Lamb, Isaac, Brimstone, Items, Cards, Shovel (Disambiguation), The Lost, D6, Mom, Magic Mushroom

## Steps

### Step 1: Discovery + manifest trimming
- [ ] `chrome-agent crawl https://bindingofisaacrebirth.wiki.gg --discovery-only` → produces manifest
- [ ] Manually trim manifest to 10 test pages

### Step 2: Fetch phase
- [ ] `--phase fetch --from-manifest <10-page-manifest>` → check `.cache/mediawiki/bindingofisaacrebirth.wiki.gg/*.json` created
- [ ] Each JSON contains `title`, `html`, `content_acquisition`, `fetched_at` fields

### Step 3: Convert phase
- [ ] `--phase convert --from-manifest <10-page-manifest>` → check .md output in runDir
- [ ] No API requests made (offline test if possible)

### Step 4: Strategy modification + re-convert
- [ ] Modify `extraction.cleanup_selectors` in strategy
- [ ] `--phase convert --from-manifest <same-manifest>` → output reflects change
- [ ] No API requests made

### Step 5: Cache skip verification
- [ ] `--phase fetch --from-manifest <same-manifest>` again → all 10 pages skipped
- [ ] Log shows "skipping X cached"

### Step 6: Incremental fetch
- [ ] Delete 1 cache file
- [ ] `--phase fetch --from-manifest <same-manifest>` → only that page re-fetched

### Step 7: Re-fetch flag
- [ ] `--phase fetch --re-fetch --from-manifest <same-manifest>` → all 10 pages re-fetched and overwritten

### Step 8: Offline convert
- [ ] Disconnect network
- [ ] `--phase convert --from-manifest <same-manifest>` → succeeds with no network

## CLI validation
- [ ] `python3 -m scripts.mediawiki-api-extract --help` shows new phase choices
- [ ] `--phase extract` → rejected with error
- [ ] `--keep-html` → shows deprecation warning
- [ ] `--no-markdown` → shows tip message
