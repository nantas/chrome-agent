import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import os from "node:os";

const repoRoot = process.cwd();
const cliJs = path.join(repoRoot, "scripts", "chrome-agent-cli.mjs");
const source = fs.readFileSync(cliJs, "utf8");

// Extract a named function as a standalone runnable string
function extractFn(fnName) {
  const fnStart = source.indexOf(`function ${fnName}(`);
  if (fnStart === -1) return null;
  const openBrace = source.indexOf("{", fnStart);
  if (openBrace === -1) return null;
  let depth = 1, pos = openBrace + 1;
  while (depth > 0 && pos < source.length) {
    if (source[pos] === "{") depth++;
    if (source[pos] === "}") depth--;
    pos++;
  }
  return source.slice(fnStart, pos);
}

// Write test to temp .cjs file, run, return parsed result
function callFn(fnName, argsArray, depNames = []) {
  const scripts = depNames.map(extractFn).filter(Boolean);
  scripts.push(extractFn(fnName));
  const combined = scripts.join("\n");
  assert.ok(combined.length > 0, fnName + " must exist in source");
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "ga-test-"));
  const tmpFile = path.join(tmpDir, "test.cjs");
  const call = "\nconsole.log(JSON.stringify(" + fnName + "(" + argsArray.join(", ") + ")));\n";
  fs.writeFileSync(tmpFile, combined + call, "utf8");
  const result = spawnSync("node", [tmpFile], { encoding: "utf8" });
  fs.rmSync(tmpDir, { recursive: true });
  if (result.status !== 0) {
    throw new Error(fnName + " script failed (status " + result.status + "): " + (result.stderr || result.stdout));
  }
  return JSON.parse(result.stdout.trim());
}

// Behavioral test helper for resolveSitemapIndex with an injected fake fetcher.
// fetchBehavior maps subUrl -> { ok, httpCode, content }. No network needed.
function callResolveSitemapIndex(subSitemapUrls, fetchBehavior) {
  const resolveSrc = extractFn("resolveSitemapIndex");
  assert.ok(resolveSrc, "resolveSitemapIndex must exist in source");
  const deps = [extractFn("parseSitemapXml"), resolveSrc];
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "ga-rsi-"));
  const tmpFile = path.join(tmpDir, "rsi.cjs");
  const runner = [
    deps[0],
    deps[1],
    'const __bh = ' + JSON.stringify(fetchBehavior) + ';',
    'const __fetch = (url) => __bh[url] || { ok: false, httpCode: 404, content: "" };',
    'const __urls = ' + JSON.stringify(subSitemapUrls) + ';',
    'console.log(JSON.stringify(resolveSitemapIndex(__urls, __fetch)));'
  ].join("\n");
  fs.writeFileSync(tmpFile, runner, "utf8");
  const result = spawnSync("node", [tmpFile], { encoding: "utf8" });
  fs.rmSync(tmpDir, { recursive: true });
  if (result.status !== 0) {
    throw new Error("resolveSitemapIndex script failed: " + (result.stderr || result.stdout));
  }
  return JSON.parse(result.stdout.trim());
}

// ═══════════════════════════════════════════
// parseSitemapXml tests
// ═══════════════════════════════════════════

test("parseSitemapXml exists in source", async (t) => {
  assert.ok(extractFn("parseSitemapXml"), "parseSitemapXml must exist");
});

test("parseSitemapXml extracts URLs from flat urlset", async (t) => {
  const r = callFn("parseSitemapXml", [
    JSON.stringify('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>https://example.com/page1</loc></url>\n  <url><loc>https://example.com/page2</loc></url>\n</urlset>')
  ]);
  assert.deepStrictEqual(r, { urls: ["https://example.com/page1", "https://example.com/page2"] });
});

test("parseSitemapXml returns empty for empty urlset", async (t) => {
  const r = callFn("parseSitemapXml", [
    JSON.stringify('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n</urlset>')
  ]);
  assert.deepStrictEqual(r, { urls: [] });
});

