import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {spawnSync} from 'node:child_process';
import {resolveAppPython} from '../scripts/lib/python-resolver.mjs';
import {buildScraplingExtractionArgs} from '../scripts/lib/scrapling-extraction-args.mjs';
const root = process.cwd();
const source = fs.readFileSync('scripts/chrome-agent-cli.mjs','utf8');
const html = '<nav><a href="/login">Create account</a></nav><main><p>Body</p><div><span class="ordinary"><img src="https://example.invalid/canary.png"></span><h2>Structural canary</h2></div><ul><big><li>List canary</li></big></ul><h3><span class="mw-headline"><div style="display:none">Group</div></span></h3><div class="group">Group</div><div class="remove">REMOVE</div><table><tr><th>Skill</th><th>Value</th></tr><tr><td>Heal</td><td><table><tr><th>Rank</th></tr><tr><td>42</td></tr></table></td></tr></table><table><tr><th>A</th><th>B</th></tr><tr><td colspan="2">Gain<img src="https://example.invalid/status.png" alt="status.png"></td></tr></table></main>';
const rules = {table_options:{merged_cell_icon_labels:{"status.png":"Blind"}},selectors:{content:'main'},cleanup_selectors:['.remove'],cleanup:['unwrap_list_item_wrappers'],heading_normalization:[{heading_selector:'h3:has(.mw-headline)',label_selector:'.group'}]};
function harness(t, overrides={}) {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'crawl-convert-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const calls=[];
  const context=vm.createContext({fs,os,path,process,console,URL,spawnSync,resolveAppPython,buildScraplingExtractionArgs,
    ensureDir:p=>fs.mkdirSync(p,{recursive:true}),writeTextFile:(p,s)=>fs.writeFileSync(p,s),
    runEngineFetch:(_r,engine,url,out)=>{calls.push({engine,url,out});assert.ok(out.endsWith('.html'),'engines acquire HTML only');fs.writeFileSync(out,html);return {ok:true};},
    ...overrides});
  for(const name of ['admitHtmlFile','convertCrawlHtml','urlToStructuredPath','relativizeMarkdownLinks','convertTraversalToMarkdown','mergeMarkdownFiles']) {
    const start=source.indexOf(`function ${name}(`);
    if(start<0) continue;
    vm.runInContext(source.slice(start,source.indexOf('\nfunction ',start+1)),context);
  }
  return {dir,calls,context};
}
function expected(rulesValue=rules, sourceHtml=html) {
  const r=spawnSync(resolveAppPython(root),['-c','import sys,json; from scripts.lib.extraction.converter import convert_page_full; d=json.load(sys.stdin); print(convert_page_full(d[0],d[1]),end="")'],{cwd:root,input:JSON.stringify([sourceHtml,rulesValue]),encoding:'utf8'});
  assert.equal(r.status,0,r.stderr); return r.stdout;
}
test('matched crawl renders full strategy through shared kernel regardless of acquisition engine',t=>{
  const {dir,calls,context}=harness(t);
  const result=context.convertTraversalToMarkdown(root,dir,{visited:['https://example.invalid/page']},{strategy:{document:{extraction:rules}},fetcherFn:()=> 'cloakbrowser',relativize:false});
  assert.equal(result.failed.length,0);
  const md=fs.readFileSync(result.successful[0].path,'utf8');
  assert.equal(md,expected());
  assert.doesNotMatch(md,/Create account|REMOVE/);
  assert.match(md,/42/);
  assert.match(md,/\n\n## Structural canary\n/);
  assert.match(md,/- List canary/);
  assert.match(md,/### Group/);
  assert.match(md,/\| Gain Blind \|/);
  assert.equal(calls.length,1);
});

import {runCrawlScrapling} from '../scripts/lib/crawl_scrapling.mjs';
function crawlSetup(t, overrides={}) {
  const h=harness(t,overrides);
  const page={id:'page',url_example:'https://example.invalid/A',links_to:[]};
  const strategy={path:path.join(root,'strategy.md'),document:{extraction:rules}};
  const ctx={repoRoot:root,repoRef:'repo://chrome-agent',runDir:h.dir,manifestPath:path.join(h.dir,'manifest.json'),targetUrl:page.url_example,strategy,doc:{structure:{pages:[page]}},startPage:page,matchingPage:page,entryPoints:['page']};
  const api={fs,log:{info(){}},report:{writeTextFile:(p,s)=>fs.writeFileSync(p,s),absoluteArtifact:(p)=>({path:p}),makeResult:(_c,_t,_r,summary,artifacts,_n,result,extra)=>({summary,artifacts,result,...extra})},
    engine:{selectFetcher:()=> 'cloakbrowser',runEngineFetch:h.context.runEngineFetch},
    cache:{runScraplingPreflight:()=>({ok:true}),scraplingSlugFromUrl:u=>u.split('/').pop(),loadScraplingCache:()=>({html})},
    traversal:{pagePatternMatches:()=>true,collectLinksFromHtml:()=>[]},
    pool:{withObscuraPool:async()=>{throw Error('already acquired pages must not be fetched again');}},
    convert:{convertTraversalToMarkdown:h.context.convertTraversalToMarkdown,urlToStructuredPath:h.context.urlToStructuredPath,collectMarkdownArtifacts:()=>[]}};
  return {...h,ctx,api};
}
test('cache-only conversion runs real shared bridge without acquisition or engine preflight',async t=>{
  const h=crawlSetup(t);
  const manifest=path.join(h.dir,'input.json');
  fs.writeFileSync(manifest,JSON.stringify({visited:['https://example.invalid/A']}));
  h.api.cache.runScraplingPreflight=()=>{throw Error('cache-only must not preflight fetch engine');};
  const result=await runCrawlScrapling(h.ctx,{phase:'convert',fromManifest:manifest},h.api);
  assert.equal(result.result,'success');
  assert.equal(h.calls.length,0);
  const state=JSON.parse(fs.readFileSync(h.ctx.manifestPath));
  assert.equal(state.phase2.successful_count,1);
  assert.equal(fs.readFileSync(h.context.urlToStructuredPath('https://example.invalid/A',h.dir),'utf8'),expected());
});
test('ordinary crawl reuses admitted acquisition even with parallel option',async t=>{
  const h=crawlSetup(t);
  const result=await runCrawlScrapling(h.ctx,{parallel:true},h.api);
  assert.equal(result.result,'success');
  assert.equal(h.calls.length,1);
});
test('sitemap manifest conversion reuses raw acquisition through shared bridge',async t=>{
  const h=crawlSetup(t);
  Object.assign(h.context,{selectFetcher:h.api.engine.selectFetcher,pagePatternMatches:()=>true,absoluteArtifact:h.api.report.absoluteArtifact,makeResult:h.api.report.makeResult,collectMarkdownArtifacts:()=>[]});
  const start=source.indexOf('async function runCrawlSitemapExtraction(');
  vm.runInContext(source.slice(start),h.context);
  const manifest=path.join(h.dir,'input.json');
  fs.writeFileSync(manifest,JSON.stringify({pages:[{url:h.ctx.targetUrl}]}));
  const result=await h.context.runCrawlSitemapExtraction(root,'repo://chrome-agent','local',h.dir,'',h.ctx.manifestPath,false,h.ctx.targetUrl,h.ctx.strategy,h.ctx.doc,{fromManifest:manifest});
  assert.equal(result.result,'success');
  assert.equal(h.calls.length,1);
});
test('cache failures preserve exact URL identities and exclude stale artifacts',async t=>{
  const h=crawlSetup(t);
  const urls=['A','B','C'].map(x=>'https://example.invalid/'+x);
  const stale=h.context.urlToStructuredPath(urls[1],h.dir);
  fs.mkdirSync(path.dirname(stale),{recursive:true});fs.writeFileSync(stale,'STALE');
  h.api.convert.collectMarkdownArtifacts=()=>[{path:stale}];
  h.api.cache.loadScraplingCache=(_r,_d,slug)=>slug==='B'?null:{html};
  const manifest=path.join(h.dir,'input.json');fs.writeFileSync(manifest,JSON.stringify({visited:urls}));
  const result=await runCrawlScrapling(h.ctx,{phase:'convert',fromManifest:manifest,merge:true},h.api);
  assert.equal(result.result,'partial_success');
  const state=JSON.parse(fs.readFileSync(h.ctx.manifestPath));
  assert.deepEqual(state.phase2.failed_urls,[urls[1]]);
  assert.equal(state.phase2.successful_count,2);
  assert.equal(result.artifacts.some(a=>a.path===stale),false);
  assert.doesNotMatch(fs.readFileSync(state.phase2.merged_path,'utf8'),/STALE/);
});
test('matched conversion fails closed on bad rules, unavailable bridge and absent prefetched bytes',t=>{
  const {dir,context,calls}=harness(t);
  const url='https://example.invalid/page';
  for(const extraction of [null,[],{cleanup:['unknown_cleanup']}]) {
    const result=context.convertTraversalToMarkdown(root,dir,{visited:[url]},{strategy:{document:{extraction}},prefetchedHtml:{[url]:html}});
    assert.equal(result.failed.length,1);assert.equal(result.successful.length,0);
  }
  context.spawnSync=()=>({status:null,error:new Error('python unavailable')});
  for(const prefetchedHtml of [{[url]:html},{}]) {
    const result=context.convertTraversalToMarkdown(root,dir,{visited:[url]},{strategy:{document:{extraction:rules}},prefetchedHtml});
    assert.equal(result.failed.length,1);assert.equal(result.successful.length,0);
  }
  assert.equal(calls.length,0);
});
test('empty rules and API acquisition use shared conversion, generic route remains available',t=>{
  const {dir,context}=harness(t);
  const url='https://example.invalid/page';
  const result=context.convertTraversalToMarkdown(root,dir,{visited:[url]},{strategy:{document:{}},fetcherFn:()=> 'mediawiki-api',relativize:false});
  assert.equal(fs.readFileSync(result.successful[0].path,'utf8'),expected({}));
  context.runEngineFetch=(_r,_e,_u,out,args)=>{assert.deepEqual([...args],['--ai-targeted']);fs.writeFileSync(out,'generic');return {ok:true};};
  const generic=context.convertTraversalToMarkdown(root,dir,{visited:[url]},{relativize:false});
  assert.equal(fs.readFileSync(generic.successful[0].path,'utf8'),'generic');
});
test('prefetched core preserves enabled infobox once and applies post-ops',t=>{
  const {dir,context,calls}=harness(t);
  const url='https://example.invalid/page';
  const fixture='<aside class="portable-infobox"><div class="pi-item pi-data"><h3 class="pi-data-label">Seed Chance</h3><div class="pi-data-value">canary</div></div></aside><main><p>word2word</p></main>';
  const extraction={selectors:{content:'main'},infobox:{enabled:true},text_normalization:['fix_spaces']};
  const result=context.convertTraversalToMarkdown(root,dir,{visited:[url]},{strategy:{document:{extraction}},prefetchedHtml:{[url]:fixture},relativize:false});
  const md=fs.readFileSync(result.successful[0].path,'utf8');
  assert.equal(md,expected(extraction,fixture));
  assert.equal((md.match(/canary/g)||[]).length,1);assert.match(md,/word 2 word/);assert.equal(calls.length,0);
});
test('all failed cached conversions cannot publish a successful result',async t=>{
  const h=crawlSetup(t);h.api.cache.loadScraplingCache=()=>null;
  const manifest=path.join(h.dir,'input.json');fs.writeFileSync(manifest,JSON.stringify({visited:[h.ctx.targetUrl]}));
  const result=await runCrawlScrapling(h.ctx,{phase:'convert',fromManifest:manifest},h.api);
  assert.equal(result.result,'failure');
  assert.equal(result.artifacts.filter(a=>a.path.endsWith('.md')).length,0);
});
test('admission rejects prefetched challenge rather than publishing Markdown',t=>{
  const {dir,context}=harness(t);
  const url='https://example.invalid/page';
  const challenge=fs.readFileSync('tests/fixtures/challenge-wikigg.html','utf8');
  const result=context.convertTraversalToMarkdown(root,dir,{visited:[url]},{strategy:{document:{extraction:rules}},prefetchedHtml:{[url]:challenge}});
  assert.equal(result.successful.length,0);assert.equal(result.failed.length,1);
  assert.match(result.failed[0].error,/challenge/);
});
test('cache-only conversion honors maxPages scope reduction',async t=>{
  const h=crawlSetup(t);
  const manifest=path.join(h.dir,'input.json');fs.writeFileSync(manifest,JSON.stringify({visited:['https://example.invalid/A','https://example.invalid/B']}));
  await runCrawlScrapling(h.ctx,{phase:'convert',fromManifest:manifest,maxPages:1},h.api);
  assert.deepEqual(JSON.parse(fs.readFileSync(h.ctx.manifestPath)).visited,['https://example.invalid/A']);
});
