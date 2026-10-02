import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { resolveAppPython } from '../scripts/lib/python-resolver.mjs';
const root = process.cwd();
const source = fs.readFileSync('scripts/chrome-agent-cli.mjs', 'utf8');
function harness(html, calls) {
  const context = vm.createContext({fs, os, path, process, resolveAppPython, fileURLToPath,
    ensureDir: (p) => fs.mkdirSync(p, {recursive:true}),
    runScraplingPreflight: () => ({ok:true, resolvedCliPath:'fake'}),
    spawnSync: (cmd,args,opts) => {
      if (cmd !== 'fake') return spawnSync(cmd,args,opts);
      calls.push(args);
      if (args[2].startsWith('file:')) fs.writeFileSync(args[3], '# Normal content');
      else fs.writeFileSync(args[3], html);
      return {status:0, stdout:'',stderr:''};
    },
  });
  for (const name of ['admitHtmlFile','runScraplingFetch']) {
    const start=source.indexOf(`function ${name}(`);
    if(start<0) continue;
    const end=source.indexOf('\nfunction ',start+1);
    vm.runInContext(source.slice(start,end),context);
  }
  return (output,args) => context.runScraplingFetch(root,'get','https://example.invalid',output,args);
}
test('fetch rejects challenge before selector and performs no conversion', () => {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'admission-'));
  try {
    const calls=[];
    const run=harness(fs.readFileSync('tests/fixtures/challenge-wikigg.html','utf8'),calls);
    const out=path.join(dir,'page.md');
    const result=run(out,['-s','article']);
    assert.equal(result.ok,false);
    assert.equal(fs.existsSync(out),false);
    assert.equal(calls.length,1);
    assert.equal(calls[0].includes('-s'),false);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
test('normal HTML is converted locally with original selector and only one remote fetch', () => {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'admission-'));
  try {
    const calls=[];
    const out=path.join(dir,'page.md');
    assert.equal(harness('<article>Normal content</article>',calls)(out,['-s','article']).ok,true);
    assert.equal(calls.filter(a=>a[2].startsWith('https:')).length,1);
    assert.ok(calls[1][2].startsWith('file:'));
    assert.equal(JSON.stringify(calls[1].slice(-2)),JSON.stringify(['-s','article']));
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});

test('legacy Scrapling cache rejects challenges without deleting evidence', () => {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'cache-admission-'));
  try {
    const context=vm.createContext({fs,path,spawnSync,resolveAppPython,process});
    for (const name of ['admitHtmlFile','scraplingCacheDir','loadScraplingCache']) {
      const start=source.indexOf(`function ${name}(`);
      if(start<0) continue;
      vm.runInContext(source.slice(start,source.indexOf('\nfunction ',start+1)),context);
    }
    // Use the actual repo for the bridge, and isolate just the cache destination.
    context.scraplingCacheDir=()=>dir;
    fs.writeFileSync(path.join(dir,'bad.html'),fs.readFileSync('tests/fixtures/challenge-wikigg.html'));
    fs.writeFileSync(path.join(dir,'bad.meta.json'),'{}');
    assert.equal(context.loadScraplingCache(root,'example.invalid','bad'),null);
    assert.equal(fs.existsSync(path.join(dir,'bad.html')),true);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});

test('bridge preserves observed HTTP errors without inventing Cloudflare', () => {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'status-admission-'));
  try {
    const filename=path.join(dir,'normal.html');
    fs.writeFileSync(filename,'<h1>Forbidden</h1>');
    const start=source.indexOf('function admitHtmlFile(');
    const context=vm.createContext({spawnSync,resolveAppPython});
    vm.runInContext(source.slice(start,source.indexOf('\nfunction ',start+1)),context);
    const result=context.admitHtmlFile(root,filename,403);
    assert.equal(result.admitted,false);
    assert.equal(result.http_status,403);
    assert.equal(result.protection_type,null);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
