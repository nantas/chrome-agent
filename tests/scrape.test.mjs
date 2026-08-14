/** Behavioral injection + static discipline test for the extracted scrape orchestrator.
 *
 * Spec: extract-scrape-orchestrator / scrape-orchestrator-is-a-seam-module.
 *
 * Before extraction, runScrape was inline in cli.mjs and untestable without
 * spawning Chrome. Now it accepts an `api` bundle of all its cli.mjs helpers
 * (grouped concern objects) — this test calls it with a stub `api` and asserts
 * the core control-flow paths: preflight failure, BFS traversal, markdown/parallel
 * branches, partial_success downgrade. Plus static discipline: no bare-identifier
 * calls, no flat api.<helper> calls, no circular import.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import { runScrape } from "../scripts/lib/scrape.mjs";

// ── Fixtures ────────────────────────────────────────────────────────────────

function baseCtx(overrides = {}) {
  return {
    repoRoot: "/repo",
    repoRef: "repo://chrome-agent",
    resolutionMode: "resolved",
    targetUrl: "https://example.com/seed",
    runDir: "/run",
    reportPath: "/run/scrape-report.md",
    manifestPath: "/run/manifest.json",
    emitReport: true,
    ...overrides,
  };
}

/** Build a stub `api` as named concern objects (matches scrapeApi bundle shape
 *  in cli.mjs). Pure helpers use lightweight real-ish implementations;
 *  side-effecting helpers are stubbed. `groupOverrides` = {group: {helper: fn}}. */
function stubApi(groupOverrides = {}) {
  const written = {};
  const api = {
    fs: {
      existsSync: (p) => p in written,
      readdirSync: () => [],
      readFileSync: (p) => written[p] ?? "",
    },
    log: console,
    report: {
      makeResult: (command, target, repoRef, summary, artifacts, nextAction, result = "success", extra = {}) =>
        ({ result, command, target, summary, artifacts, next_action: nextAction, ...extra }),
      absoluteArtifact: (filePath, lifecycle, description) => ({ path: filePath, lifecycle, description }),
      writeTextFile: (p, content) => { written[p] = content; },
      buildScrapeReport: ({ events, result }) => `# scrape report\nresult: ${result}\n${(events || []).join("\n")}`,
    },
    handoff: {
      generateHandoff: () => ({ path: "/run/handoff.md", summary: "stub-handoff" }),
      internalFailure: ({ command, reason, enginePath, resultMsg, artifacts = [] }) => ({
        result: "failure",
        command,
        reason,
        engine_path: enginePath,
        summary: resultMsg,
        artifacts,
        handoff_path: "/run/handoff.md",
        handoff_summary: "stub-handoff",
      }),
    },
    engine: {
      runScraplingPreflight: () => ({ ok: true, status: "available", stdout: "", stderr: "" }),
      runEngineFetch: () => ({ ok: true, stderr: "" }),
    },
    pool: {
      runObscuraPreflight: () => ({ ok: false }),
      withObscuraPool: async (_repoRoot, _urls, _workers, _timeout, fn) => {
        // Stub: call fn with empty fetch results to exercise the parallel branch.
        const result = await fn([]);
        return { result, extractionMethod: "obscura-serve-pool", fallbackReason: null };
      },
    },
    traversal: {
      extractAllLinks: () => [],
    },
    convert: {
      convertTraversalToMarkdown: () => ({ successful: [], failed: [], mergedPath: null }),
      collectMarkdownArtifacts: () => [],
    },
  };
  for (const [group, helperOverrides] of Object.entries(groupOverrides)) {
    if (api[group]) Object.assign(api[group], helperOverrides);
  }
  // Expose the in-memory store so tests can assert what was written.
  api.__written = written;
  return api;
}

// ── Behavior tests ──────────────────────────────────────────────────────────

test("preflight failure delegates to api.handoff.internalFailure and emits handoff_path", async () => {
  const api = stubApi({
    engine: { runScraplingPreflight: () => ({ ok: false, status: "unavailable", stdout: "", stderr: "boom" }) },
  });
  const ctx = baseCtx();
  const result = await runScrape(ctx, { markdown: false }, api);

  assert.equal(result.result, "failure");
  assert.equal(result.command, "scrape");
  assert.match(result.summary, /preflight failed/i);
  assert.equal(result.handoff_path, "/run/handoff.md");
  // internalFailure was the builder: a report was written via api.report.writeTextFile
  assert.ok(api.__written[ctx.reportPath].includes("result: failure"));
});

