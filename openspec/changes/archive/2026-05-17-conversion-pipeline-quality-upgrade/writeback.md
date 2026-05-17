# Writeback

## Change

- **Name:** conversion-pipeline-quality-upgrade
- **Verification:** PASS (see `verification.md`)

## Writeback Targets

### 1. `openspec/specs/sample-self-check/spec.md`

**Delta type:** MODIFIED — expand S1-S7 to S1-S12

**Changes:**
- S1: Add full URL verification requirement and `relative_image_url` fixable type
- S2: Replace legacy `.md` link resolution with zero relative `/wiki/` link detection, add `relative_link` fixable type
- S3: Add field count ≥3 requirement and `infobox_html_residue` fixable type, add HTML tag residue detection
- S5: Add raw HTML closing tag detection (`</a>`, `</span>`, `</div>`) and unresolved HTML entity detection (`&amp;`, `&lt;`, `&gt;`)
- S6: Replace qualitative row check with quantitative ≤5% deviation threshold
- ADDED S8: Section completeness — verify all `mw-headline` sections preserved as Markdown headings, `fixable_type: "section_loss"`
- ADDED S9: Navigation leakage — detect ≥3 consecutive nav keyword lines, `fixable_type: "nav_leak"`
- ADDED S10: YouTube title quality — reject generic `YouTube Video (ID)` titles, `fixable_type: "youtube_title"`
- ADDED S11: Zero relative links — grep for `](/wiki/` and `](/images/`, `fixable_type: "relative_link"`
- ADDED S12: Infobox semantic quality — Name spacing, filename-as-name, ID navigation leak detection, `fixable_type: "name_spacing"` / `"name_is_filename"` / `"id_navigation_leak"`
- ADDED `auto-remediation-extended` — 6 new fixable types in auto-remediation loop

### 2. `openspec/specs/explore-workflow/spec.md`

**Delta type:** MODIFIED — add Agent Gate requirements

**Changes:**
- ADDED `agent-gate-self-check-before-presentation` — S1-S12 summary table before sample content
- ADDED `agent-gate-sample-file-paths` — samples written to `outputs/<run-tag>/` with file paths presented
- ADDED `agent-gate-self-audit-before-user-review` — agent compares source vs converted before user sees
- ADDED `agent-gate-full-retest-on-converter-change` — all samples re-tested on any converter change
- ADDED `agent-gate-iteration-limit` — max 3 fix→retest cycles
- MODIFIED `sample-conversion-and-self-check` — run S1-S12 (not S1-S7), present summary before content

### 3. `openspec/specs/pipeline-converters/spec.md`

**Delta type:** MODIFIED — add new methods, update clean_html behavior spec

**Changes:**
- ADDED `balanced-element-removal-method` — `remove_balanced_element()` and `remove_all_matching()` as static methods
- ADDED `tooltip-icon-link-merge-method` — `merge_tooltip_links()` as static method
- ADDED `youtube-oembed-extraction-method` — `extract_video_links()` with oEmbed API + fallback
- ADDED `video-links-insert-into-body` — insert into `## In-game Footage` section
- MODIFIED `config-driven-cleanup` — add `skip_patterns` from `image_filtering`, `wiki_domain` required, `infobox_field_handlers` propagation
- MODIFIED `used-for-toc-removal` — change from "SHALL use `remove_all_matching()`" to "SHALL perform balanced/nested-aware element removal (via DOM-native CSS selector decomposition or equivalent)"
- MODIFIED `used-for-edit-section-removal` — same relaxation to allow selectolax CSS path

### 4. `openspec/specs/site-strategy/spec.md`

**Delta type:** MODIFIED — add infobox field handler configuration

**Changes:**
- ADDED `infobox-field-handler-configuration` — `extraction.infobox_field_handlers` map with 8 handler types (text, image, count_images, extract_cur_id, dedup_pools, simplify_collection, extract_tags)
- ADDED `extraction-config-propagation` — handlers passed to converter at construction time

### 5. `AGENTS.md`

**Delta type:** MODIFIED — update explore gate reference

**Changes:**
- Section "Explore→Crawl Confirmation Gate", item 4: add reference to Agent Gate rules in `skills/chrome-agent/SKILL.md`
- ✅ Already applied in task 2.7.2

## Non-writeback Updates (already applied)

| Target | Change | Status |
|--------|--------|--------|
| `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` | Added `infobox_field_handlers`, extended `skip_patterns`, added nav cleanup selectors | ✅ Applied |
| `sites/templates/mediawiki-wiki-gg.yaml` | Added `image_filtering`, `cleanup_selectors`, updated `content_profile` | ✅ Applied |
| `sites/strategies/registry.json` | No structural change needed (domain entry exists, field count unchanged) | ✅ N/A |
| `skills/chrome-agent/SKILL.md` | Added Agent Gate section | ✅ Applied |
| `scripts/explore/requirements.txt` | Added `selectolax>=0.3`, `markdownify>=0.11` | ✅ Applied |

## Execution Checklist

- [ ] 4.3.1 Update `openspec/specs/sample-self-check/spec.md`
- [ ] 4.3.2 Update `openspec/specs/explore-workflow/spec.md`
- [ ] 4.3.3 Update `openspec/specs/pipeline-converters/spec.md`
- [ ] 4.3.4 Update `openspec/specs/site-strategy/spec.md`
- [ ] 4.3.5 Verify `AGENTS.md` already updated
