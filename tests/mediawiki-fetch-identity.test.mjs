import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { spawnSync } from 'node:child_process';
import { resolveAppPython } from '../scripts/lib/python-resolver.mjs';

const root = process.cwd();
const source = fs.readFileSync('scripts/chrome-agent-cli.mjs', 'utf8');
function harness(t, response) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'mw-identity-'));
  t.after(() => fs.rmSync(dir, {recursive:true, force:true}));
  const callsPath = path.join(dir, 'calls.json');
  const context = vm.createContext({fs, path, URL, resolveAppPython,
    readFrontmatter: () => ({api:{base_url:'https://example.invalid/api.php'}}),
    spawnSync: (cmd, args, options) => {
      const prefix = `import sys, types, json\nfrom pathlib import Path\nm = types.ModuleType('scripts.pipeline.client')\nclass FakeClient:\n    def __init__(self, base_url): self.base_url = base_url\n    def query(self, **params):\n        Path(${JSON.stringify(callsPath)}).write_text(json.dumps({'base_url':self.base_url,'params':params}))\n        return json.loads(${JSON.stringify(JSON.stringify(response))})\n    def parse(self, page, **params): return self.query(action='parse',page=page,**params)\nm.ApiClient = FakeClient\nsys.modules['scripts.pipeline.client'] = m\n`;
      return spawnSync(cmd, ['-c', prefix + args[1], ...args.slice(2)], options);
    },
  });
  for (const name of ['isMediawikiApiTarget', 'resolveMediawikiFetchRequest', 'runMediawikiApiFetch']) {
    const start = source.indexOf(`function ${name}(`);
    if (start < 0) continue;
    vm.runInContext(source.slice(start, source.indexOf('\nfunction ', start + 1)), context);
  }
  return {dir, context, call: (url, strategy = []) => context.runMediawikiApiFetch(root, url, path.join(dir,'content.md'), strategy),
    request: () => JSON.parse(fs.readFileSync(callsPath,'utf8'))};
}

test('显式单页 parse 保留原 HTML、完整 API 响应和真实身份', t => {
  const html = '<div><table><tr><td rowspan="2">A</td></tr></table></div>';
  const response = {parse:{title:'Endgame (Mega Mall Story)',pageid:17,revid:902,text:{'*':html}},warnings:{example:'kept'}};
  const h = harness(t, response);
  const url = 'https://example.invalid/api.php?action=parse&page=Endgame_(Mega_Mall_Story)&prop=text%7Crevid&format=json';
  const result = h.call(url);
  assert.equal(result.ok, true, result.stderr);
  assert.equal(fs.readFileSync(result.output_path,'utf8'), html);
  assert.equal(result.mediawiki.page_title, response.parse.title);
  assert.equal(result.mediawiki.page_id, 17);
  assert.equal(result.mediawiki.revision_id, 902);
  assert.deepEqual(JSON.parse(fs.readFileSync(result.mediawiki.response_path,'utf8')), response);
  assert.equal(h.request().base_url, 'https://example.invalid/api.php');
  assert.deepEqual(h.request().params, {action:'parse',page:'Endgame_(Mega_Mall_Story)',prop:'text|revid'});
});