test("minimal BFS traversal visits the start url and writes a manifest", async () => {
  const api = stubApi(); // preflight ok, fetch ok, extractAllLinks -> []
  const ctx = baseCtx();
  const result = await runScrape(ctx, { markdown: false }, api);

  assert.equal(result.result, "success");
  const manifest = JSON.parse(api.__written[ctx.manifestPath]);
  assert.deepEqual(manifest.visited, ["https://example.com/seed"]);
  assert.equal(manifest.command, "scrape");
});

test("markdown:true (default) path collects markdown artifacts and does not throw", async () => {
  const mdArtifact = { path: "/run/scrape-output.md", lifecycle: "disposable", description: "merged scrape output" };
  const api = stubApi({
    convert: {
      collectMarkdownArtifacts: () => [mdArtifact],
      convertTraversalToMarkdown: () => ({ successful: [{ url: "https://example.com/seed" }], failed: [], mergedPath: "/run/scrape-output.md" }),
    },
  });
  const ctx = baseCtx();
  const result = await runScrape(ctx, { markdown: true }, api);

  assert.equal(result.result, "success");
  assert.ok(result.artifacts.some((a) => a.path === mdArtifact.path),
    "markdown:true path must include artifacts from api.convert.collectMarkdownArtifacts");
});

test("parallel:true delegates to api.pool.withObscuraPool", async () => {
  let poolCalled = false;
  const api = stubApi({
    pool: {
      withObscuraPool: async (...args) => {
        poolCalled = true;
        const fn = args[args.length - 1];
        const result = await fn([]);
        return { result, extractionMethod: "obscura-serve-pool", fallbackReason: null };
      },
    },
  });
  const ctx = baseCtx();
  await runScrape(ctx, { markdown: true, parallel: true }, api);

  assert.equal(poolCalled, true, "runScrape with parallel:true MUST call api.pool.withObscuraPool");
});

test("all fetch failures downgrade result to failure (zero successes)", async () => {
  const api = stubApi({
    engine: { runEngineFetch: () => ({ ok: false, stderr: "boom" }) },
  });
  const ctx = baseCtx();
  const result = await runScrape(ctx, { markdown: false }, api);

  assert.equal(result.result, "failure"); // zero successes -> failure, not partial
  assert.match(result.summary, /failed before any page completed/i);
});

test("partial_success when traversal has at least one success and one failure", async () => {
  let call = 0;
  const api = stubApi({
    engine: {
      // First fetch succeeds, second fails.
      runEngineFetch: () => (call++ === 0 ? { ok: true, stderr: "" } : { ok: false, stderr: "boom" }),
    },
    traversal: {
      // First success discovers one new link (which then fails).
      extractAllLinks: () => (call === 1 ? ["https://example.com/second"] : []),
    },
  });
  const ctx = baseCtx();
  const result = await runScrape(ctx, { markdown: false }, api);

  assert.equal(result.result, "partial_success");
  assert.match(result.summary, /visited 2 page/);
});

test("BFS discovers and queues new links via api.traversal.extractAllLinks", async () => {
  const fetchedUrls = [];
  let callCount = 0;
  const api = stubApi({
    engine: {
      runEngineFetch: (_repoRoot, _fetcher, url) => {
        fetchedUrls.push(url);
        return { ok: true, stderr: "" };
      },
    },
    traversal: {
      // First fetch discovers one new link, subsequent fetches discover none.
      extractAllLinks: () => (callCount++ === 0 ? ["https://example.com/linked"] : []),
    },
  });
  const ctx = baseCtx();
  const result = await runScrape(ctx, { markdown: false, sameDomain: true }, api);

  assert.equal(result.result, "success");
  assert.ok(fetchedUrls.includes("https://example.com/linked"), "BFS SHALL queue discovered links");
  const manifest = JSON.parse(api.__written[ctx.manifestPath]);
  assert.equal(manifest.visited.length, 2);
});

