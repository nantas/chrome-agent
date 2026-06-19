import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { buildScraplingExtractionArgs } from "../scripts/lib/scrapling-extraction-args.mjs";

const repoRoot = process.cwd();
const cliJs = path.join(repoRoot, "scripts", "chrome-agent-cli.mjs");
const cliSource = fs.readFileSync(cliJs, "utf8");

// =============================================================================
// Unit tests for the shared extraction-args helper.
// Spec ref: specs/fetch-strategy-selector/spec.md
//   - strategy-content-selector-passthrough  (selector → ["-s", selector])
//   - ai-targeted-fallback-when-no-selector  (no selector → ["--ai-targeted"])
//   - shared-arg-builder-helper              (mediawiki-api → [strategy.path])
//   - selector-injection-safety              (selector stays a discrete argv element)
// =============================================================================

test("helper: strategy with non-empty content selector + scrapling fetcher returns -s args", () => {
  const strategy = {
    path: "/repo/sites/strategies/posthog.com/strategy.md",
    document: { extraction: { selectors: { content: "div[class*='@container/reader-content']" } } },
  };
  const args = buildScraplingExtractionArgs(strategy, "get");
  assert.deepEqual(args, ["-s", "div[class*='@container/reader-content']"]);
});

test("helper: does NOT pass --ai-targeted when a content selector is declared", () => {
  const strategy = {
    path: "/repo/s.md",
    document: { extraction: { selectors: { content: "main article" } } },
  };
  const args = buildScraplingExtractionArgs(strategy, "get");
  assert.equal(args.includes("--ai-targeted"), false, "must not emit --ai-targeted when selector present");
  assert.deepEqual(args, ["-s", "main article"]);
});

test("helper: strategy WITHOUT content selector falls back to --ai-targeted", () => {
  // selector field missing entirely
  const strategyNoBlock = { path: "/repo/s.md", document: { extraction: {} } };
  assert.deepEqual(buildScraplingExtractionArgs(strategyNoBlock, "get"), ["--ai-targeted"]);

  // extraction block missing
  const strategyNoExtraction = { path: "/repo/s.md", document: {} };
  assert.deepEqual(buildScraplingExtractionArgs(strategyNoExtraction, "fetch"), ["--ai-targeted"]);

  // selector present but empty string
  const strategyEmpty = { path: "/repo/s.md", document: { extraction: { selectors: { content: "" } } } };
  assert.deepEqual(buildScraplingExtractionArgs(strategyEmpty, "get"), ["--ai-targeted"]);

  // selector present but whitespace-only
  const strategyWs = { path: "/repo/s.md", document: { extraction: { selectors: { content: "   " } } } };
  assert.deepEqual(buildScraplingExtractionArgs(strategyWs, "get"), ["--ai-targeted"]);
});

test("helper: null strategy falls back to --ai-targeted (no match)", () => {
  assert.deepEqual(buildScraplingExtractionArgs(null, "get"), ["--ai-targeted"]);
  assert.deepEqual(buildScraplingExtractionArgs(undefined, "get"), ["--ai-targeted"]);
});

test("helper: mediawiki-api fetcher returns [strategy.path] regardless of selector", () => {
  const strategy = {
    path: "/repo/sites/strategies/wiki.example.com/strategy.md",
    document: { extraction: { selectors: { content: "should-be-ignored" } } },
  };
  // Even with a content selector declared, mediawiki-api path must use strategy.path
  assert.deepEqual(buildScraplingExtractionArgs(strategy, "mediawiki-api"), [strategy.path]);
  assert.equal(buildScraplingExtractionArgs(strategy, "mediawiki-api").includes("-s"), false);
});

test("helper: mediawiki-api fetcher with null strategy returns empty array", () => {
  assert.deepEqual(buildScraplingExtractionArgs(null, "mediawiki-api"), []);
});

// selector-injection-safety: selector with special chars stays ONE argv element
test("helper: selector with special characters is a single discrete argv element", () => {
  const tricky = "div[class*='@container/reader-content']";
  const strategy = { path: "/repo/s.md", document: { extraction: { selectors: { content: tricky } } } };
  const args = buildScraplingExtractionArgs(strategy, "get");
  assert.equal(args.length, 2, "exactly two elements: ['-s', <selector>]");
  assert.equal(args[0], "-s");
  assert.equal(args[1], tricky, "selector value is intact and unescaped");
  // Negative: ensure the helper did not split on spaces, brackets, or quotes
  assert.equal(args.some((a) => a.includes("class*") && a !== tricky), false);
  assert.equal(args.some((a) => a === "div[class*='@container/reader-content']"), true);
});

