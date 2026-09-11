/** Public MediaWiki workflow. All subprocess I/O is injected by the CLI. */
export function runMediawikiWorkflow(options, api) {
  options = {...options, pipelineTimeoutMs: resolvePipelineTimeout(options.pipelineTimeoutSeconds) * 1000};
  const discoveryOnly = options.discoveryOnly || options.phase === 'discover';
  if ((discoveryOnly && options.fromManifest) || (options.discoveryOnly && options.phase && options.phase !== 'discover')) {
    throw new Error('incompatible discovery and extraction options');
  }
  let manifest = options.fromManifest;
  if (discoveryOnly || (!manifest && (!options.phase || options.phase === 'all'))) {
    const discovery = api.run('discover', options);
    if (discovery.status !== 0 && discovery.status !== 1) return withFailure(discovery, options);
    if (discoveryOnly || !options.yes || discovery.status === 1) {
      return {...discovery, discovery_only: true, confirmation_required: !discoveryOnly || !options.yes};
    }
    manifest = discovery.payload?.manifest_path;
    if (!manifest) throw new Error('Discovery returned no manifest');
  }
  return withFailure(api.run('pipeline', {...options, fromManifest: manifest}), options);
}

function withFailure(result, options) {
  if ((result.status === 0 || result.status === 1) && !result.error && !result.signal) return result;
  return {...result, failure_context: {
    pipeline_timeout_seconds: options.pipelineTimeoutMs / 1000,
    upstream_backend: 'mediawiki', upstream_exit_code: result.status ?? null,
    process_error: result.error?.message ?? null, signal: result.signal ?? null,
    stderr_summary: (result.stderr || result.payload?.error || '').slice(-4000),
    requested_mode: options.discoveryOnly || options.phase === 'discover' ? 'discovery_only' : options.fromManifest ? 'from_manifest' : 'all',
    fallback_reason: 'incompatible_workflow_contract',
    failure_kind: result.status === 10 && !result.error && !result.signal ? 'external' : 'internal',
  }};
}

/** Validate a bounded subprocess budget, independent of API request timeouts. */
export function resolvePipelineTimeout(value = 600) {
  if (!/^[0-9]+$/.test(String(value)) || typeof value === 'boolean') {
    throw new Error('--pipeline-timeout-seconds requires an integer from 1 to 86400');
  }
  const seconds = Number(value);
  if (!Number.isSafeInteger(seconds) || seconds < 1 || seconds > 86400) {
    throw new Error('--pipeline-timeout-seconds requires an integer from 1 to 86400');
  }
  return seconds;
}
