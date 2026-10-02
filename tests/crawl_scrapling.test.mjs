/** Behavioral injection test for the extracted crawl orchestrator.
 *
 * Spec: extract-crawl-scrapling-orchestrator /
 *       crawl-scrapling-orchestrator-is-a-seam-module,
 *       scenario orchestrator-extractable-and-importable.
 *
 * Before extraction, runCrawlScrapling was inline in cli.mjs and untestable
 * without spawning Chrome. Now it accepts an `api` bundle of all its
 * cli.mjs helpers — this test calls it with a stub `api` (real pure helpers
 * where cheap, stubs for side-effecting helpers) and asserts the two core
 * control-flow paths: preflight failure (early handoff) and a minimal
 * successful bounded traversal.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import { runCrawlScrapling } from "../scripts/lib/crawl_scrapling.mjs";

// Minimal strategy/doc/page fixtures.
const START_PAGE = { id: "home", url_example: "https://example.com/home", label: "Home", links_to: [] };
const strategy = { path: "/s/strat.md" };
const doc = { structure: { pages: [START_PAGE] } };

function baseCtx(overrides = {}) {
  return {
    repoRoot: "/repo",
    repoRef: "repo://chrome-agent",
    resolutionMode: "resolved",
    runDir: "/run",
    reportPath: "/run/crawl-report.md",
    manifestPath: "/run/manifest.json",
    emitReport: true,
    targetUrl: "https://example.com/home",
    strategy,
    doc,
    startPage: START_PAGE,
    matchingPage: START_PAGE,
    entryPoints: ["home"],
    ...overrides,
  };
}

/** Build a stub `api` as named concern objects (matches the crawlApi bundle
 *  shape in cli.mjs). Pure helpers use lightweight real-ish implementations;
 *  side-effecting helpers are stubbed. `overrides` is a flat map of
 *  {group: {helper: fn}} for per-test stubbing. */
function stubApi(groupOverrides = {}) {
  const written = {};
  const api = {
    fs: {
      readFileSync: (p) => written[p] ?? "",
      readdirSync: () => [],
      existsSync: (p) => p in written,
      unlinkSync: () => {},
    },
    log: { info() {}, warn() {} },
    report: {
      // result/file builders — real-ish passthroughs (pure)
      makeResult: (command, target, repoRef, summary, artifacts, nextAction, result = "success", extra = {}) =>
        ({ result, command, target, summary, artifacts, next_action: nextAction, ...extra }),
      absoluteArtifact: (filePath, lifecycle, description) => ({ path: filePath, lifecycle, description }),
      writeTextFile: (p, content) => { written[p] = content; },
      buildCrawlReport: ({ events, result }) => `# report\nresult: ${result}\n${(events || []).join("\n")}`,
    },
    handoff: {
      generateHandoff: () => ({ path: "/run/handoff.md", summary: "stub-handoff" }),
    },
    engine: {
      selectFetcher: () => "scrapling-get",
      runEngineFetch: () => ({ ok: true, stderr: "" }),
    },
    cache: {
      runScraplingPreflight: () => ({ ok: true, status: "available" }),
      scraplingCacheDir: () => "/cache",
      ensureDir: () => {},
      isScraplingCached: () => false,
      saveScraplingCache: () => {},
      scraplingSlugFromUrl: () => "slug",
      loadScraplingCache: () => null,
      buildScraplingExtractionArgs: () => [],
    },
    pool: {
      runObscuraPreflight: () => ({ ok: false }),
      findAvailablePort: async () => 0,
      startObscuraServe: async () => ({}),
      concurrentFetch: async () => [],
      stopObscuraServe: () => {},
    },
    traversal: {
      pagePatternMatches: () => true,
      collectLinksFromHtml: () => [],
      nextPaginationUrl: () => null,
    },
    convert: {
      convertTraversalToMarkdown: () => ({ successful: [], failed: [], mergedPath: null }),
      collectMarkdownArtifacts: () => [],
      urlToStructuredPath: () => "/run/out.md",
    },
  };
  // Apply per-group overrides: groupOverrides = { cache: { runScraplingPreflight: fn }, ... }
  for (const [group, helperOverrides] of Object.entries(groupOverrides)) {
    if (api[group]) Object.assign(api[group], helperOverrides);
  }
  return api;
}