test("parseSitemapXml detects sitemapindex", async (t) => {
  const r = callFn("parseSitemapXml", [
    JSON.stringify('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <sitemap><loc>https://x.com/s.xml</loc></sitemap>\n</sitemapindex>')
  ]);
  assert.strictEqual(r.isIndex, true);
});

test("parseSitemapXml extracts sub-sitemap URLs from sitemapindex (multiple)", async (t) => {
  const r = callFn("parseSitemapXml", [
    JSON.stringify('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <sitemap><loc>https://example.com/sitemap-0.xml</loc></sitemap>\n  <sitemap><loc>https://example.com/sitemap-1.xml</loc></sitemap>\n</sitemapindex>')
  ]);
  assert.strictEqual(r.isIndex, true);
  assert.ok(Array.isArray(r.sitemaps), "should return sitemaps array");
  assert.deepStrictEqual(r.sitemaps, ["https://example.com/sitemap-0.xml", "https://example.com/sitemap-1.xml"]);
});

test("parseSitemapXml extracts single sub-sitemap (PostHog shape)", async (t) => {
  const r = callFn("parseSitemapXml", [
    JSON.stringify('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://posthog.com/sitemap/sitemap-0.xml</loc></sitemap></sitemapindex>')
  ]);
  assert.strictEqual(r.isIndex, true);
  assert.deepStrictEqual(r.sitemaps, ["https://posthog.com/sitemap/sitemap-0.xml"]);
});

test("parseSitemapXml flat urlset has no sitemaps field (regression guard)", async (t) => {
  const r = callFn("parseSitemapXml", [
    JSON.stringify('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>https://example.com/page1</loc></url>\n</urlset>')
  ]);
  assert.strictEqual(r.isIndex, undefined);
  assert.strictEqual(r.sitemaps, undefined, "flat urlset must not carry sitemaps field");
});

test("parseSitemapXml returns error for non-XML", async (t) => {
  const r = callFn("parseSitemapXml", [JSON.stringify("<html><body>Not XML</body></html>")]);
  assert.ok(r.error, "should have error field");
});

test("parseSitemapXml handles URLs with CDATA", async (t) => {
  const r = callFn("parseSitemapXml", [
    JSON.stringify('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc><![CDATA[https://example.com/page]]></loc></url>\n</urlset>')
  ]);
  assert.deepStrictEqual(r, { urls: ["https://example.com/page"] });
});

// ═══════════════════════════════════════════
// matchesPagePattern tests (exclude_patterns)
// ═══════════════════════════════════════════

test("matchesPagePattern exists in source", async (t) => {
  assert.ok(extractFn("matchesPagePattern"), "matchesPagePattern must exist");
});

test("matchesPagePattern exact-glob excludes references path", async (t) => {
  const r = callFn("matchesPagePattern", [
    JSON.stringify("exact:/docs/references/**"),
    JSON.stringify("https://posthog.com/docs/references/posthog-js")
  ]);
  assert.strictEqual(r, true);
});

test("matchesPagePattern exact-glob keeps non-references path", async (t) => {
  const r = callFn("matchesPagePattern", [
    JSON.stringify("exact:/docs/references/**"),
    JSON.stringify("https://posthog.com/docs/cdp/overview")
  ]);
  assert.strictEqual(r, false);
});

test("matchesPagePattern exact-glob excludes DEEP multi-level references path", async (t) => {
  // Regression for glob double-replacement bug: `**` must compile to `.*`
  // (any depth), not `.[^/]*` (single segment). A deep path with multiple
  // slash-separated segments after /docs/references/ must still match.
  const r = callFn("matchesPagePattern", [
    JSON.stringify("exact:/docs/references/**"),
    JSON.stringify("https://posthog.com/docs/references/posthog-js/types/ActionStepType")
  ]);
  assert.strictEqual(r, true);
});

test("matchesPagePattern regex anchored to path", async (t) => {
  const r = callFn("matchesPagePattern", [
    JSON.stringify("regex:^/docs/v\\d+/.*"),
    JSON.stringify("https://posthog.com/docs/v1/migration")
  ]);
  assert.strictEqual(r, true);
});

