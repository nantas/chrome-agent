import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();
const cliJs = path.join(repoRoot, "scripts", "chrome-agent-cli.mjs");
const source = fs.readFileSync(cliJs, "utf8");

test("runCrawlScrapling has local pages binding", async (t) => {
  // Find the function start
  const fnStart = source.indexOf("async function runCrawlScrapling(");
  assert.ok(fnStart !== -1, "runCrawlScrapling function must exist");

  // Find the opening brace after signature
  const openBrace = source.indexOf("{", fnStart);
  assert.ok(openBrace !== -1, "function body must have opening brace");

  // Extract the first ~20 lines of function body (enough for the binding + opts destructure)
  const bodyStart = openBrace + 1;
  const bodySlice = source.slice(bodyStart, bodyStart + 8000);

  // The fix: const pages = doc?.structure?.pages ?? [];
  // Must appear BEFORE any pages.find() call
  const pagesBinding = bodySlice.match(/const pages = doc\?\.structure\?\.pages \?\? \[\]/);
  assert.ok(pagesBinding !== null, "runCrawlScrapling must have local `const pages = doc?.structure?.pages ?? []` binding");

  // Verify pages.find() calls exist in the function (proving they're needed)
  const pagesFindMatch = bodySlice.match(/pages\.find\(/);
  assert.ok(pagesFindMatch !== null, "runCrawlScrapling must contain pages.find() calls");

  // Verify the binding comes before the first pages.find() call
  const bindingIndex = bodySlice.indexOf("const pages = doc?.structure?.pages ?? []");
  const findIndex = bodySlice.indexOf("pages.find(");
  assert.ok(bindingIndex < findIndex, "pages binding must appear before first pages.find() call");
});

test("runCrawlScrapling does not use typeof guard as crutch", async (t) => {
  // Anti-pattern: typeof pages !== 'undefined' (masking the root cause)
  const fnStart = source.indexOf("async function runCrawlScrapling(");
  const openBrace = source.indexOf("{", fnStart);
  const bodySlice = source.slice(openBrace + 1, openBrace + 8000);

  assert.ok(
    !bodySlice.includes("typeof pages !== 'undefined'"),
    "Must NOT use typeof pages guard (anti-pattern per spec)"
  );
  assert.ok(
    !bodySlice.includes("globalThis.pages"),
    "Must NOT use globalThis.pages (anti-pattern per spec)"
  );
});