test("no circular import: module does not import from cli.mjs", async () => {
  const fs = await import("node:fs");
  const src = fs.readFileSync(new URL("../scripts/lib/scrape.mjs", import.meta.url), "utf8");
  const importLines = src.split("\n").filter((l) => l.trim().startsWith("import"));
  const hasCycle = importLines.some((l) => l.includes("chrome-agent-cli"));
  assert.equal(hasCycle, false, "scrape.mjs must not import from cli.mjs (would create a cycle)");
});

// ── Dispatch-site test ──────────────────────────────────────────────────────

test("cli.mjs builds a scrapeApi bundle as named concern objects at dispatch site", async () => {
  const fs = await import("node:fs");
  const cliSrc = fs.readFileSync(new URL("../scripts/chrome-agent-cli.mjs", import.meta.url), "utf8");
  const start = cliSrc.indexOf("scrapeApi = {");
  assert.notEqual(start, -1, "cli.mjs SHALL construct a `scrapeApi` bundle at the scrape dispatch site");
  // find the closing brace of the bundle object
  let i = cliSrc.indexOf("{", start);
  let depth = 0;
  const blockStart = i;
  for (; i < cliSrc.length; i++) {
    const c = cliSrc[i];
    if (c === "{") depth++;
    else if (c === "}") { depth--; if (depth === 0) break; }
  }
  const block = cliSrc.slice(blockStart + 1, i);
  // must declare the canonical concern groups
  for (const group of ["report:", "handoff:", "engine:", "pool:", "traversal:", "convert:"]) {
    assert.ok(block.includes(group), `scrapeApi bundle SHALL include group \`${group.slice(0, -1)}\``);
  }
});

// ── Static discipline: bare-call + flat-call detection ──────────────────────

/** Read the scrapeApi bundle from cli.mjs as a {group: [helper]} map. */
async function readScrapeApiGroups() {
  const fs = await import("node:fs");
  const cliSrc = fs.readFileSync(new URL("../scripts/chrome-agent-cli.mjs", import.meta.url), "utf8");
  const start = cliSrc.indexOf("scrapeApi = {");
  if (start === -1) throw new Error("scrapeApi bundle not found in cli.mjs");
  let i = cliSrc.indexOf("{", start);
  let depth = 0;
  const blockStart = i;
  for (; i < cliSrc.length; i++) {
    const c = cliSrc[i];
    if (c === "{") depth++;
    else if (c === "}") { depth--; if (depth === 0) break; }
  }
  const block = cliSrc.slice(blockStart + 1, i);
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

async function readScrapeApiHelperToGroup() {
  const groups = await readScrapeApiGroups();
  const map = {};
  for (const [g, helpers] of Object.entries(groups)) {
    for (const h of helpers) map[h] = g;
  }
  return map;
}

test("all bundled helpers are called via the api.<group>. prefix (no bare-identifier calls)", async () => {
  const fs = await import("node:fs");
  const helperToGroup = await readScrapeApiHelperToGroup();
  const modSrc = fs.readFileSync(new URL("../scripts/lib/scrape.mjs", import.meta.url), "utf8");
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
    "scrape.mjs must call every bundled helper via `api.<group>.` prefix. " +
    "Bare calls throw ReferenceError at runtime. Violations:\n" +
    bareViolations.map((v) => `  L${v.line}: ${v.key} — ${v.text}`).join("\n"));
});

test("seam surface uses named concern groups (no flat api.<helper> calls to groupable helpers)", async () => {
  const fs = await import("node:fs");
  const helperToGroup = await readScrapeApiHelperToGroup();
  const modSrc = fs.readFileSync(new URL("../scripts/lib/scrape.mjs", import.meta.url), "utf8");

  const flatViolations = [];
  for (const [helper, group] of Object.entries(helperToGroup)) {
    const re = new RegExp("\\bapi\\." + helper.replace(/[.*+?^${}()|[\]\\\\]/g, "\\\\$&") + "(?![A-Za-z0-9_])", "g");
    let m;
    while ((m = re.exec(modSrc)) !== null) {
      flatViolations.push({ helper, shouldUse: `api.${group}.${helper}` });
    }
  }

  assert.deepEqual(flatViolations, [],
    "scrape.mjs must use api.<group>.<helper>, not flat api.<helper>. Violations:\n" +
    flatViolations.map((v) => `  ${v.helper} should be ${v.shouldUse}`).join("\n"));
});