test("matchesPagePattern regex anchored to full URL", async (t) => {
  const r = callFn("matchesPagePattern", [
    JSON.stringify("regex:^https://posthog\\.com/blog/"),
    JSON.stringify("https://posthog.com/blog/changelog")
  ]);
  assert.strictEqual(r, true);
});

test("matchesPagePattern exact no-wildcard matches full URL", async (t) => {
  const r = callFn("matchesPagePattern", [
    JSON.stringify("exact:https://posthog.com/docs/handbook"),
    JSON.stringify("https://posthog.com/docs/handbook")
  ]);
  assert.strictEqual(r, true);
});

// ═══════════════════════════════════════════
// autoGroupSitemapUrls tests (T6.1)
// ═══════════════════════════════════════════

test("autoGroupSitemapUrls exists in source", async (t) => {
  assert.ok(extractFn("autoGroupSitemapUrls"), "autoGroupSitemapUrls must exist");
});

test("autoGroupSitemapUrls groups URLs by first path segment", async (t) => {
  const r = callFn("autoGroupSitemapUrls", [
    JSON.stringify(["https://example.com/cat-a/page1", "https://example.com/cat-a/page2", "https://example.com/cat-b/page3"]),
    JSON.stringify({ domain: "example.com", structure: { pages: [{ id: "doc", url_pattern: "/:rest*", page_pattern: ["regex:.*"] }] } })
  ], ["pagePatternMatches"]);
  assert.ok(Array.isArray(r), "should return array");
  assert.ok(r.length > 0, "should contain pages");
  const dirs = r.map(p => p.target_directory);
  assert.ok(dirs.includes("cat-a"), "should include cat-a");
  assert.ok(dirs.includes("cat-b"), "should include cat-b");
  // Verify structure of each entry
  for (const entry of r) {
    assert.ok(entry.url, "must have url");
    assert.ok(entry.title, "must have title");
    assert.ok(entry.target_directory, "must have target_directory");
    assert.ok(entry.target_filename.endsWith(".md"), "target_filename must end with .md");
    assert.ok(entry.assigned_category, "must have assigned_category");
  }
});

// ═══════════════════════════════════════════
// buildSitemapDiscoverySummary tests (T6.1)
// ═══════════════════════════════════════════

test("buildSitemapDiscoverySummary exists in source", async (t) => {
  assert.ok(extractFn("buildSitemapDiscoverySummary"), "buildSitemapDiscoverySummary must exist");
});

test("buildSitemapDiscoverySummary produces correct structure", async (t) => {
  const pages = [
    { url: "https://x.com/cat-a/p1", title: "p1", target_directory: "cat-a", target_filename: "p1.md", assigned_category: "Cat A", page_type: "doc" },
    { url: "https://x.com/cat-a/p2", title: "p2", target_directory: "cat-a", target_filename: "p2.md", assigned_category: "Cat A", page_type: "doc" },
    { url: "https://x.com/cat-b/p3", title: "p3", target_directory: "cat-b", target_filename: "p3.md", assigned_category: "Cat B", page_type: "doc" },
  ];
  const r = callFn("buildSitemapDiscoverySummary", [
    JSON.stringify("example.com"),
    JSON.stringify("Example Docs"),
    JSON.stringify(pages),
    JSON.stringify("/tmp/test-output")
  ]);
  assert.strictEqual(r.discovery_method, "sitemap");
  assert.strictEqual(r.domain, "example.com");
  assert.strictEqual(r.total_pages, 3);
  assert.strictEqual(r.categories.length, 2);
  assert.ok(r.manifest_path, "manifest_path should not be null");
  assert.ok(r.estimated_time_minutes >= 1);
  // Verify caveats
  assert.ok(r.caveats.length > 0, "should have caveats");
  assert.ok(r.caveats[0].includes("sitemap"), "caveats should mention sitemap");
});

// ═══════════════════════════════════════════
// runCrawlSitemapDiscovery flow tests (T7.1)
// ═══════════════════════════════════════════

test("runCrawlSitemapDiscovery exists in source", async (t) => {
  assert.ok(extractFn("runCrawlSitemapDiscovery"), "runCrawlSitemapDiscovery must exist");
});

