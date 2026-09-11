# Verification

## 验证结论

Implementation verified against this change's four delta specs. Core tasks and convergence checks completed; documentation/spec writeback follows the target map below. No bulk site crawl, historical manifest/Markdown migration, downstream ingest, commit, push or archive was performed.

## Spec-to-Implementation Coverage

| Spec requirements | Implementation | Evidence |
| --- | --- | --- |
| discover-kernel: pipeline-manifest-source; cli: manifest-input-compatibility | lib/manifest_contract.py; pipeline cli/orchestrator | test_manifest_contract: version/domain/fingerprint, legacy in-memory adaptation, ambiguity/path rejection, discover rejection before I/O |
| discover-kernel: explore-discovery-modules; cli: Phase-based execution | explore/page_discovery.py; lib/mediawiki-crawl.mjs; public cli | mediawiki-crawl.test: discovery/alias/--yes/partial/conflicts; actual public CLI subprocess dispatch; test_page_discovery_contract: both kernel routes |
| discover-kernel: discovery-manifest-contract; unclassified-main-namespace-directory; list-index-consumer-agreement | discovery_allpages/page_discovery; assemble; converter and link_resolver | test_page_discovery_contract: ns0/14/3000 paths, canonical/redirect resolution without adding pages, eligible/absent lists, real index body and live index links |
| discover-kernel: summary-reflects-discovery-evidence | ObservedClient/build_summary in page_discovery.py | test_page_discovery_contract: unknown null, observed request denominator, directory/index agreement and total-empty failure |
| cli: mediawiki-error-and-fallback-semantics | mediawiki-crawl workflow and existing internalFailure adapter | Node tests: exit20/14/null/SIGTERM, no fallback, stderr/upstream context; real CLI JSON and handoff |
| explore-architecture-gate: all 3 requirements | shared extraction/schema.py, architecture_gate.py | test_extraction_schema/test_explore_architecture_gate: malformed shapes/names, unknown keys, shared consumers, full Fandom/neon Gate, generic tooltip and AST docstring exclusion |
| strategy: Extraction; fandom-extraction-configuration-migration | shared schema; preprocessor; template/neon and 4 other MediaWiki strategies | test_extraction_schema: lazyload/edit/TOC/ambox/normalization behavior, old inert-rule equivalence, non-MediaWiki descriptive-rule compatibility; six real site samples |
| strategy: 字段适配规则; Registry 索引更新; 输出与结果格式; strategy-registry-sync | strategy_lifecycle/bootstrap CLI, freeze, registry-based findStrategy | test_strategy_lifecycle/test_freeze_gap: whitelist, target URLs, draft metadata, invalid profile, validation failure preserves markers, reviewed freeze, publication rollback and capability-gap artifact |

## Task-to-Evidence Coverage

- 1.1–1.2: baseline retained user registry/growagarden/mobalytics modifications; spec source targets explicitly mapped; LSP unavailable so rg used. P0 and task-specific docs reviewed.
- 2.1–2.16: each slice first produced a failing targeted regression, then passed its targeted unittest/node:test set. RED included missing new modules, empty-directory mismatch, missing v2/summary/failure_context, invalid old Fandom config, legacy index link, and generic Gate false positives.
- 3.1–3.2: complete required Python suite last ran **143 tests / OK**, Node suite **106 tests / all pass**. After subsequent canonical-list and Gate additions, targeted affected tests passed (11 discovery/manifest; 10 Gate/manifest). Python 3.9 AST grammar check passed for modified/new Python files; new .mjs remains ESM with named functions.
- 3.3: `python3 scripts/test_runner.py site-samples --domain DOMAIN` passed with **1 non-skipped real sample per domain** after adding MediaWiki-cache lookup and passing actual strategy extraction to shared full conversion. Runner regression proves strip_footer and cache selection, and rejects empty output. Initial 0-sample runs were NOT counted as validation.
- 3.4: actual `node scripts/chrome-agent-cli.mjs doctor --check capabilities --format json` returned **success**, 44 checks. Discover references existing discover-kernel spec; CLI/validation adapters marked infrastructure or mirror rather than duplicate kernels.
- 3.5: source/global runtime and skill files compare byte-equal with cmp; installed hash equals current HEAD `f7fd98ac70444ae4849cc6b9e0d293b6e222366e`. Full `chrome-agent doctor --format json` returned **success**, no failed checks.
- 3.6: no source manifest rewritten; legacy empty paths preserved; no my-wiki changes. Only five single-page API reads were made for missing regression samples, under the authorized validation scope.

