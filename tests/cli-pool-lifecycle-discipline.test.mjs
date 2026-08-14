/** Static discipline check: pool-lifecycle-single-orchestration.
 *
 * Spec: cleanup-cli-and-converter-dead-code / pool-lifecycle-single-orchestration,
 *       scenario all-pool-callers-delegate-to-withObscuraPool.
 *
 * The obscura serve-pool lifecycle (preflight → serve → fetch → stop → fallback)
 * SHALL be owned by a single withObscuraPool helper. startObscuraServe( calls
 * are permitted only inside withObscuraPool's definition, inside runObscuraFetch
 * (single-page fetch, out of scope), or inside the crawl_scrapling.mjs seam via
 * api.pool.withObscuraPool. Inlining the lifecycle in runScrape/runBatch/
 * runCrawlScrapling handler bodies is FORBIDDEN.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

function readLines(p) {
  return fs.readFileSync(new URL(p, import.meta.url), "utf8").split("\n");
}

const CLI = readLines("../scripts/chrome-agent-cli.mjs");
const SEAM = readLines("../scripts/lib/crawl_scrapling.mjs");

/** Find the line range of a top-level function definition (heuristic). */
function fnRange(lines, name) {
  const start = lines.findIndex((l) => new RegExp(`^(async )?function ${name}\\(`).test(l));
  if (start < 0) return null;
  // find closing brace at same or lower indent (top-level)
  let depth = 0;
  for (let i = start; i < lines.length; i++) {
    for (const c of lines[i]) {
      if (c === "{") depth++;
      else if (c === "}") { depth--; if (depth === 0) return [start + 1, i + 1]; }
    }
  }
  return [start + 1, lines.length];
}

test("startObscuraServe is only called inside withObscuraPool, runObscuraFetch, or api.pool — not inlined in handlers", () => {
  const allowedRanges = [];
  for (const name of ["withObscuraPool", "runObscuraFetch"]) {
    const r = fnRange(CLI, name);
    if (r) allowedRanges.push({ file: "cli.mjs", range: r, name });
  }
  const violations = [];

  // cli.mjs: any startObscuraServe( outside allowed ranges (skip the definition)
  CLI.forEach((line, i) => {
    if (!/startObscuraServe\(/.test(line)) return;
    if (/^(async )?function startObscuraServe\(/.test(line)) return; // definition, not a call
    const ln = i + 1;
    const inAllowed = allowedRanges.some((a) => ln >= a.range[0] && ln <= a.range[1]);
    if (!inAllowed) violations.push({ file: "cli.mjs", line: ln, text: line.trim() });
  });

  // crawl_scrapling.mjs: startObscuraServe must be via api.pool (grouped seam),
  // never a bare or flat call. Currently the pool block delegates to
  // api.pool.withObscuraPool, so startObscuraServe should not appear at all
  // outside an api.pool. qualification.
  SEAM.forEach((line, i) => {
    if (!/startObscuraServe\(/.test(line)) return;
    if (/api\.pool\./.test(line)) return; // delegated — ok
    violations.push({ file: "crawl_scrapling.mjs", line: i + 1, text: line.trim() });
  });

  assert.deepEqual(violations, [],
    "obscura serve-pool lifecycle must be owned by withObscuraPool. " +
    "startObscuraServe( may appear only inside withObscuraPool, runObscuraFetch, " +
    "or via api.pool.withObscuraPool in the seam. Spec: pool-lifecycle-single-orchestration. " +
    "Violations:\n" + violations.map((v) => `  ${v.file}@L${v.line}: ${v.text}`).join("\n"));
});
