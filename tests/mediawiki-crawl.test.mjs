import test from 'node:test';
import assert from 'node:assert/strict';
import { runMediawikiWorkflow } from '../scripts/lib/mediawiki-crawl.mjs';

function harness(results = []) {
  const calls = [];
  const api = {
    run(kind, args) { calls.push({kind, args}); return results.shift() ?? {status: 0, payload: {result: 'success', manifest_path: '/run/page_manifest.json'}}; },
  };
  return {api, calls};
}
for (const options of [{discoveryOnly: true}, {discoveryOnly: true, yes: true}, {phase: 'discover'}, {}]) {
  test(`discovery stops before extraction ${JSON.stringify(options)}`, () => {
    const h = harness();
    const result = runMediawikiWorkflow(options, h.api);
    assert.equal(h.calls.length, 1); assert.equal(h.calls[0].kind, 'discover');
    assert.equal(result.discovery_only, true);
  });
}
test('yes resumes complete discovery, partial does not', () => {
  const h = harness();runMediawikiWorkflow({yes:true},h.api);
  assert.deepEqual(h.calls.map(c=>c.kind), ['discover','pipeline']);
  const partial = harness([{status:1,payload:{result:'partial_success',manifest_path:'/m'}}]);
  runMediawikiWorkflow({yes:true},partial.api);assert.equal(partial.calls.length,1);
});
test('manifest resumes directly and conflicts fail before spawn', () => {
  const h=harness();runMediawikiWorkflow({fromManifest:'/m'},h.api);
  assert.equal(h.calls[0].kind,'pipeline');
  assert.throws(()=>runMediawikiWorkflow({fromManifest:'/m',discoveryOnly:true},h.api),/incompatible/);
});

test('process failure metadata is preserved and null is never partial', () => {
  for (const status of [20,14,null]) {
    const h=harness([{status,stderr:'upstream details',signal:status===null?'SIGTERM':null}]);
    const result=runMediawikiWorkflow({discoveryOnly:true},h.api);
    assert.equal(result.failure_context.upstream_exit_code,status);
    assert.equal(result.failure_context.stderr_summary,'upstream details');
    assert.equal(result.failure_context.fallback_reason,'incompatible_workflow_contract');
    assert.equal(h.calls.length,1);
  }
});

test('real public CLI dispatches discovery and retains upstream failure', async () => {
  const fs = await import('node:fs');const os = await import('node:os');const path = await import('node:path');
  const {spawnSync} = await import('node:child_process');
  const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'mediawiki-cli-'));
  try {
    const fake=path.join(tmp,'python');const log=path.join(tmp,'calls');
    fs.writeFileSync(fake,`#!/bin/sh\nset -eu\nprintf '%s\\n' "$*" >> '${log}'\nprintf '%s\\n' '{"result":"success","manifest_path":"${tmp}/page_manifest.json"}'\n`);fs.chmodSync(fake,0o755);
    const args=['scripts/chrome-agent-cli.mjs','crawl','https://growagarden.fandom.com/wiki/Grow_a_Garden_Wiki','--discovery-only','--format','json','--output',tmp];
    const env={...process.env,CHROME_AGENT_PYTHON:fake};
    let result=spawnSync(process.execPath,args,{encoding:'utf8',env});
    assert.equal(result.status,0,result.stderr);assert.equal(JSON.parse(result.stdout).discovery_only,true);
    assert.match(fs.readFileSync(log,'utf8'),/scripts.explore.page_discovery/);
    assert.doesNotMatch(fs.readFileSync(log,'utf8'),/scripts.pipeline/);
    fs.writeFileSync(fake, `#!/bin/sh\ncase "$*" in *strategy_lifecycle*) exit 0;; esac\nprintf "manifest_contract broken" >&2\nexit 20\n`);
    result=spawnSync(process.execPath,args,{encoding:'utf8',env});
    const error=JSON.parse(result.stdout);assert.equal(error.upstream_exit_code,20);assert.match(error.stderr_summary,/manifest_contract/);
    assert.ok(error.handoff_path);assert.equal(error.result,'failure');
  } finally {fs.rmSync(tmp,{recursive:true,force:true});}
});

test('capability doctor recognizes discover kernel without duplicate spec', async () => {
  const {spawnSync}=await import('node:child_process');
  const result=spawnSync(process.execPath,['scripts/chrome-agent-cli.mjs','doctor','--check','capabilities','--format','json'],{encoding:'utf8'});
  const report=JSON.parse(result.stdout);
  assert.equal(report.result,'success',report.summary);
  assert.ok(report.checks.some(c=>c.name==='impl_page_discovery' && c.ok));
});
