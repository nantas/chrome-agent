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

test("no circular import: module does not import from cli.mjs", async () => {
  const fs = await import("node:fs");
  const src = fs.readFileSync(new URL("../scripts/lib/crawl_scrapling.mjs", import.meta.url), "utf8");
  const importLines = src.split("\n").filter((l) => l.trim().startsWith("import"));
  const hasCycle = importLines.some((l) => l.includes("chrome-agent-cli"));
  assert.equal(hasCycle, false,
    "crawl_scrapling.mjs must not import from cli.mjs (would create a cycle)");
});
