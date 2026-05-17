# Binding: Explore KI Lifecycle

## Capability Binding

| Capability | Spec Path | Status |
|-----------|-----------|--------|
| `explore-ki-lifecycle` | `specs/explore-ki-lifecycle/spec.md` | **NEW** |

## Modified Capabilities

| Capability | Spec Path | Delta |
|-----------|-----------|-------|
| `sample-self-check` | `../../specs/sample-self-check/spec.md` | Self-check output enhanced with KI classification (owner + priority) |
| `explore-workflow` | `../../specs/explore-workflow/spec.md` | Workflow phases: KI Lifecycle inserted between Architecture Gate and User Confirmation |
| `site-strategy` | `../../specs/site-strategy/spec.md` | KI table schema extended with Status, Priority, Owner, Resolution columns |

## Artifacts

### New Files
- `openspec/specs/explore-ki-lifecycle/spec.md` — frozen spec

### Modified Files
- `openspec/specs/explore-workflow/spec.md` — insert KI Lifecycle phase
- `openspec/specs/sample-self-check/spec.md` — add KI classification to check output
- `sites/strategies/bindingofisaacrebirth.wiki.gg/strategy.md` — expanded KI table (completed in this session)
- `sites/templates/mediawiki-wiki-gg.yaml` — if template contains KI table placeholder

## Verification

- [ ] All 6 KIs in Isaac Wiki strategy have correct Owner and Priority
- [ ] KI table schema is parseable and backward-compatible
- [ ] KI fix order in session follows P0→P1→P2→P3
- [ ] 3-iteration limit is respected
