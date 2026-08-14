import path from "node:path";

/**
 * Scrape orchestrator — extracted from the CLI god module.
 *
 * Pure structural extraction: receives all cli.mjs helpers via an injected
 * `api` bundle (named concern objects: api.fs + api.report + api.handoff +
 * api.engine + api.pool + api.traversal + api.convert) to avoid circular
 * imports and to make BFS traversal / markdown conversion / result synthesis
 * unit-testable with stubs. Only runScrape lives here; all helpers stay in
 * cli.mjs (including scrape-specific extractAllLinks / buildScrapeReport,
 * which reach this module only via the bundle).
 *
 * Spec: extract-scrape-orchestrator / scrape-orchestrator-is-a-seam-module.
 */

export async function runScrape(ctx, opts, api) {
  const { repoRoot, repoRef, resolutionMode, targetUrl, runDir, reportPath, manifestPath, emitReport } = ctx;
  const {
    maxPages = null,
    sameDomain = true,
    matchPattern = null,
    markdown = true,
    merge = false,
    concurrency = 5,
    fetcherOverride = null,
    keepHtml = false,
    parallel = false,
    workers = 5,
  } = opts;

  const preflight = api.engine.runScraplingPreflight(repoRoot, true);
  if (!preflight.ok) {
    if (emitReport) {
      const report = api.report.buildScrapeReport({
        targetUrl,
        repoRef,
        resolutionMode,
        events: ["Scrapling CLI preflight failed before scrape traversal."],
        result: "failure",
      });
      api.report.writeTextFile(reportPath, report);
    }
    const artifacts = [];
    if (emitReport) {
      artifacts.push(api.report.absoluteArtifact(reportPath, "durable", "Scrape preflight report"));
    }
    // Handoff: Scrapling preflight failure is internal — delegate to the builder.
    return api.handoff.internalFailure({
      command: "scrape", target: targetUrl, repoRef, runDir,
      reason: "preflight_failure", summary: `Scrapling CLI preflight failed (${preflight.status ?? "unknown"}).`,
      stderr: `${preflight.stdout ?? ""}${preflight.stderr ?? ""}`.trim(),
      resultMsg: "Scrape stopped because Scrapling CLI preflight failed.",
      enginePath: `scrapling_preflight:${preflight.status ?? "unavailable"} -> blocked`,
      artifacts,
    });
  }

  // Phase 1: Traversal
  const queue = [targetUrl];
  const visited = new Set();
  const events = [];
  let failures = 0;

  while (queue.length > 0 && (maxPages == null || visited.size < maxPages)) {
    const url = queue.shift();
    if (!url || visited.has(url)) {
      continue;
    }
    visited.add(url);
    const fetcher = fetcherOverride || "get";
    const pageNum = String(visited.size).padStart(2, "0");
    const outputPath = path.join(runDir, `${pageNum}.html`);
    const fetchResult = api.engine.runEngineFetch(repoRoot, fetcher, url, outputPath);

    if (fetchResult.ok) {
      events.push(`Fetched ${url} via ${fetcher}.`);
      const discovered = api.traversal.extractAllLinks(outputPath, url, { sameDomain, matchPattern });
      for (const nextUrl of discovered) {
        if (!visited.has(nextUrl) && !queue.includes(nextUrl)) {
          queue.push(nextUrl);
        }
      }
      if (discovered.length > 0) {
        events.push(`Discovered ${discovered.length} new link(s) from ${url}.`);
      }
    } else {
      failures += 1;
      const errorPath = path.join(runDir, `${pageNum}.stderr.log`);
      api.report.writeTextFile(errorPath, fetchResult.stderr || "Scrapling scrape fetch failed.");
      events.push(`Failed ${url} via ${fetcher}.`);
    }
  }

  const manifest = {
    command: "scrape",
    target: targetUrl,
    repo_ref: repoRef,
    resolution_mode: resolutionMode,
    visited: [...visited],
    max_pages: maxPages,
    same_domain: sameDomain,
    match_pattern: matchPattern,
  };

  // Phase 2: Markdown conversion
  let phase2Result = null;
  let extractionMethod = "scrapling";
  let parallelFallbackReason = null;

  if (markdown && visited.size > 0) {
    if (parallel) {
      const poolOutcome = await api.pool.withObscuraPool(repoRoot, [...visited], workers, 15, async (fetchResults) => {
        const prefetchedHtml = {};
        for (const r of fetchResults) {
          if (r.html) {
            prefetchedHtml[r.url] = r.html;
          }
        }
        return api.convert.convertTraversalToMarkdown(repoRoot, runDir, manifest, {
          fetcherFn: () => fetcherOverride || "get",
          concurrency,
          merge,
          cleanupHtml: !keepHtml,
          outputName: "scrape-output",
          prefetchedHtml,
        });
      });
      phase2Result = poolOutcome.result;
      extractionMethod = poolOutcome.extractionMethod;
      parallelFallbackReason = poolOutcome.fallbackReason;
    }

    if (!phase2Result) {
      phase2Result = api.convert.convertTraversalToMarkdown(repoRoot, runDir, manifest, {
        fetcherFn: () => fetcherOverride || "get",
        concurrency,
        merge,
        cleanupHtml: !keepHtml,
        outputName: "scrape-output",
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

  const artifacts = [api.report.absoluteArtifact(manifestPath, "disposable", "Scrape manifest")];

  if (markdown) {
    artifacts.push(...api.convert.collectMarkdownArtifacts(runDir));
    // Ensure merged file gets a descriptive label if found by collectMarkdownArtifacts
    for (const { url } of (phase2Result?.failed ?? [])) {
      const idx = manifest.visited.indexOf(url);
      if (idx >= 0) {
        const errorPath = path.join(runDir, `${String(idx + 1).padStart(2, "0")}.md.error.log`);
        if (api.fs.existsSync(errorPath)) {
          artifacts.push(api.report.absoluteArtifact(errorPath, "disposable", `Conversion error for ${url}`));
        }
      }
    }
  } else {
    for (let i = 0; i < visited.size; i += 1) {
      const pageNum = String(i + 1).padStart(2, "0");
      const htmlPath = path.join(runDir, `${pageNum}.html`);
      if (api.fs.existsSync(htmlPath)) {
        artifacts.push(api.report.absoluteArtifact(htmlPath, "disposable", `Scraped page ${pageNum}`));
      }
    }
  }

  const traversalOk = visited.size > 0 && failures === 0;
  const conversionOk = !markdown || (phase2Result && phase2Result.failed.length === 0);
  const resultState =
    traversalOk && conversionOk ? "success" : visited.size > failures ? "partial_success" : "failure";

  if (emitReport) {
    const report = api.report.buildScrapeReport({
      targetUrl,
      repoRef,
      resolutionMode,
      events,
      result: resultState,
      phase2: markdown && phase2Result
        ? {
            successful: phase2Result.successful.length,
            failed: phase2Result.failed.length,
            mergedPath: phase2Result.mergedPath,
          }
        : null,
    });
    api.report.writeTextFile(reportPath, report);
    artifacts.unshift(api.report.absoluteArtifact(reportPath, "durable", "Scrape report"));
  }

  const summary =
    resultState === "success"
      ? `Scrape visited ${visited.size} page(s)${markdown ? ` and converted ${phase2Result.successful.length} to Markdown` : ""}.`
      : resultState === "partial_success"
        ? `Scrape visited ${visited.size} page(s)${markdown ? `; ${phase2Result.successful.length} converted, ${phase2Result.failed.length} failed` : ` with ${failures} fetch failure(s)`}.`
        : "Scrape failed before any page completed successfully.";

  const nextAction =
    resultState === "failure"
      ? "Review the scrape report, URL filters, or target availability before retrying."
      : "Inspect the scrape outputs. Adjust --match or --max-pages if more coverage is needed.";

  return api.report.makeResult("scrape", targetUrl, repoRef, summary, artifacts, nextAction, resultState, {
    workflow: "content_retrieval",
    engine_path: `scrapling_preflight:${preflight.status ?? "unknown"} -> scrape_traversal(${visited.size} pages)${markdown ? ` -> markdown_conversion(${phase2Result?.successful.length ?? 0}/${visited.size})` : ""}`,
    extraction_method: extractionMethod,
    ...(parallelFallbackReason ? { fallback_reason: parallelFallbackReason } : {}),
  });
}