test("runCrawlSitemapDiscovery has handoff for unreachable sitemap", async (t) => {
  // Structural: verify error-handling code exists
  const body = extractFn("runCrawlSitemapDiscovery");
  assert.ok(body.includes("sitemap_unreachable"), "must have sitemap_unreachable handoff");
  assert.ok(body.includes("sitemap_unreachable"), "must handle fetch failure");
});

test("runCrawlSitemapDiscovery has handoff for parse error", async (t) => {
  const body = extractFn("runCrawlSitemapDiscovery");
  assert.ok(body.includes("sitemap_parse_error"), "must have sitemap_parse_error handoff");
});

test("runCrawlSitemapDiscovery iterates sub-sitemaps instead of handoff for index", async (t) => {
  const body = extractFn("runCrawlSitemapDiscovery");
  assert.ok(!body.includes("sitemap_index_unsupported"), "must NOT handoff on sitemap index anymore");
  assert.ok(body.includes("parsed.sitemaps"), "must iterate parsed.sitemaps");
  // Set dedup now lives inside resolveSitemapIndex (extracted for unit testing);
  // cross-sitemap dedup behavior is covered by the behavioral test
  // "resolveSitemapIndex: cross-sitemap deduplication via Set".
  assert.ok(body.includes("resolveSitemapIndex("), "must delegate sub-sitemap iteration+dedup to resolveSitemapIndex");
  assert.ok(body.includes("sitemap_all_subs_failed"), "must handoff when ALL sub-sitemaps fail");
});

test("runCrawlSitemapDiscovery tracks sub-sitemap partial failures", async (t) => {
  const body = extractFn("runCrawlSitemapDiscovery");
  assert.ok(body.includes("subSitemapErrors"), "must track failures via subSitemapErrors array");
  assert.ok(body.includes("Sub-sitemap"), "warnings/caveats must reference Sub-sitemap failures");
  assert.ok(body.includes("partial_success"), "must emit partial_success when some sub-sitemaps fail but URLs remain");
});

test("runCrawlSitemapDiscovery applies exclude_patterns after page_pattern include", async (t) => {
  const body = extractFn("runCrawlSitemapDiscovery");
  assert.ok(body.includes("exclude_patterns"), "must read discovery.exclude_patterns");
  assert.ok(body.includes("matchesPagePattern"), "must use matchesPagePattern for exclude filtering");
  assert.ok(body.includes("finalUrls"), "must produce finalUrls after include+exclude stages");
});

test("runCrawlSitemapDiscovery has handoff for zero pattern match", async (t) => {
  const body = extractFn("runCrawlSitemapDiscovery");
  assert.ok(body.includes("sitemap_no_pattern_match"), "must have sitemap_no_pattern_match handoff");
});

test("runCrawlSitemapDiscovery uses curl for sitemap fetch", async (t) => {
  const body = extractFn("runCrawlSitemapDiscovery");
  // Must use curl (not scrapling) for XML sitemap
  assert.ok(body.includes('spawnSync("curl"'), "must use curl for sitemap fetch");
  assert.ok(body.includes('"-sL"'), "must use -sL curl flags");
});

// ═══════════════════════════════════════════
// resolveSitemapIndex behavioral tests (partial-failure coverage)
// Injects a fake fetcher; no network. Covers spec scenarios:
//   one-sub-sitemap-fails-others-succeed / all-sub-sitemaps-fail /
//   cross-sitemap-deduplication / parse-error / nested-index.
// ═══════════════════════════════════════════

function __urlset(urls) {
  return '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    urls.map(function (u) { return '<url><loc>' + u + '</loc></url>'; }).join('') +
    '</urlset>';
}

test("resolveSitemapIndex exists in source", async (t) => {
  assert.ok(extractFn("resolveSitemapIndex"), "resolveSitemapIndex must exist");
});