test('fetch 编排无策略时仍走显式 API，manifest 和 artifacts 指向原 HTML 与响应', t => {
  const h = harness(t, {parse:{title:'Page',pageid:3,revid:9,text:{'*':'<p>original</p>'}}});
  const c = h.context;
  Object.assign(c, {
    buildRunPaths: () => ({runDir:h.dir,reportPath:path.join(h.dir,'report.md')}),
    ensureDir: () => {}, findStrategy: () => ({strategy:null}),
    selectFetcher: () => 'get', buildScraplingExtractionArgs: () => [],
    runEngineFetch: (root, fetcher, url, out, args) => {
      assert.equal(fetcher, 'mediawiki-api');
      return c.runMediawikiApiFetch(root,url,out,args);
    },
    shouldEmitReport: () => false,
    writeTextFile: (p, text) => fs.writeFileSync(p,text),
    absoluteArtifact: (p,kind,description) => ({path:p,kind,description}),
    summarizeContent: () => 'Page',
    makeResult: (...args) => args,
  });
  const start = source.indexOf('function runFetch(');
  vm.runInContext(source.slice(start,source.indexOf('\nfunction ',start+1)),c);
  const url = 'https://example.invalid/api.php?action=parse&page=Page';
  const result = c.runFetch(root,'repo://chrome-agent','explicit',url,false);
  assert.equal(result[6], 'success');
  const manifest = JSON.parse(fs.readFileSync(path.join(h.dir,'manifest.json'),'utf8'));
  assert.equal(manifest.target, url);
  assert.equal(manifest.output, path.join(h.dir,'content.html'));
  assert.equal(manifest.mediawiki.revision_id,9);
  assert.ok(result[4].some(a => a.path === manifest.mediawiki.response_path));
  assert.ok(result[4].some(a => a.path === manifest.output));
  assert.equal(fs.existsSync(path.join(h.dir,'content.md')),false);
});

test('显式 API 拒绝非单页、未知动作/参数和重复参数，请求前失败', t => {
  for (const query of ['action=query&page=Page','action=parse&page=A%7CB', 'action=parse&page=Page&section=2', 'action=parse&page=Page&page=Other','action=parse&page=Page&format=xml']) {
    const h = harness(t, {});
    assert.equal(h.call('https://example.invalid/api.php?' + query).ok,false,query);
    assert.equal(fs.existsSync(path.join(h.dir,'calls.json')),false,query);
  }
});

test('缺失权威身份或挑战 HTML 不发布正文，保留 API 诊断', t => {
  for (const parsed of [{title:'Page',pageid:3,text:{'*':'<p>x</p>'}},
    {title:'Page',pageid:3,revid:9,text:{'*':fs.readFileSync('tests/fixtures/challenge-wikigg.html','utf8')}}]) {
    const h = harness(t, {parse:parsed});
    const result = h.call('https://example.invalid/api.php?action=parse&page=Page');
    assert.equal(result.ok,false);
    assert.equal(fs.existsSync(path.join(h.dir,'content.html')),false);
    assert.ok(result.diagnostic_path);
  }
});

test('history 通过共享 query 返回最多 50 条元数据并保留续页令牌，无贡献者字段', t => {
  const response = {continue:{rvcontinue:'20260101000000|91',continue:'||'},query:{pages:{'257':{pageid:257,title:'Characters',revisions:[{revid:8144,parentid:8143,timestamp:'2026-01-01T00:00:00Z',comment:'edit',size:1200}]}}}};
  const h = harness(t,response);
  const result = h.call('https://example.invalid/wiki/Characters?action=history',['strategy.md']);
  assert.equal(result.ok,true,result.stderr);
  assert.deepEqual(JSON.parse(fs.readFileSync(result.output_path,'utf8')),response);
  assert.equal(path.basename(result.output_path),'history.json');
  assert.deepEqual(h.request().params,{prop:'revisions',titles:'Characters',rvprop:'ids|timestamp|comment|size',rvlimit:50});
  assert.equal(result.mediawiki.page_id,257);
  assert.equal(result.mediawiki.revision_id,null);
  assert.equal(result.mediawiki.revision_count,1);
  assert.equal(result.mediawiki.continue.rvcontinue,response.continue.rvcontinue);
});