## 关键证据入口

| 证据类型 | 证据路径/链接 | 对应 requirement/task |
| --- | --- | --- |
| Reproducible tests | tests/test_manifest_contract.py; tests/test_page_discovery_contract.py; tests/mediawiki-crawl.test.mjs | discovery/CLI/assembly |
| Configuration/lifecycle tests | tests/test_extraction_schema.py; tests/test_strategy_lifecycle.py; tests/test_freeze_gap.py | Gate/migration/freeze |
| Runner consumer proof | tests/test_site_runner_strategy.py | 3.3 |
| Local full run logs | /tmp/gag-unittest-final.log; /tmp/gag-node-final.log; /tmp/gag-capabilities-final.json; /tmp/gag-doctor-full.json | convergence |
| Per-domain sample logs | /tmp/gag-sample-DOMAIN.log | 3.3 |

### Site sample provenance and final result

| Domain | Page / source | Count | Exit |
| --- | --- | --- | --- |
| growagarden.fandom.com | Crops / one action=parse request, 2026-09-10 | 1 | 0 |
| neonabyss.fandom.com | Items / one action=parse request, 2026-09-10 | 1 | 0 |
| slaythespire.wiki.gg | Cards_List / one action=parse request, 2026-09-10 | 1 | 0 |
| balatrowiki.org | Jokers / one action=parse request, 2026-09-10 | 1 | 0 |
| bindingofisaacrebirth.wiki.gg | Bloody Gust / existing MediaWiki cache | 1 | 0 |
| vampire.survivors.wiki | Weapons / one action=parse request, 2026-09-10 | 1 | 0 |

Requests used existing requests library and `chrome-agent/pipeline` UA; no browser/engine installation. Snapshots are new site regression golden files, not regenerated historical bulk outputs. Large tables retain the converter's existing nested-table warning behavior; structural checks passed.

## 缺口与阻塞项

No blocking implementation gap identified. Validation is bounded: one real sample per affected domain plus offline behavior fixtures, not full-site extraction equivalence or fixed 1596-page coverage. Complete API HTML is persisted losslessly as six `samples/*.html.gz` fixtures (416,662 compressed bytes total), with adjacent source.json URL/provenance/SHA256. The runner falls back to these when caches are absent. Forced no-cache validation ran all six persisted fixtures: **6 tests / OK / 0 skipped**. No DOM pruning or historical output replacement was performed. Five non-MediaWiki sites use narrative cleanup contracts and were deliberately excluded from MediaWiki operation-schema enforcement. Four MediaWiki sites with unsupported inert normalize_infobox/strip_dpl_wikitext/strip_json_data declarations were migrated with equivalent preprocessing evidence, without inventing implementations. No all-site schema rewrite was performed.

Final fixture portability regression: `tests/test_site_runner_strategy.py` first failed to find a compressed fixture without cache, then passed after adding the stdlib gzip fallback. Full-page golden/structural checks remain unchanged.

## Archive validation (2026-09-11)

- Pre-archive `openspec validate restore-mediawiki-discovery-and-strategy-contracts --strict`: passed; 27/27 tasks and all seven artifacts complete.
- All 18 delta requirement blocks match their explicitly mapped canonical files after whitespace normalization. Archive retains `.openspec.yaml`; no incoming change-path links required repair.
- Actual `node scripts/chrome-agent-cli.mjs doctor --check capabilities --format json`: success. Staged and working-tree `git diff --check`: passed.
- Canonical CLI validation remains limited by pre-existing repository layout: discover-kernel, cli and explore-architecture-gate lack the CLI-required Purpose section in HEAD; strategy uses merged canonical files and is not recognized as a standalone item. This is not a successful canonical strict validation; exact mapped requirement comparison provides the sync evidence. No unrelated format migration performed.
