import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import {spawnSync} from 'node:child_process';
const source = fs.readFileSync('scripts/chrome-agent-cli.mjs', 'utf8');
function load(context, names) {
  for (const name of names) {
    const start=source.indexOf(`function ${name}(`);
    const end=source.indexOf('\nfunction ',start+1);
    vm.runInContext(source.slice(start,end),context);
  }
}
function report(needsUpdate=false) {
  return {all_ok:!needsUpdate, engines:[{engine:'cloakbrowser', expected:'0.4.3',detected:needsUpdate?null:'0.4.3',status:needsUpdate?'not_installed':'detected',needs_update:needsUpdate}]};
}
function fixture(t, body, spawn=spawnSync) {
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'health-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  fs.mkdirSync(path.join(root,'scripts'));
  fs.mkdirSync(path.join(root,'configs'));
  fs.writeFileSync(path.join(root,'configs/engine-versions.json'),JSON.stringify({engines:{cloakbrowser:{expected_version:'0.4.3'}}}));
  if(body!==null) fs.writeFileSync(path.join(root,'scripts/engine-version-check.sh'),body);
  const c=vm.createContext({fs,path,spawnSync:spawn});
  load(c,['runEngineVersionCheck']);
  return c.runEngineVersionCheck(root);
}
function shellReport(value,exit=0) {return `cat <<'JSON'\n${JSON.stringify(value)}\nJSON\nexit ${exit}\n`;}
test('missing checker is an explicit failure',t=>{
  const r=fixture(t,null);
  assert.equal(r.all_ok,false);
  assert.equal(r.error,'version_check_failed');
});
test('invalid checker outcomes cannot claim health',t=>{
  for(const body of ['', 'echo bad', shellReport({all_ok:true,engines:[]}), shellReport(report(),1), shellReport({...report(),engines:[...report().engines,...report().engines]}), shellReport({...report(),all_ok:'true'})]) {
    assert.equal(fixture(t,body).error,'version_check_failed',body);
  }
});
test('spawn failure and timeout are check failures',t=>{
  for(const code of ['ENOENT','ETIMEDOUT']) {
    const r=fixture(t,'exit 0',()=>({status:null,stdout:'',stderr:'',error:{code,message:code}}));
    assert.equal(r.error,'version_check_failed');
    assert.match(r.detail,new RegExp(code));
  }
});
test('complete nonhealthy report survives nonzero exit',t=>{
  const r=fixture(t,shellReport(report(true),1));
  assert.equal(r.all_ok,false);
  assert.equal(r.engines[0].status,'not_installed');
  assert.equal(r.error,undefined);
});
test('complete healthy report remains healthy',t=>assert.equal(fixture(t,shellReport(report())).all_ok,true));

function doctor(version, overrides={}) {
  const c=vm.createContext({fs:{existsSync:()=>true},path,os,process,
    runScraplingPreflight:()=>({ok:true}),runObscuraPreflight:()=>({ok:true,workerOk:true}),
    repoShapeIsValid:()=>true,runEngineVersionCheck:()=>version,
    runGitFetchCheck:()=>({ok:true,stale:false}),runExplorePythonDepsCheck:()=>({ok:true}),
    resolutionSummary:()=>'',makeResult:(command,target,repo,summary,artifacts,next_action,status,extra)=>({status,next_action,...extra}),...overrides});
  load(c,['runDoctor']);
  return c.runDoctor('/repo','repo://chrome-agent','explicit_override');
}
test('optional missing engine is explicit nonblocking partial readiness',()=>{
  const r=doctor(report(true));
  assert.equal(r.status,'partial_success');
  assert.equal(r.dispatch_allowed,true);
  const check=r.checks.find(c=>c.name==='version_cloakbrowser');
  assert.equal(check.blocking,false);
  assert.equal(check.readiness,'needs_preflight');
  assert.match(r.next_action,/preflight/);
});
test('required and unknown failures block dispatch',()=>{
  for(const version of [{all_ok:false,engines:[],error:'version_check_failed',detail:'bad JSON'},
    {...report(true),engines:[{...report(true).engines[0],engine:'scrapling'}]},
    {...report(true),engines:[{...report(true).engines[0],status:'inspection_failed'}]}]) {
    const r=doctor(version);
    assert.equal(r.status,'failure');
    assert.equal(r.dispatch_allowed,false);
    assert.ok(r.checks.some(c=>!c.ok && c.blocking));
  }
});
test('healthy and freshness gates retain their semantics',()=>{
  assert.equal(doctor(report()).status,'success');
  assert.equal(doctor(report(),{runGitFetchCheck:()=>({ok:false,stale:false,detail:'stale'})}).dispatch_allowed,false);
});

test('Node CloakBrowser rejects invalid preflight instead of falling back to system Python',()=>{
  for(const stdout of ['', 'STATUS=missing\nRESOLVED_CLI_PATH=/bin/sh\n', 'STATUS=available\nRESOLVED_CLI_PATH=/nonexistent\n']) {
    let calls=0;
    const c=vm.createContext({fs,path,ensureDir:()=>{},spawnSync:()=>{calls++;return {status:0,stdout,stderr:''};}});
    load(c,['runCloakbrowserFetch']);
    assert.equal(c.runCloakbrowserFetch('/repo','https://example.invalid','/tmp/not-written.html').ok,false);
    assert.equal(calls,1);
  }
});

test('Node CloakBrowser uses the resolved executable and preserves admission',t=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'cloak-node-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const out=path.join(dir,'page.html');
  const calls=[];
  const c=vm.createContext({fs,path,ensureDir:p=>fs.mkdirSync(p,{recursive:true}),
    spawnSync:(cmd,args)=>{calls.push(cmd);return cmd==='bash'
      ? {status:0,stdout:`STATUS=repaired\nRESOLVED_CLI_PATH=${process.execPath}\n`,stderr:''}
      : {status:0,stdout:JSON.stringify({success:true,html:'<article>Normal</article>'}),stderr:''};},
    admitHtmlFile:()=>({admitted:false,reason:'challenge_page'})});
  load(c,['runCloakbrowserFetch']);
  assert.equal(c.runCloakbrowserFetch('/repo','https://example.invalid',out).ok,false);
  assert.equal(calls[1],process.execPath);
  assert.equal(fs.existsSync(out),false);
});
