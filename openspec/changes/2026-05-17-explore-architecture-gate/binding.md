# Binding: Explore Architecture Gate

## Capability Binding

| Capability | Spec Path | Status |
|-----------|-----------|--------|
| `explore-architecture-gate` | `specs/explore-architecture-gate/spec.md` | **NEW** |

## Modified Capabilities

| Capability | Spec Path | Delta |
|-----------|-----------|-------|
| `explore-workflow` | `../../specs/explore-workflow/spec.md` | Workflow phases reordered: Architecture Gate inserted between self-check and user confirmation |
| `explore-skill-gates` | `../../specs/explore-skill-gates/spec.md` | Agent Gate rules extended with architecture checks |

## Artifacts

### New Files
- `scripts/explore/architecture_gate.py` — programmatic strategy→pipeline validation
- `openspec/specs/explore-architecture-gate/spec.md` — frozen spec

### Modified Files
- `openspec/specs/explore-workflow/spec.md` — insert Architecture Gate phase
- `openspec/specs/explore-skill-gates/spec.md` — add architecture gate rules
- `.agents/skills/chrome-agent/SKILL.md` — add Agent Gate: Architecture Gate section

## Verification

- [ ] `scripts/explore/architecture_gate.py` can be imported without errors
- [ ] Dead config detection correctly flags strategy fields not referenced in pipeline
- [ ] Agent audit checklist covers all violation types from commit 55ac8d4
- [ ] Gate blocks user confirmation when violations exist
