import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { gzipSync, gunzipSync } from 'node:zlib';

const source = fs.readFileSync(new URL('../scripts/chrome-agent-cli.mjs', import.meta.url), 'utf8');
const base = 'https://example.invalid';
const top = `${base}/sitemap.xml`;
function urlset(...urls) {
  return `<urlset>${urls.map(url => `<url><loc>${url}</loc></url>`).join('')}</urlset>`;
}
function index(...urls) {
  return `<sitemapindex>${urls.map(url => `<sitemap><loc>${url}</loc></sitemap>`).join('')}</sitemapindex>`;
}
function harness(t, responses, options = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'sitemap-files-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const runDir = path.join(root, 'run');
  fs.mkdirSync(runDir);
  const calls = [];
  const context = vm.createContext({ fs, path, URL, Buffer, gunzipSync,
    inferredRepoRoot: root, DEFAULT_REPO_REF: 'repo://test',
    console: { log() {} },
    spawnSync(command, args) {
      assert.equal(command, 'curl');
      const url = args.at(-1);
      calls.push(url);
      const response = responses[url];
      if (response === undefined) return { status: 1, stdout: '000', stderr: 'offline' };
      fs.writeFileSync(args[args.indexOf('-o') + 1], response);
      return { status: 0, stdout: '200', stderr: '' };
    },
  });
  const names = ['readSitemapContent', 'parseSitemapXml', 'resolveSitemapIndex',
    'runCrawlSitemapDiscovery', 'autoGroupSitemapUrls', 'buildSitemapDiscoverySummary',
    'pagePatternMatches', 'matchesPagePattern', 'internalFailure', 'generateHandoff',
    'makeResult', 'absoluteArtifact', 'slugify', 'nowParts', 'ensureDir', 'writeTextFile'];
  for (const name of names) {
    const match = new RegExp(`^(?:async )?function ${name}\\(`, 'm').exec(source);
    if (!match) continue;
    const end = source.indexOf('\n}\n', match.index) + 2;
    vm.runInContext(source.slice(match.index, end), context);
  }
  const doc = { domain: 'example.invalid', discovery: { method: 'sitemap', sitemap_url: top, ...options },
    structure: { pages: [{ id: 'docs', page_pattern: ['regex:^https://example[.]invalid/docs/'], target_directory: 'docs' }] } };
  return { root, runDir, context, calls,
    run: () => context.runCrawlSitemapDiscovery(root, 'repo://test', 'test', runDir, null, false,
      `${base}/docs/start`, { path: path.join(root, 'strategy.md') }, doc, {}),
    manifest: () => JSON.parse(fs.readFileSync(path.join(runDir, 'page_manifest.json'), 'utf8')),
    summary: () => JSON.parse(fs.readFileSync(path.join(runDir, 'discovery_summary.json'), 'utf8')),
  };
}

test('discovery reads gzip child bytes and preserves the raw response', async t => {
  const child = `${base}/child.xml.gz`;
  const raw = gzipSync(urlset(`${base}/docs/a`));
  const h = harness(t, { [top]: index(child), [child]: raw });
  const result = await h.run();
  assert.equal(result.result, 'success', JSON.stringify(result));
  assert.deepEqual(h.manifest().pages.map(p => p.url), [`${base}/docs/a`]);
  assert.deepEqual(fs.readFileSync(path.join(h.runDir, '_sitemap_sub_0.xml')), raw);
});

test('discovery reads gzip top-level urlset without a gzip suffix', async t => {
  const h = harness(t, { [top]: gzipSync(urlset(`${base}/docs/a`)) });
  assert.equal((await h.run()).result, 'success');
  assert.deepEqual(h.manifest().pages.map(p => p.url), [`${base}/docs/a`]);
});

test('gzip index merges mixed child encodings by bytes, deduplicates and filters', async t => {
  const a = `${base}/compressed.xml`, b = `${base}/plaintext.xml.gz`;
  const h = harness(t, {
    [top]: gzipSync(index(a, b)),
    [a]: gzipSync(urlset(`${base}/docs/a`, `${base}/docs/excluded`, `${base}/other/b`)),
    [b]: urlset(`${base}/docs/a`, `${base}/docs/b`),
  }, { exclude_patterns: ['exact:/docs/excluded'] });
  assert.equal((await h.run()).result, 'success');
  assert.deepEqual(h.manifest().pages.map(p => p.url), [`${base}/docs/a`, `${base}/docs/b`]);
  assert.deepEqual(h.calls, [top, a, b]);
});

test('corrupt top-level gzip returns a decompression handoff and retains bytes', async t => {
  const raw = gzipSync(urlset(`${base}/docs/a`)).subarray(0, 12);
  const h = harness(t, { [top]: raw });
  const result = await h.run();
  assert.equal(result.result, 'failure');
  assert.match(result.handoff_summary, /sitemap_decompress_error/);
  assert.deepEqual(fs.readFileSync(path.join(h.runDir, '_sitemap.xml')), raw);
});

