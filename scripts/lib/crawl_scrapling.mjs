import path from "node:path";

/**
 * Scrapling crawl orchestrator — extracted from the CLI god module.
 *
 * Pure structural extraction: receives all cli.mjs helpers via an injected
 * `api` bundle (api.fs + named helper functions) to avoid circular imports
 * and to make traversal/manifest/handoff logic unit-testable with stubs.
 * Only runCrawlScrapling lives here; all helpers stay in cli.mjs.
 *
 * Spec: extract-crawl-scrapling-orchestrator /
 *       crawl-scrapling-orchestrator-is-a-seam-module.
 */

export async function runCrawlScrapling(ctx, opts, api) {
  const { repoRoot, repoRef, resolutionMode, runDir, reportPath, manifestPath, emitReport, targetUrl, strategy, doc, startPage, matchingPage, entryPoints } = ctx;
  const {
    maxPages = null,
    concurrency = 5,
    fromManifest = null,
    yes: yesFlag = false,
    excludeCategory = [],
    phase = null,
    reFetch = false,
    keepHtml = false,
    markdown = true,
    merge = false,
    parallel = false,
    workers = 5,
  } = opts;

const pages = doc?.structure?.pages ?? [];
let events = [];
let fallbackReason = null;
const preflight = api.cache.runScraplingPreflight(repoRoot, true);
if (!preflight.ok) {
  if (emitReport) {
    const report = api.report.buildCrawlReport({
      targetUrl,
      repoRef,
      resolutionMode,
      strategy,
      events: ["Scrapling CLI preflight failed before crawl traversal."],
      result: "failure",
    });
    api.report.writeTextFile(reportPath, report);
  }
  const artifacts = [];
  if (emitReport) {
    artifacts.push(api.report.absoluteArtifact(reportPath, "durable", "Crawl preflight report"));
  }
  // Handoff: Scrapling preflight failure is internal
  const handoff = api.handoff.generateHandoff({ command: "crawl", target: targetUrl, repoRef, runDir, error: { reason: "preflight_failure", summary: `Scrapling CLI preflight failed (${preflight.status ?? "unknown"}).`, stderr: `${preflight.stdout ?? ""}${preflight.stderr ?? ""}`.trim() }, strategy });
  return api.report.makeResult(
    "crawl",
    targetUrl,
    repoRef,
    "Crawl stopped because Scrapling CLI preflight failed.",
    artifacts,
    `The problem must be resolved in the chrome-agent repository. See handoff document at ${handoff.path}.`,
    "failure",
    {
      workflow: "content_retrieval",
      engine_path: `strategy_registry -> scrapling_preflight:${preflight.status ?? "unavailable"} -> blocked`,
      handoff_path: handoff.path,
      handoff_summary: handoff.summary,
    },
  );
}

const queue = [];
// --- from-manifest: seed queue from existing manifest ---
if (fromManifest && api.fs.existsSync(fromManifest)) {
  try {
    const loadedManifest = JSON.parse(api.fs.readFileSync(fromManifest, "utf8"));
    const loadedVisited = loadedManifest.visited ?? [];
    for (const url of loadedVisited) {
      const page = pages.find((p) => api.traversal.pagePatternMatches(p, url));
      if (page) {
        queue.push({ url, page, paginationIndex: 1 });
      }
    }
    api.log.info(`Loaded ${queue.length} URLs from manifest for Scrapling traversal`);
  } catch (err) {
    console.warn(`Failed to load manifest: ${err.message}`);
  }
}
if (queue.length === 0) {
  const startUrl = matchingPage && matchingPage.id === startPage.id ? targetUrl : startPage.url_example;
  queue.push({ url: startUrl, page: startPage, paginationIndex: 1 });
}
const visited = new Set();
const artifacts = [];
// events already declared above (let events)
let failures = 0;

while (queue.length > 0 && (maxPages == null || visited.size < maxPages)) {
  const item = queue.shift();
  if (!item || visited.has(item.url)) {
    continue;
  }
  // --exclude-category filtering for Scrapling path (match by page id/label)
  if (excludeCategory.length > 0 && item.page) {
    const pageIdLower = (item.page.id || "").toLowerCase();
    const pageLabelLower = (item.page.label || "").toLowerCase();
    const isExcluded = excludeCategory.some(
      (cat) => cat.toLowerCase() === pageIdLower || cat.toLowerCase() === pageLabelLower,
    );
    if (isExcluded) {
      events.push(`Skipped ${item.url} — excluded category: ${item.page.id}`);
      continue;
    }
  }
  visited.add(item.url);
  const fetcher = api.engine.selectFetcher(strategy, item.page);
  const pageSlug = `${String(visited.size).padStart(2, "0")}-${item.page.id}`;
  const outputPath = path.join(runDir, `${pageSlug}.html`);
  const fetchResult = api.engine.runEngineFetch(repoRoot, fetcher, item.url, outputPath);

  if (fetchResult.ok) {
    artifacts.push(api.report.absoluteArtifact(outputPath, "disposable", `Crawled page ${item.page.id}`));
    events.push(`Fetched ${item.url} via ${fetcher} for page ${item.page.id}.`);
  } else {
    failures += 1;
    const errorPath = path.join(runDir, `${pageSlug}.stderr.log`);
    api.report.writeTextFile(errorPath, fetchResult.stderr || "Scrapling crawl fetch failed.");
    artifacts.push(api.report.absoluteArtifact(errorPath, "disposable", `Crawl error for ${item.page.id}`));
    events.push(`Failed ${item.url} via ${fetcher} for page ${item.page.id}.`);
    continue;
  }

  for (const link of item.page.links_to ?? []) {
    const nextPage = pages.find((page) => page.id === link.target);
    if (!nextPage) {
      events.push(`Skipped undeclared target page ${link.target} from ${item.page.id}.`);
      continue;
    }
    const discovered = api.traversal.collectLinksFromHtml(outputPath, item.url, link.selector);
    for (const url of discovered) {
      if (api.traversal.pagePatternMatches(nextPage, url) && !visited.has(url)) {
        queue.push({ url, page: nextPage, paginationIndex: 1 });
      }
    }
    if (discovered.length === 0) {
      events.push(`No bounded links matched selector ${link.selector} from ${item.page.id}.`);
    }
  }

  if (item.page.pagination && item.page.pagination !== "none" && (maxPages == null || queue.length + visited.size < maxPages)) {
    if (item.page.pagination.mechanism === "url_parameter") {
      const nextPageNumber = item.paginationIndex + 1;
      const nextUrl = api.traversal.nextPaginationUrl(item.url, item.page.pagination, nextPageNumber);
      if (nextUrl && !visited.has(nextUrl) && (maxPages == null || queue.length + visited.size < maxPages)) {
        queue.push({ url: nextUrl, page: item.page, paginationIndex: nextPageNumber });
        events.push(`Queued bounded pagination URL ${nextUrl} from ${item.page.id}.`);
      }
    } else {
      events.push(`Pagination mechanism ${item.page.pagination.mechanism} is bounded but not auto-followed in this implementation.`);
    }
  }
}

const manifest = {
  command: "crawl",
  target: targetUrl,
  repo_ref: repoRef,
  resolution_mode: resolutionMode,
  strategy_file: path.relative(repoRoot, strategy.path),
  visited: [...visited],
  max_pages: maxPages,
  start_page: startPage.id,
  bounded_by: {
    entry_points: entryPoints,
    links_to: true,
    pagination: true,
    unrestricted_recursive_spider: false,
  },
};

// Determine domain for cache operations
const crawlDomain = new URL(targetUrl).hostname;
let phase2Result = null;

// --- Scrapling --phase fetch: save visited pages to cache, skip conversion ---
if (phase === "fetch" && visited.size > 0) {
  const domainCacheDir = api.cache.scraplingCacheDir(repoRoot, crawlDomain);
  api.cache.ensureDir(domainCacheDir);
  let cacheWriteCount = 0;
  let cacheSkipCount = 0;
  for (const url of visited) {
    const slug = api.cache.scraplingSlugFromUrl(url);
    if (!reFetch && api.cache.isScraplingCached(repoRoot, crawlDomain, slug)) {
      cacheSkipCount++;
      events.push(`Skipping cache write for ${url} (already cached)`);
      continue;
    }
    // Find the fetched HTML file for this URL
    let htmlContent = null;
    for (const f of api.fs.readdirSync(runDir)) {
      if (f.endsWith(".html")) {
        const fpath = path.join(runDir, f);
        const content = api.fs.readFileSync(fpath, "utf8");
        if (content.includes(url) || f.includes(slug)) {
          htmlContent = content;
          break;
        }
      }
    }
    if (htmlContent) {
      api.cache.saveScraplingCache(repoRoot, crawlDomain, slug, htmlContent, {
        url, fetcher: "scrapling",
      });
      cacheWriteCount++;
      events.push(`Cached ${url} -> .cache/scrapling/${crawlDomain}/${slug}.html`);
    }
  }
  console.log(`Scrapling fetch phase: ${cacheWriteCount} cached, ${cacheSkipCount} skipped`);
}

// --- Scrapling --phase convert: read from cache and convert ---
if (phase === "convert" && fromManifest) {
  const manifestData = JSON.parse(api.fs.readFileSync(fromManifest, "utf8"));
  const urls = manifestData.visited || [];
  let convertOk = 0;
  let convertFail = 0;
  for (const url of urls) {
    const slug = api.cache.scraplingSlugFromUrl(url);
    const cached = api.cache.loadScraplingCache(repoRoot, crawlDomain, slug);
    if (!cached) {
      events.push(`Cache miss for ${url} — skipping`);
      convertFail++;
      continue;
    }
    const tmpHtmlPath = path.join(runDir, `_cached_${slug}.html`);
    api.report.writeTextFile(tmpHtmlPath, cached.html);
    const mdPath = api.convert.urlToStructuredPath(url, runDir);
    const cachedArgs = api.cache.buildScraplingExtractionArgs(strategy, "get");
    const scraplingResult = api.engine.runEngineFetch(repoRoot, "get", `file://${tmpHtmlPath}`, mdPath, cachedArgs);
    if (scraplingResult.ok) {
      convertOk++;
      events.push(`Converted cached ${url} to Markdown`);
    } else {
      convertFail++;
      events.push(`Failed to convert cached ${url}`);
    }
    try { api.fs.unlinkSync(tmpHtmlPath); } catch {}
  }
  phase2Result = {
    successful: urls.slice(0, convertOk).map((url, i) => ({ url })),
    failed: urls.slice(0, convertFail).map((url, i) => ({ url, error: "conversion_failed" })),
    mergedPath: null,
  };
  console.log(`Scrapling convert phase: ${convertOk} converted, ${convertFail} failed`);
}

// Phase 2: Markdown conversion (standard path, not --phase fetch/convert)
let extractionMethod = "scrapling";
let parallelFallbackReason = null;

if (markdown && visited.size > 0 && phase !== "fetch" && phase2Result === null) {
  if (parallel) {
    const poolOutcome = await api.pool.withObscuraPool(repoRoot, [...visited], workers, 15, async (fetchResults) => {
      const prefetchedHtml = {};
      for (const r of fetchResults) {
        if (r.html) {
          prefetchedHtml[r.url] = r.html;
        }
      }
      return api.convert.convertTraversalToMarkdown(repoRoot, runDir, manifest, {
        fetcherFn: (url) => {
          const page = pages.find((p) => api.traversal.pagePatternMatches(p, url));
          return api.engine.selectFetcher(strategy, page);
        },
        strategy,
        concurrency,
        merge,
        cleanupHtml: !keepHtml,
        outputName: "crawl-output",
        prefetchedHtml,
      });
    });
    phase2Result = poolOutcome.result;
    extractionMethod = poolOutcome.extractionMethod;
    parallelFallbackReason = poolOutcome.fallbackReason;
  }

  if (!phase2Result) {
    phase2Result = api.convert.convertTraversalToMarkdown(repoRoot, runDir, manifest, {
      fetcherFn: (url) => {
        const page = pages.find((p) => api.traversal.pagePatternMatches(p, url));
        return api.engine.selectFetcher(strategy, page);
      },
      strategy,
      concurrency,
      merge,
      cleanupHtml: !keepHtml,
      outputName: "crawl-output",
    });
  }

  manifest.phase2 = {
    successful_count: phase2Result.successful.length,
    failed_count: phase2Result.failed.length,
    failed_urls: phase2Result.failed.map((f) => f.url),
    merged_path: phase2Result.mergedPath,
  };
}

api.report.writeTextFile(manifestPath, JSON.stringify(manifest, null, 2));

// Rebuild artifacts based on output mode
const finalArtifacts = [api.report.absoluteArtifact(manifestPath, "disposable", "Crawl manifest")];

if (markdown) {
  finalArtifacts.push(...api.convert.collectMarkdownArtifacts(runDir));
  // Ensure merged file gets a descriptive label if found by api.convert.collectMarkdownArtifacts
  for (const { url } of (phase2Result?.failed ?? [])) {
    const idx = manifest.visited.indexOf(url);
    if (idx >= 0) {
      const errorPath = path.join(runDir, `${String(idx + 1).padStart(2, "0")}.md.error.log`);
      if (api.fs.existsSync(errorPath)) {
        finalArtifacts.push(api.report.absoluteArtifact(errorPath, "disposable", `Conversion error for ${url}`));
      }
    }
  }
} else {
  for (const file of api.fs.readdirSync(runDir)) {
    if (file.endsWith(".html")) {
      finalArtifacts.push(api.report.absoluteArtifact(path.join(runDir, file), "disposable", `Crawled page ${file}`));
    }
  }
}

const traversalOk = visited.size > 0 && failures === 0;
const conversionOk = !markdown || (phase2Result && phase2Result.failed.length === 0);
const resultState =
  traversalOk && conversionOk ? "success" : visited.size > failures ? "partial_success" : "failure";

const finalExtractionMethod = extractionMethod;
const finalFallbackReason = parallelFallbackReason ?? fallbackReason;

if (emitReport) {
  const report = api.report.buildCrawlReport({
    targetUrl,
    repoRef,
    resolutionMode,
    strategy,
    events,
    result: resultState,
    phase2: markdown && phase2Result
      ? {
          successful: phase2Result.successful.length,
          failed: phase2Result.failed.length,
          mergedPath: phase2Result.mergedPath,
        }
      : null,
    extractionMethod: finalExtractionMethod,
    fallbackReason: finalFallbackReason,
  });
  api.report.writeTextFile(reportPath, report);
  finalArtifacts.unshift(api.report.absoluteArtifact(reportPath, "durable", "Crawl report"));
}

const summary =
  resultState === "success"
    ? `Crawl completed within declared strategy boundaries and visited ${visited.size} page(s)${markdown ? `; ${phase2Result.successful.length} converted to Markdown` : ""}.`
    : resultState === "partial_success"
      ? `Crawl visited ${visited.size} page(s)${markdown ? `; ${phase2Result.successful.length} converted, ${phase2Result.failed.length} failed` : ` with ${failures} fetch failure(s)`}.`
      : "Crawl failed before any page completed successfully.";
const nextAction =
  resultState === "failure"
    ? "Review the crawl report, strategy selectors, or authentication requirements before retrying."
    : "Inspect the crawl outputs. Extend the site strategy if more bounded traversal is needed.";

return api.report.makeResult("crawl", targetUrl, repoRef, summary, finalArtifacts, nextAction, resultState, {
  workflow: "content_retrieval",
  engine_path: `strategy_registry -> bounded_crawl -> scrapling_preflight:${preflight.status ?? "unknown"}${markdown ? ` -> markdown_conversion(${phase2Result?.successful.length ?? 0}/${visited.size})` : ""}`,
  extraction_method: finalExtractionMethod,
  ...(finalFallbackReason ? { fallback_reason: finalFallbackReason } : {}),
  confirmation_bypassed: yesFlag,
});
}