test("preflight failure returns failure result and emits a handoff report path", async () => {
  const api = stubApi({
    cache: { runScraplingPreflight: () => ({ ok: false, status: "unavailable", stdout: "", stderr: "boom" }) },
  });
  const ctx = baseCtx();
  const result = await runCrawlScrapling(ctx, { markdown: false }, api);

  assert.equal(result.result, "failure");
  assert.equal(result.command, "crawl");
  assert.match(result.summary, /preflight failed/i);
  assert.equal(result.handoff_path, "/run/handoff.md");
  // Report was written (side effect went through api.writeTextFile).
  assert.equal(api.fs.readFileSync(ctx.reportPath).includes("result: failure"), true);
});

test("minimal successful traversal visits the start page and writes a manifest", async () => {
  const api = stubApi(); // preflight ok, fetch ok, no discovered links
  const ctx = baseCtx();
  const result = await runCrawlScrapling(ctx, { markdown: false }, api);

  assert.equal(result.result, "success");
  // Manifest was written with the visited URL.
  const manifest = JSON.parse(api.fs.readFileSync(ctx.manifestPath));
  assert.deepEqual(manifest.visited, ["https://example.com/home"]);
  assert.equal(manifest.start_page, "home");
  assert.equal(manifest.bounded_by.unrestricted_recursive_spider, false);
});

test("markdown:true (default) path collects markdown artifacts and does not throw ReferenceError", async () => {
  // Regression guard: the default crawl path runs with markdown === true and
  // SHALL call api.collectMarkdownArtifacts(runDir) into finalArtifacts. Before
  // the fix this threw ReferenceError (bare-identifier call). See spec scenario
  // markdown-true-branch-produces-artifacts-not-reference-error.
  const mdArtifact = { path: "/run/crawl-output.md", lifecycle: "disposable", description: "merged crawl output" };
  const api = stubApi({
    convert: {
      collectMarkdownArtifacts: () => [mdArtifact],
      convertTraversalToMarkdown: () => ({ successful: [{ url: "https://example.com/home" }], failed: [], mergedPath: "/run/crawl-output.md" }),
    },
  });
  const ctx = baseCtx();
  const result = await runCrawlScrapling(ctx, { markdown: true }, api);

  assert.equal(result.result, "success");
  // The sentinel markdown artifact MUST appear in finalArtifacts — proves the
  // api.collectMarkdownArtifacts branch was reached and returned its value.
  assert.ok(result.artifacts.some((a) => a.path === mdArtifact.path),
    "markdown:true path must include the artifact returned by api.collectMarkdownArtifacts");
});

test("no circular import: module does not import from cli.mjs", async () => {
  const fs = await import("node:fs");
  const src = fs.readFileSync(new URL("../scripts/lib/crawl_scrapling.mjs", import.meta.url), "utf8");
  const importLines = src.split("\n").filter((l) => l.trim().startsWith("import"));
  const hasCycle = importLines.some((l) => l.includes("chrome-agent-cli"));
  assert.equal(hasCycle, false,
    "crawl_scrapling.mjs must not import from cli.mjs (would create a cycle)");
});


/** Read the crawlApi bundle from cli.mjs as a {group: [helper]} map.
 *
 * The bundle is organized as named concern objects; this parses each group
 * and its member helpers. Used by the discipline tests below.
 */
async function readCrawlApiGroups() {
  const fs = await import("node:fs");
  const cliSrc = fs.readFileSync(new URL("../scripts/chrome-agent-cli.mjs", import.meta.url), "utf8");
  const start = cliSrc.indexOf("crawlApi = {");
  if (start === -1) throw new Error("crawlApi bundle not found in cli.mjs");
  let i = cliSrc.indexOf("{", start);
  let depth = 0;
  const blockStart = i;
  for (; i < cliSrc.length; i++) {
    const c = cliSrc[i];
    if (c === "{") depth++;
    else if (c === "}") { depth--; if (depth === 0) break; }
  }
  const block = cliSrc.slice(blockStart + 1, i);
  // Parse groups: `groupName: { a, b, c }`.
  const groups = {};
  const groupRe = /([A-Za-z_$][\w$]*)\s*:\s*\{([^}]*)\}/g;
  let gm;
  while ((gm = groupRe.exec(block)) !== null) {
    const groupName = gm[1];
    groups[groupName] = [];
    for (const member of gm[2].split(",")) {
      const m = member.trim().match(/^([A-Za-z_$][\w$]*)/);
      if (m) groups[groupName].push(m[1]);
    }
  }
  return groups;
}

