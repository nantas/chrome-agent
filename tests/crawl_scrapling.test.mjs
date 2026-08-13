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

/** Build a stub `api`. Pure helpers use lightweight real-ish implementations;
 *  side-effecting helpers are captured/stubbed via the given overrides. */
function stubApi(overrides = {}) {
  const written = {};
  return {
    fs: {
      readFileSync: (p) => written[p] ?? "",
      readdirSync: () => [],
      existsSync: (p) => p in written,
      unlinkSync: () => {},
    },
    // result/file builders — real-ish passthroughs (pure)
    makeResult: (command, target, repoRef, summary, artifacts, nextAction, result = "success", extra = {}) =>
      ({ result, command, target, summary, artifacts, next_action: nextAction, ...extra }),
    absoluteArtifact: (filePath, lifecycle, description) => ({ path: filePath, lifecycle, description }),
    writeTextFile: (p, content) => { written[p] = content; },
    log: { info() {}, warn() {} },
    generateHandoff: (ctx) => ({ path: "/run/handoff.md", summary: "stub-handoff" }),
    buildCrawlReport: ({ events, result }) => `# report\nresult: ${result}\n${(events || []).join("\n")}`,
    // traversal helpers — stubbed per-test
    pagePatternMatches: () => true,
    selectFetcher: () => "scrapling-get",
    runScraplingPreflight: () => ({ ok: true, status: "available" }),
    runEngineFetch: () => ({ ok: true, stderr: "" }),
    collectLinksFromHtml: () => [],
    convertTraversalToMarkdown: () => ({ successful: [], failed: [], mergedPath: null }),
    collectMarkdownArtifacts: () => [],
    buildScraplingExtractionArgs: () => [],
    // unused in tested paths but referenced by signature breadth
    runObscuraPreflight: () => ({ ok: false }),
    findAvailablePort: async () => 0,
    startObscuraServe: async () => ({}),
    concurrentFetch: async () => [],
    stopObscuraServe: () => {},
    urlToStructuredPath: (u) => "/run/out.md",
    nextPaginationUrl: () => null,
    scraplingCacheDir: () => "/cache",
    ensureDir: () => {},
    isScraplingCached: () => false,
    saveScraplingCache: () => {},
    scraplingSlugFromUrl: (u) => "slug",
    loadScraplingCache: () => null,
    ...overrides,
  };
}

test("preflight failure returns failure result and emits a handoff report path", async () => {
  const api = stubApi({
    runScraplingPreflight: () => ({ ok: false, status: "unavailable", stdout: "", stderr: "boom" }),
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
    collectMarkdownArtifacts: () => [mdArtifact],
    convertTraversalToMarkdown: () => ({ successful: [{ url: "https://example.com/home" }], failed: [], mergedPath: "/run/crawl-output.md" }),
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

/** Static call-site discipline check.
 *
 * Spec: crawl-scrapling-orchestrator-is-a-seam-module,
 *       scenario all-bundled-helpers-called-via-api-prefix.
 *
 * crawl_scrapling.mjs is an independent ESM module whose helpers arrive via
 * an injected `api` bundle. A bare-identifier call to a bundled helper
 * (e.g. `collectMarkdownArtifacts(x)` instead of `api.collectMarkdownArtifacts(x)`)
 * resolves to nothing in module scope and throws ReferenceError at runtime.
 * This test reads the bundle definition from cli.mjs, then greps the seam
 * module for any bundled key used bare and fails if one exists.
 *
 * ponytail: ceiling — string literals are not stripped; no bundled key
 * currently appears in a string literal in this module. Refine if one ever does.
 */
async function readCrawlApiKeys() {
  const fs = await import("node:fs");
  const cliSrc = fs.readFileSync(new URL("../scripts/chrome-agent-cli.mjs", import.meta.url), "utf8");
  // Locate the crawlApi bundle block via brace matching.
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
  // Keys: shorthand `foo,` → foo; keyed `foo: bar` → foo.
  const keys = [];
  for (const raw of block.split(",")) {
    const entry = raw.trim();
    if (!entry) continue;
    const m = entry.match(/^([A-Za-z_$][\w$]*)/);
    if (m) keys.push(m[1]);
  }
  return keys;
}

test("all bundled helpers are called via the api. prefix (no bare-identifier calls)", async () => {
  const fs = await import("node:fs");
  const bundledKeys = await readCrawlApiKeys();
  const modSrc = fs.readFileSync(new URL("../scripts/lib/crawl_scrapling.mjs", import.meta.url), "utf8");
  const lines = modSrc.split("\n");

  const violations = [];
  lines.forEach((line, idx) => {
    const stripped = line.trim();
    // skip comment lines (//, *, block-comment continuation)
    if (stripped.startsWith("//") || stripped.startsWith("*")) return;
    for (const key of bundledKeys) {
      const re = new RegExp("(?<![\\w$])" + key.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&") + "(?![\\w$])", "g");
      let m;
      while ((m = re.exec(line)) !== null) {
        // Determine whether the key has a namespace base (api., console., path., …)
        // or is a bare identifier. The bug class is a bare-identifier call:
        // resolves to nothing in module scope → ReferenceError.
        let prefix = line.slice(0, m.index).replace(/\s+$/, "");
        // strip a trailing spread operator — `...key` is bare, `...api.key` is not
        if (prefix.endsWith("...")) prefix = prefix.slice(0, -3).replace(/\s+$/, "");
        // qualified: any dotted base (api.key, console.log, path.join, …)
        if (prefix.endsWith(".")) continue;
        // local declaration of this name (function/const/let/var/import) — not a call
        if (new RegExp("\\b(function|const|let|var)\\s+" + key + "\\b|\\bimport\\b").test(line)) continue;
        violations.push({ key, line: idx + 1, text: stripped });
      }
    }
  });

  assert.deepEqual(violations, [],
    "crawl_scrapling.mjs must call every bundled helper via `api.` prefix. " +
    "Bare calls throw ReferenceError at runtime (see spec all-bundled-helpers-called-via-api-prefix). " +
    "Violations:\n" + violations.map((v) => `  L${v.line}: ${v.key} — ${v.text}`).join("\n"));
});