test('decoded non-XML remains a parse error', async t => {
  const h = harness(t, { [top]: gzipSync('<html>Not a sitemap</html>') });
  assert.match((await h.run()).handoff_summary, /sitemap_parse_error/);
});

test('one corrupt gzip child keeps valid URLs and reports partial failure', async t => {
  const a = `${base}/bad.gz`, b = `${base}/good.xml`;
  const h = harness(t, { [top]: index(a, b), [a]: Buffer.from([0x1f, 0x8b, 0x08]),
    [b]: urlset(`${base}/docs/a`) });
  const result = await h.run();
  assert.equal(result.result, 'partial_success');
  assert.deepEqual(h.manifest().pages.map(p => p.url), [`${base}/docs/a`]);
  const summary = h.summary();
  assert.equal(summary.failure_rate, 0.5);
  assert.match(summary.warnings.join(' '), /bad.gz.*decompress_error/);
  assert.match(summary.caveats.join(' '), /1\/2 sub-sitemaps failed/);
});

test('all corrupt children use all-subs-failed; decoded HTML stays parse_error', async t => {
  const a = `${base}/bad.gz`, b = `${base}/bad2.gz`;
  const h = harness(t, { [top]: index(a, b), [a]: Buffer.from([0x1f, 0x8b]),
    [b]: Buffer.from([0x1f, 0x8b, 0x08]) });
  const result = await h.run();
  assert.match(result.handoff_summary, /sitemap_all_subs_failed/);
  const report = fs.readFileSync(result.handoff_path, 'utf8');
  assert.equal((report.match(/decompress_error/g) || []).length, 2);
  const html = harness(t, { [top]: index(a), [a]: gzipSync('<html>Bad</html>') });
  const htmlResult = await html.run();
  assert.match(fs.readFileSync(htmlResult.handoff_path, 'utf8'), /parse_error/);
});

test('failure handoff links raw index and children without inventing a manifest', async t => {
  const a = `${base}/a.gz`, b = `${base}/b.gz`, raw = Buffer.from([0x1f, 0x8b]);
  const h = harness(t, { [top]: index(a, b), [a]: raw, [b]: raw });
  const result = await h.run();
  const report = fs.readFileSync(result.handoff_path, 'utf8');
  for (const name of ['_sitemap.xml', '_sitemap_sub_0.xml', '_sitemap_sub_1.xml']) {
    assert.ok(report.includes(path.join(h.runDir, name)), `${name} must be linked`);
    assert.ok(result.artifacts.some(a => a.path === path.join(h.runDir, name)));
  }
  assert.ok(!report.includes(path.join(h.runDir, 'manifest.json')));
  assert.deepEqual(fs.readFileSync(path.join(h.runDir, '_sitemap_sub_0.xml')), raw);
});

test('network failure does not link absent or stale sitemap responses', async t => {
  const h = harness(t, {});
  fs.writeFileSync(path.join(h.runDir, '_sitemap.xml'), 'stale');
  fs.writeFileSync(path.join(h.runDir, '_sitemap_sub_9.xml'), 'old unrelated response');
  const result = await h.run();
  assert.match(result.handoff_summary, /sitemap_unreachable/);
  const report = fs.readFileSync(result.handoff_path, 'utf8');
  assert.ok(!report.includes(path.join(h.runDir, '_sitemap.xml')));
  assert.ok(!report.includes(path.join(h.runDir, '_sitemap_sub_9.xml')));
  assert.equal(result.artifacts.length, 0);
});

test('legacy handoff callers retain existing manifest and logs without duplicates', t => {
  const h = harness(t, {});
  for (const name of ['manifest.json', 'fetch.log']) fs.writeFileSync(path.join(h.runDir, name), '{}');
  const context = { command: 'fetch', target: base, repoRef: 'repo://test', runDir: h.runDir,
    error: { reason: 'test_failure', summary: 'Fixture failure' } };
  const legacy = h.context.generateHandoff(context);
  assert.ok(fs.readFileSync(legacy.path, 'utf8').includes(path.join(h.runDir, 'manifest.json')));
  const report = h.context.generateHandoff({ ...context, artifacts: [
    { path: path.join(h.runDir, 'manifest.json'), description: 'Manifest' },
    { path: path.join(h.runDir, 'absent.xml'), description: 'Absent' },
  ] });
  const text = fs.readFileSync(report.path, 'utf8');
  for (const name of ['manifest.json', 'fetch.log']) {
    assert.equal(text.split(path.join(h.runDir, name)).length - 1, 1);
  }
  assert.ok(!text.includes('absent.xml'));
});
