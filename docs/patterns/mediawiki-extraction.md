# MediaWiki Content Extraction Patterns

> **Version:** v1 draft  
> **Coverage:** Weird Gloop-hosted MediaWiki (validated on `vampire.survivors.wiki` and `balatrowiki.org`, both MediaWiki 1.45.3). May not fully apply to self-hosted or Wikimedia Foundation instances.

---

## 1. Platform Taxonomy

### Weird Gloop MediaWiki

- **Hosting:** Weird Gloop (managed MediaWiki farm, e.g. `*.wiki` domains).
- **Version:** Typically MediaWiki 1.45.x at time of writing.
- **Skin:** Vector or Weird Gloop customisation; DOM structure follows standard MediaWiki conventions (`#firstHeading`, `#mw-content-text`, `.mw-parser-output`).
- **Rendering:** Server-side static HTML. No JavaScript required for article body content.
- **Protection level:** Usually `low` (no Cloudflare challenge, no login wall for read access).
- **Engine preference:** `scrapling-get` is sufficient; `obscura-fetch` as fallback for pages with minor dynamic elements.

### Self-hosted / Standard MediaWiki

- **Variability:** Skins, extensions, and DOM classes differ widely.
- **Validation required:** Before applying these patterns, confirm the target instance matches the DOM assumptions below.

---

## 2. Noise Taxonomy

Noise is organised into four clusters. Each cluster contains specific artefact types observed on Weird Gloop instances.

### 2.1 Navigation Cluster

Elements that aid site navigation but are not article content.

| Noise | Description | vampire.survivors.wiki | balatrowiki.org |
|-------|-------------|------------------------|-----------------|
| Footer sections | "Tools", "Privacy", "About", "Disclaimers", "Navigation menu" | Yes (has "Navigation menu" heading) | Yes (no "Navigation menu" heading) |
| Section edit links | `[edit]`, `[edit source]` next to headings | Rare | Present |
| Skip links | "Jump to navigation", "Jump to search" | Present | Present |

### 2.2 Template Cluster

Artefacts exposed from MediaWiki templates, especially hidden or module-generated content.

| Noise | Description | vampire.survivors.wiki | balatrowiki.org |
|-------|-------------|------------------------|-----------------|
| DPL wikitext | Exposed `{{hl|...}}`, `{{Chips|...}}`, `{{Mult|...}}` from `metadata-dpl` spans | Rare | Present (Jokers page) |
| Scribunto JSON data | JSON rows from Lua module output (display:none content surfaced by Scrapling) | Present | Absent |
| Empty parentheses | `()` from empty template parameters | Present | Present |
| Inline style blocks | `<style data-mw-deduplicate="...">` (when present in raw HTML) | Absent | Absent |

### 2.3 Link Cluster

Malformed or non-content links in Scrapling text output.

| Noise | Description | vampire.survivors.wiki | balatrowiki.org |
|-------|-------------|------------------------|-----------------|
| Nested image links | `[![](thumb-url)](article-url)` pattern | Present | Present |
| Internal link residue | `"title")` trailing artefacts from link syntax | Present | Present |
| Category links | `[[Category:...]]` lines | Present | Present |

### 2.4 Table Cluster

Table formatting issues specific to MediaWiki infoboxes and data tables.

| Noise | Description | vampire.survivors.wiki | balatrowiki.org |
|-------|-------------|------------------------|-----------------|
| Sparse infobox | Many empty columns (`|  |  |  |  |`) with ≤2 non-empty cells | Present | Present |
| Missing separator | Markdown table missing `| --- |` after header row | Present | Present |

---

## 3. Cleanup Pipeline

### Rule Ordering Rationale

Rules are executed in cluster order: **navigation → template → link → table**.

1. **Navigation first** removes structural noise (footers, edit links) that might contain templates or links.
2. **Template second** cleans up wikitext and JSON artefacts before link/table normalisation tries to parse them.
3. **Link third** operates on cleaner text, avoiding false matches against template syntax.
4. **Table last** because table normalisation depends on stable cell boundaries; earlier steps may remove rows, changing counts.

### Cluster Execution Flow

```
Input: Scrapling Markdown output
  → Navigation cluster
      → strip_footer
      → strip_edit_links
      → strip_skip_links
  → Template cluster
      → strip_dpl_wikitext
      → strip_json_data
      → strip_empty_parens
  → Link cluster
      → convert_nested_images
      → normalize_internal
      → strip_category_links
  → Table cluster
      → normalize_infobox
      → fix_separators
Output: Cleaned Markdown
```

### Profile Mappings

| Profile | Navigation | Template | Link | Table |
|---------|------------|----------|------|-------|
| `vampire-survivors` | strip_footer, strip_skip_links | strip_json_data, strip_empty_parens | convert_nested_images, normalize_internal, strip_category_links | normalize_infobox, fix_separators |
| `balatro` | strip_footer, strip_edit_links, strip_skip_links | strip_dpl_wikitext, strip_empty_parens | convert_nested_images, normalize_internal, strip_category_links | normalize_infobox, fix_separators |
| `generic-mediawiki` | All rules | All rules | All rules | All rules (with aggressive-mode warning) |

---

## 4. Cross-site Reuse

When encountering a new MediaWiki site (especially Weird Gloop), follow this checklist before applying extraction patterns:

1. **Run `chrome-agent explore <url>` for backend detection**
   - If the site is not yet in `sites/strategies/registry.json`, `explore` will automatically fetch raw HTML and detect known backends (e.g., Weird Gloop MediaWiki via `<meta name="generator">`, `#mw-content-text`, and `/w/` URL patterns).
   - When a backend is detected, `explore` recommends a concrete `bootstrap-strategy` command using an existing reference domain (e.g., `vampire.survivors.wiki` or `balatrowiki.org`).

2. **Use `bootstrap-strategy` to generate a draft strategy**
   - Example: `chrome-agent bootstrap-strategy https://newsite.wiki/w/Main_Page --from balatrowiki.org`
   - This generates `sites/strategies/newsite.wiki/strategy.md` with copied frontmatter, replaced domain/URLs, and a `backend: weird-gloop-mediawiki-1.45` advisory tag.
   - The generated strategy must be reviewed and validated before production use.

3. **Verify MediaWiki identity manually (if backend detection missed)**
   - Check HTML `<meta name="generator" content="MediaWiki ...">`.
   - Confirm DOM structure contains `#mw-content-text` or `.mw-parser-output`.

4. **Assess protection level**
   - Run `scrapling-get <url>` and inspect output.
   - If blocked or challenged, check `protection_level` and consider `obscura-fetch` or `scrapling-stealthy-fetch`.

5. **Compare against noise taxonomy**
   - Run a sample article through Scrapling and compare output against the four clusters above.
   - Note any site-specific noise not covered by existing clusters.

6. **Select cleanup profile**
   - If the site is Weird Gloop and matches vampire/balatro structure: start with the closest existing profile.
   - Otherwise: use `generic-mediawiki` with `--dry-run` first to inspect rule effects.

7. **Identify gaps**
   - If site-specific noise is found, create a new profile in `clean-mediawiki.sh` or document the gap in this file.
   - Do not extend the generic profile with unverified rules.

---

## References

- `sites/strategies/vampire.survivors.wiki/strategy.md` — vampire.survivors.wiki crawl strategy
- `sites/strategies/vampire.survivors.wiki/_attachments/clean-mediawiki.sh` — cleanup script with profiles
- `sites/strategies/vampire.survivors.wiki/_attachments/extract-links.py` — category page link extraction