/** Flatten groups into a helper→group map (helpers are unique across groups). */
async function readCrawlApiHelperToGroup() {
  const groups = await readCrawlApiGroups();
  const map = {};
  for (const [g, helpers] of Object.entries(groups)) {
    for (const h of helpers) map[h] = g;
  }
  return map;
}

test("all bundled helpers are called via the api.<group>. prefix (no bare-identifier calls)", async () => {
  // C4 invariant, preserved: a bare-identifier call to a bundled helper
  // resolves to nothing in module scope → ReferenceError at runtime.
  const fs = await import("node:fs");
  const helperToGroup = await readCrawlApiHelperToGroup();
  const modSrc = fs.readFileSync(new URL("../scripts/lib/crawl_scrapling.mjs", import.meta.url), "utf8");
  const lines = modSrc.split("\n");

  const bareViolations = [];
  lines.forEach((line, idx) => {
    const stripped = line.trim();
    if (stripped.startsWith("//") || stripped.startsWith("*")) return;
    for (const key of Object.keys(helperToGroup)) {
      const re = new RegExp("(?<![\\w$.])" + key.replace(/[.*+?^${}()|[\]\\\\]/g, "\\\\$&") + "(?![\\w$])", "g");
      let m;
      while ((m = re.exec(line)) !== null) {
        const before = line.slice(0, m.index).replace(/\s+$/, "").replace(/\.{3}$/, "");
        if (before.endsWith(".")) continue; // qualified (api.x, console.x, …)
        if (new RegExp("\\b(function|const|let|var)\\s+" + key + "\\b|\\bimport\\b").test(line)) continue;
        bareViolations.push({ key, line: idx + 1, text: stripped });
      }
    }
  });

  assert.deepEqual(bareViolations, [],
    "crawl_scrapling.mjs must call every bundled helper via `api.<group>.` prefix. " +
    "Bare calls throw ReferenceError at runtime (C4 invariant). Violations:\n" +
    bareViolations.map((v) => `  L${v.line}: ${v.key} — ${v.text}`).join("\n"));
});

test("seam surface uses named concern groups (no flat api.<helper> calls to groupable helpers)", async () => {
  // Spec: crawl-scrapling-orchestrator-is-a-seam-module,
  //       scenario seam-surface-uses-named-concern-groups.
  // A flat `api.<helper>` call where <helper> belongs to a declared group is
  // FORBIDDEN — it must be `api.<group>.<helper>`.
  const fs = await import("node:fs");
  const helperToGroup = await readCrawlApiHelperToGroup();
  const modSrc = fs.readFileSync(new URL("../scripts/lib/crawl_scrapling.mjs", import.meta.url), "utf8");

  const flatViolations = [];
  for (const [helper, group] of Object.entries(helperToGroup)) {
    const re = new RegExp("\\bapi\\." + helper.replace(/[.*+?^${}()|[\]\\\\]/g, "\\\\$&") + "(?![A-Za-z0-9_])", "g");
    let m;
    while ((m = re.exec(modSrc)) !== null) {
      flatViolations.push({ helper, shouldUse: `api.${group}.${helper}` });
    }
  }

  assert.deepEqual(flatViolations, [],
    "crawl_scrapling.mjs must use api.<group>.<helper>, not flat api.<helper>. " +
    "Spec: seam-surface-uses-named-concern-groups. Violations:\n" +
    flatViolations.map((v) => `  ${v.helper} should be ${v.shouldUse}`).join("\n"));
});

test("failed page diagnostic HTML cannot be written to production cache", async () => {
  let writes = 0;
  const api = stubApi({
    engine: { runEngineFetch: () => ({ok:false, stderr:'challenge_page'}) },
    fs: { readdirSync: () => ['page.raw.html'], readFileSync: () => '<h1>Just a moment</h1>https://example.com/home' },
    cache: { saveScraplingCache: () => { writes++; } },
  });
  const result = await runCrawlScrapling(baseCtx(), {markdown:false, phase:'fetch'}, api);
  assert.equal(result.result,'failure');
  assert.equal(writes,0);
});
