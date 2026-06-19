// Shared helper: build scrapling CLI extraArgs from a matched strategy.
//
// Spec: openspec/specs (change strategy-selector-passthrough /
//       specs/fetch-strategy-selector/spec.md)
//
// selector-injection-safety (HARD CONSTRAINT):
//   The content selector MUST remain a discrete argv array element. Safety
//   relies entirely on runScraplingFetch()'s spawnSync(argvArray) invocation —
//   the selector is never shell-joined or string-interpolated. Any refactor
//   that collapses this into a shell string will reintroduce an injection
//   vector for selectors containing [, *, ', etc. Do NOT do that.

/**
 * Build the scrapling `extract <fetcher> <url> <output>` extraArgs from a
 * matched strategy.
 *
 * Decision order:
 *   1. mediawiki-api fetcher  → [strategy.path]   (independent of selectors)
 *   2. strategy declares a non-empty extraction.selectors.content
 *                             → ["-s", selector]  (precise extraction)
 *   3. otherwise              → ["--ai-targeted"] (heuristic fallback)
 *
 * @param {object|null|undefined} strategy - matched strategy object
 *   ({ path: string, document: { extraction?: { selectors?: { content?: string } } } })
 *   or null/undefined when no strategy matches the URL.
 * @param {string} fetcher - resolved scrapling fetcher name
 *   ("get" | "fetch" | "stealthy-fetch" | "cloakbrowser" | "mediawiki-api").
 * @returns {string[]} extraArgs to spread into runEngineFetch / runScraplingFetch.
 */
export function buildScraplingExtractionArgs(strategy, fetcher) {
  // (1) MediaWiki API path keeps its existing strategy.path pass-through and is
  //     independent of content selectors (the API returns structured content).
  if (fetcher === "mediawiki-api") {
    return strategy ? [strategy.path] : [];
  }

  // (2) CloakBrowser path: scripts/cloakbrowser_fetcher.py is a separate CLI
  //     that accepts NEITHER -s nor --ai-targeted. The pre-change code hardcoded
  //     ["--ai-targeted"] for every non-mediawiki fetcher, which made every
  //     cloakbrowser fetch fail with `unrecognized arguments: --ai-targeted`
  //     (a pre-existing bug affecting protection_level:high strategies such as
  //     boardgamegeek.com / wiki.supercombo.gg). This helper returns [] instead,
  //     fixing the pre-existing bug: cloakbrowser_fetcher.py needs no extraction
  //     flag (it has its own fetch logic). Selector pass-through for cloakbrowser
  //     is deferred — see design D6 / change strategy-selector-passthrough.
  if (fetcher === "cloakbrowser") {
    return [];
  }

  // (3) Strategy-sourced content selector takes priority over the ai-targeted
  //     heuristic. Applies to scrapling-family fetchers (get / fetch / stealthy-fetch).
  //     Only a non-empty string (after trim) qualifies as declared.
  const selector = strategy?.document?.extraction?.selectors?.content;
  if (typeof selector === "string" && selector.trim() !== "") {
    // Kept as a discrete array element — see injection-safety note at top.
    return ["-s", selector];
  }

  // (3) Deterministic fallback: no usable selector → ai-targeted heuristic.
  //     Backward compatible with pre-change behavior for all strategies that
  //     do not declare extraction.selectors.content.
  return ["--ai-targeted"];
}
