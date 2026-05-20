# Writeback

## Change: link-fallback-redirect-skip

## Verification Status

✅ All specs verified. Empty files 7→1, broken links unchanged.

## Writeback Targets

### 1. `openspec/specs/pipeline/pipeline-conversion.md`

**Action**: ADD scenario — link-resolver-fallback-to-wiki-url

**Content**:
- New scenario: when LinkResolver encounters a target not in manifest, it returns the original wiki URL instead of a bare `.md` relative path
- Applicable to both ExactTitleLinkResolver and ShortNameLinkResolver

### 2. `openspec/specs/pipeline-converters/spec.md`

**Action**: ADD requirement — redirect-detection-and-skip

**Content**:
- New requirement: convert phase detects redirect pages via `redirectMsg` HTML marker
- Redirect pages are skipped (no .md output, status "redirect")
- Redirect map is built and injected into link resolution

### 3. `openspec/specs/mediawiki/api.md`

**Action**: UPDATE — LinkResolver resolve() fallback semantics

**Content**:
- Fallback return changed from `[display](slug.md)` to `[display](https://{domain}/wiki/{slug})`
- New `redirect_map` parameter on convert_links() and resolve() methods
- When target is a redirect source, resolve follows the redirect before manifest lookup

## Execution Notes

- All writebacks are spec/doc updates (no code changes)
- Changes should reference the change `link-fallback-redirect-skip` as the source