// cloakbrowser (D6): separate CLI accepts neither -s nor --ai-targeted.
// Pre-change code hardcoded ["--ai-targeted"] which made every cloakbrowser
// fetch fail (unrecognized arg, affecting protection_level:high strategies).
// Helper MUST return [] — no extraction flag needed — and never emit -s to it.
test("helper: cloakbrowser fetcher returns [] (no extraction flag)", () => {
  const strategy = {
    path: "/repo/s.md",
    document: { extraction: { selectors: { content: "main" } } },
  };
  assert.deepEqual(buildScraplingExtractionArgs(strategy, "cloakbrowser"), []);
  // Negative: never pass -s nor --ai-targeted to cloakbrowser_fetcher.py
  const args = buildScraplingExtractionArgs(strategy, "cloakbrowser");
  assert.equal(args.includes("-s"), false);
  assert.equal(args.includes("--ai-targeted"), false);
});

// =============================================================================
// Source-text structural assertions: fetch & crawl must consume the helper
// (no hardcoded ["--ai-targeted"] in the extraction call sites).
// Pattern follows tests/crawl-scrapling-pages-scope.test.mjs.
// =============================================================================

test("runFetch builds fetch args via buildScraplingExtractionArgs (no hardcoded ai-targeted)", () => {
  const fnStart = cliSource.indexOf("function runFetch(");
  assert.notEqual(fnStart, -1, "runFetch must exist");
  // Slice a generous window of the function body
  const slice = cliSource.slice(fnStart, fnStart + 4000);

  assert.match(slice, /buildScraplingExtractionArgs\(/, "runFetch must call buildScraplingExtractionArgs");
  // The old hardcoded form must be gone from runFetch
  assert.doesNotMatch(
    slice,
    /\[["']--ai-targeted["']\]/,
    "runFetch must not hardcode ['--ai-targeted'] anymore",
  );
});

test("runFetch imports the shared helper module", () => {
  assert.match(
    cliSource,
    /import\s*\{[^}]*buildScraplingExtractionArgs[^}]*\}\s*from\s*["'][^"']*scrapling-extraction-args\.mjs["']/,
    "chrome-agent-cli.mjs must import buildScraplingExtractionArgs",
  );
});

test("crawl convert loop (convertTraversalToMarkdown) consumes the helper at both extraction sites", () => {
  const fnStart = cliSource.indexOf("function convertTraversalToMarkdown(");
  assert.notEqual(fnStart, -1, "convertTraversalToMarkdown must exist");
  const nextFn = cliSource.indexOf("\nfunction ", fnStart + 1);
  const slice = cliSource.slice(fnStart, nextFn === -1 ? fnStart + 6000 : nextFn);

  assert.match(slice, /buildScraplingExtractionArgs\(/, "convertTraversalToMarkdown must call the helper");
  // Both the prefetched-html (file://) path and the per-page fetch path must
  // route through the helper — no literal ["--ai-targeted"] remaining.
  const literalMatches = slice.match(/\[["']--ai-targeted["']\]/g);
  assert.equal(literalMatches, null, "convertTraversalToMarkdown must not hardcode ['--ai-targeted']");
});

test("runCrawlScrapling (incl. --phase convert cache fastpath) has no hardcoded ai-targeted", () => {
  const fnStart = cliSource.indexOf("async function runCrawlScrapling(");
  assert.notEqual(fnStart, -1, "runCrawlScrapling must exist");
  const nextAsync = cliSource.indexOf("\nasync function ", fnStart + 1);
  const nextFn = cliSource.indexOf("\nfunction ", fnStart + 1);
  const candidates = [nextAsync, nextFn].filter((x) => x !== -1);
  const end = candidates.length ? Math.min(...candidates) : fnStart + 8000;
  const slice = cliSource.slice(fnStart, end);

  // The --phase convert cache fastpath must route cached HTML conversion
  // through the helper too (strategy is in scope in runCrawlScrapling).
  assert.match(slice, /buildScraplingExtractionArgs\(/, "runCrawlScrapling must call the helper");
  const literalMatches = slice.match(/\[["']--ai-targeted["']\]/g);
  assert.equal(literalMatches, null, "runCrawlScrapling must not hardcode ['--ai-targeted']");
});