test('oldid 只向 parse 传修订 ID，核验服务端版本与页面而非回退当前页', t => {
  const h = harness(t,{parse:{title:'Characters',pageid:257,revid:8130,text:{'*':'<p>older</p>'}}});
  const result = h.call('https://example.invalid/wiki/Characters?oldid=8130',['strategy.md']);
  assert.equal(result.ok,true,result.stderr);
  assert.equal(fs.readFileSync(result.output_path,'utf8'),'<p>older</p>');
  assert.deepEqual(h.request().params,{action:'parse',oldid:8130,prop:'text|revid'});
  assert.equal(result.mediawiki.revision_id,8130);
  assert.equal(path.basename(result.output_path),'content.html');
  for (const parsed of [{title:'Characters',pageid:257,revid:8144},{title:'Other',pageid:258,revid:8130}]) {
    const bad = harness(t,{parse:{...parsed,text:{'*':'<p>wrong</p>'}}});
    assert.equal(bad.call('https://example.invalid/wiki/Characters?oldid=8130',['strategy.md']).ok,false);
    assert.equal(fs.existsSync(path.join(bad.dir,'content.html')),false);
  }
});

test('history 续页保持同页、显式小上限，不自动遍历', t => {
  const h = harness(t,{query:{pages:{'257':{pageid:257,title:'Characters',revisions:[{revid:8130}]}}}});
  assert.equal(h.call('https://example.invalid/wiki/Characters?action=history&limit=2&rvcontinue=20260101000000%7C91',['strategy.md']).ok,true);
  assert.deepEqual(h.request().params,{prop:'revisions',titles:'Characters',rvprop:'ids|timestamp|comment|size',rvlimit:2,rvcontinue:'20260101000000|91',continue:'||'});
});

test('非法历史或修订组合在网络前拒绝，跨源策略拒绝', t => {
  for (const query of ['action=edit','action=raw','action=history&oldid=1','action=history&limit=500','action=history&limit=0','action=history&rvcontinue=abc','oldid=0','oldid=-1','oldid=1.5','oldid=9007199254740992','oldid=1&diff=prev','oldid=1&oldid=2','limit=2','title=Other','action=']) {
    const h=harness(t,{});
    const result=h.call('https://example.invalid/wiki/Characters?'+query,['strategy.md']);
    assert.equal(result.ok,false,query);
    assert.equal(fs.existsSync(path.join(h.dir,'calls.json')),false,query);
  }
  const h=harness(t,{});
  assert.equal(h.call('https://other.invalid/wiki/Characters?action=history',['strategy.md']).ok,false);
  assert.equal(fs.existsSync(path.join(h.dir,'calls.json')),false);
});

test('普通 fetch 保持原输出且完整子页标题；index.php 与显式 oldid 有独立身份', t => {
  const response={parse:{title:'Some Page/Subpage',pageid:4,revid:7,text:{'*':'<p>complete</p>'}}};
  const h=harness(t,response);
  assert.equal(h.call('https://example.invalid/wiki/Some_Page/Subpage',['strategy.md']).output_path,path.join(h.dir,'content.md'));
  assert.deepEqual(h.request().params,{action:'parse',page:'Some Page/Subpage',prop:'text|revid',redirects:true});
  const index=harness(t,response);
  assert.equal(index.call('https://example.invalid/w/index.php?title=Some_Page%2FSubpage&oldid=7',['strategy.md']).ok,true);
  const api=harness(t,response);
  assert.equal(api.call('https://example.invalid/w/api.php?action=parse&oldid=7').ok,true);
  assert.deepEqual(api.request().params,{action:'parse',oldid:7,prop:'text|revid'});
});

test('历史响应不接受错页、超上限或无修订号', t => {
  for (const page of [{pageid:257,title:'Other',revisions:[{revid:1}]},
    {pageid:257,title:'Characters',revisions:[{}]},
    {pageid:257,title:'Characters',revisions:[{revid:1},{revid:2}]}]) {
    const h=harness(t,{query:{pages:{'257':page}}});
    assert.equal(h.call('https://example.invalid/wiki/Characters?action=history&limit=1',['strategy.md']).ok,false);
    assert.equal(fs.existsSync(path.join(h.dir,'history.json')),false);
  }
});