test("resolveSitemapIndex: one sub fails (404), others succeed -> merges ok urls + 1 error", async (t) => {
  const r = callResolveSitemapIndex(
    ["https://x/sitemap-0.xml", "https://x/sitemap-1.xml"],
    {
      "https://x/sitemap-0.xml": { ok: true, httpCode: 200, content: __urlset(["https://x/a", "https://x/b"]) },
      "https://x/sitemap-1.xml": { ok: false, httpCode: 404, content: "" }
    }
  );
  assert.deepStrictEqual(r.urls, ["https://x/a", "https://x/b"]);
  assert.strictEqual(r.errors.length, 1);
  assert.strictEqual(r.errors[0].url, "https://x/sitemap-1.xml");
  assert.ok(r.errors[0].reason.startsWith("HTTP "), "reason must start with HTTP: " + r.errors[0].reason);
});

test("resolveSitemapIndex: all sub-sitemaps fail -> empty urls + all errors", async (t) => {
  const r = callResolveSitemapIndex(
    ["https://x/sitemap-0.xml", "https://x/sitemap-1.xml"],
    {
      "https://x/sitemap-0.xml": { ok: false, httpCode: 500, content: "" },
      "https://x/sitemap-1.xml": { ok: false, httpCode: 404, content: "" }
    }
  );
  assert.deepStrictEqual(r.urls, []);
  assert.strictEqual(r.errors.length, 2);
});

test("resolveSitemapIndex: cross-sitemap deduplication via Set", async (t) => {
  const r = callResolveSitemapIndex(
    ["https://x/sitemap-0.xml", "https://x/sitemap-1.xml"],
    {
      "https://x/sitemap-0.xml": { ok: true, httpCode: 200, content: __urlset(["https://x/a", "https://x/b"]) },
      "https://x/sitemap-1.xml": { ok: true, httpCode: 200, content: __urlset(["https://x/b", "https://x/c"]) }
    }
  );
  assert.deepStrictEqual(r.urls, ["https://x/a", "https://x/b", "https://x/c"]);
});

test("resolveSitemapIndex: parse error -> error with parse_error prefix", async (t) => {
  const r = callResolveSitemapIndex(
    ["https://x/sitemap-0.xml"],
    { "https://x/sitemap-0.xml": { ok: true, httpCode: 200, content: "this is not xml <<<" } }
  );
  assert.deepStrictEqual(r.urls, []);
  assert.strictEqual(r.errors.length, 1);
  assert.ok(r.errors[0].reason.startsWith("parse_error"), "reason must start with parse_error: " + r.errors[0].reason);
});

test("resolveSitemapIndex: nested index -> nested_index_unsupported", async (t) => {
  const r = callResolveSitemapIndex(
    ["https://x/sitemap-0.xml"],
    { "https://x/sitemap-0.xml": { ok: true, httpCode: 200, content: '<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://x/deep.xml</loc></sitemap></sitemapindex>' } }
  );
  assert.deepStrictEqual(r.urls, []);
  assert.strictEqual(r.errors.length, 1);
  assert.strictEqual(r.errors[0].reason, "nested_index_unsupported");
});
// ═══════════════════════════════════════════
// runCrawlSitemapExtraction flow tests (T8.1)
// ═══════════════════════════════════════════

test("runCrawlSitemapExtraction exists in source", async (t) => {
  assert.ok(extractFn("runCrawlSitemapExtraction"), "runCrawlSitemapExtraction must exist");
});

test("runCrawlSitemapExtraction reads from page_manifest.json fallback", async (t) => {
  const body = extractFn("runCrawlSitemapExtraction");
  assert.ok(body.includes("page_manifest.json"), "must read from page_manifest.json");
});

test("runCrawlSitemapExtraction applies maxPages limit", async (t) => {
  const body = extractFn("runCrawlSitemapExtraction");
  assert.ok(body.includes("Math.min(maxPages"), "must apply maxPages limit");
});

test("runCrawlSitemapExtraction has manifest missing error", async (t) => {
  const body = extractFn("runCrawlSitemapExtraction");
  assert.ok(body.includes("Manifest not found"), "must handle missing manifest");
});

test("runCrawlSitemapExtraction does NOT contain BFS diffusion", async (t) => {
  const body = extractFn("runCrawlSitemapExtraction");
  // Must NOT call collectLinksFromHtml (BFS diffusion; bounded_by.links_to ok)
  assert.ok(!body.includes("collectLinksFromHtml"), "must not call collectLinksFromHtml (BFS diffusion)");
});
