/** Browser interaction tests use synthetic HTTP fixtures only.
 * They verify product behavior; they are not model-quality experiments.
 * Run with Playwright available and optionally PLAYWRIGHT_EXECUTABLE_PATH.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdtemp, mkdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const root = fileURLToPath(new URL('../docs/', import.meta.url));
const KEY = 'browser-fixture-secret-never-export';
const DETECTOR_KEY = 'synthetic-detector-secret-never-export';
const ARTIFACTS = process.env.PROSELEDGER_BROWSER_ARTIFACTS || null;
const HEADINGS = ['Abstract','Introduction','Related Work','Methodology','Planned Evaluation','Limitations and Conclusion'];
const sections = HEADINGS.map((heading,id) => ({heading,text:[
  `This section describes the proposed revision study in order to make its evidence-preservation objective clear.`,
  `The planned method will compare original and revised wording while retaining qualifications, source attribution, and methodological limitations.`,
  `The study will use supplied notes and will not treat a fluent sentence as evidence that its scientific claim is correct [S${id % 2 + 1}].`,
  `The evaluation remains planned, and the proposed comparison does not establish any experimental result.`
].join(' ')}));
const sources = [{id:'S1',title:'Evidence-preserving editing',excerpt:'This synthetic source describes checking that a revised document retains the claims and qualifications already supported by supplied evidence. It does not establish that fluent prose is factually correct.'}, {id:'S2',title:'Review before retention',excerpt:'This synthetic source proposes comparing an edited text with its original and checking source attribution and research status before retaining a change. No completed evaluation result is reported.'}];
const notes = sources.map(s=>`[${s.id}] ${s.title}\n${s.excerpt}`).join('\n\n');
const title = 'A proposal <img src=x onerror="window.injected=true">';
const initial = '# '+title+'\n\n'+sections.map(s=>'## '+s.heading+'\n\n'+s.text).join('\n\n');
function payload(body) {
  const raw=body.messages.at(-1).content;
  const split=raw.lastIndexOf('INPUT DATA:');
  if(split<0) return {instruction:raw,data:{}};
  return {instruction:raw.slice(0,split),data:JSON.parse(raw.slice(split+'INPUT DATA:'.length).trim())};
}
function responseFor(body, context) {
  const {instruction,data}=payload(body);
  if(instruction.startsWith('Write one coherent')) return {stage:'generate_initial_proposal',value:{title,sections}};
  if(instruction.startsWith('Copy-edit only')) {
    const section=data.section;
    let text=section.original.replace('in order to','to');
    if(section.id===0 && context.repair) text=text.replace('The evaluation remains planned','The evaluation was completed');
    return {stage:'rewrite_section_'+(section.id+1),value:{text}};
  }
  if(instruction.startsWith('Independently review each')) return {stage:'audit_sections',value:{reviews:data.sections.map(s=>({id:s.id,approve:!(s.id===0&&context.repair),issues:s.id===0&&context.repair?[{originalQuote:'The evaluation remains planned',revisedQuote:'The evaluation was completed',problem:'The candidate changes planned work into completed work.'}]:[],readability:'better'}))}};
  if(instruction.startsWith('Repair only')) return {stage:'repair',value:{sections:data.sections.map(s=>({id:s.id,patches:[{before:'The evaluation was completed',after:'The evaluation remains planned',issueIndex:0}],reason:'Restore the original research status.'}))}};
  if(instruction.startsWith('Independently verify')) return {stage:'audit_full_revision',value:{contentPreserved:!context.rejectFull,issues:context.rejectFull?[{section:'Methodology',originalQuote:'retaining qualifications',revisedQuote:'retaining qualifications',problem:'Synthetic rejection fixture: source support requires manual inspection.'}]:[],readability:context.rejectFull?'worse':'better',reason:context.rejectFull?'The fixture rejects this candidate.':'The candidate preserves supplied meanings and removes redundant wording.'}};
  return {stage:'test_connection',value:{ok:true}};
}
async function downloadJSON(page, selector) {
  const waiting=page.waitForEvent('download'); await page.click(selector);
  const download=await waiting;
  const text=await readFile(await download.path(),'utf8');
  assert.ok(!text.includes(KEY),'credentials must not appear in exported JSON');
  assert.ok(!text.includes(DETECTOR_KEY),'detector keys must not appear in exported JSON');
  return JSON.parse(text);
}
async function installFixture(page, options={}) {
  const requests=[];let failed=false;
  await page.route('https://api.openai.com/**',async route=>{
    const request=route.request();
    if(request.method()==='OPTIONS'){await route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'}});return;}
    assert.equal(request.headers().authorization,`Bearer ${KEY}`);
    const body=request.postDataJSON();
    const result=responseFor(body,options);
    requests.push({stage:result.stage,body});
    assert.ok(!JSON.stringify(body).includes(KEY),'key belongs only in request auth header');
    if(options.failAuditOnce && result.stage==='audit_sections'&&!failed){failed=true;await route.fulfill({status:401,json:{error:{message:'synthetic auth fixture'}}});return;}
    if(options.delayAt===result.stage)await new Promise(resolve=>setTimeout(resolve,700));
    try{await route.fulfill({status:200,json:{model:'synthetic-browser-fixture',choices:[{index:0,message:{content:JSON.stringify(result.value)},finish_reason:'stop'}],usage:{prompt_tokens:100,completion_tokens:40,total_tokens:140}}});}catch(error){if(!/closed|handled|cancel/i.test(error.message))throw error;}
  });
  return requests;
}
async function fill(page,{existing=true,provider='openai'}={}) {
  await page.selectOption('#provider-preset',provider);
  await page.fill('#topic','Preserving scientific evidence when revising research proposals');
  await page.fill('#source-notes',notes);
  if(existing)await page.fill('#supplied-draft',initial);
  await page.fill('#api-key',KEY);await page.check('#consent');
}
async function waitFinished(page) {
  await page.waitForFunction(()=>document.querySelector('#generate')?.disabled===false && !document.querySelector('#results-panel')?.hidden,{},{timeout:15000});
}

let server,browser,base,temporary;
test.before(async()=>{
  temporary=await mkdtemp(path.join(tmpdir(),'proseledger-browser-'));
  if(ARTIFACTS)await mkdir(ARTIFACTS,{recursive:true});
  server=createServer(async(req,res)=>{
    try{
      const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
      const resolved=path.resolve(root,'.'+pathname);
      if(!resolved.startsWith(root)){res.writeHead(403);res.end();return;}
      const data=await readFile(resolved);
      const type={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'}[path.extname(resolved)]||'application/octet-stream';
      res.writeHead(200,{'Content-Type':type});res.end(data);
    }catch{res.writeHead(404);res.end('Not found');}
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',()=>{server.off('error',reject);resolve();});});base='http://127.0.0.1:'+server.address().port;
  browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_EXECUTABLE_PATH?{executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH}:{}),args:['--disable-gpu']});
});
test.after(async()=>{await browser?.close();if(server?.listening)await new Promise(resolve=>server.close(resolve));if(temporary)await rm(temporary,{recursive:true,force:true});});
async function pageFor(t,options={}){
  const context=await browser.newContext({acceptDownloads:true,viewport:{width:1440,height:1000}});
  t.after(()=>context.close());const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const localRequests=[];await page.route(/^http:\/\/(?:127\.0\.0\.1|localhost):1143[467]\//,async route=>{localRequests.push(route.request().url());await route.abort();});
  const requests=await installFixture(page,options);await page.goto(base+'/'+(options.page||'revise.html'));
  await page.waitForFunction(()=>document.querySelector('#source-notes')?.value.length>0);
  t.after(()=>assert.deepEqual(localRequests,[],'API-only pages must never contact local model services'));
  return{page,requests,localRequests,errors};
}

test('supplied-proposal revision applies bounded repair, exports exact retention and displays model text safely',async t=>{
  const{page,requests,errors}=await pageFor(t,{repair:true});
  if(ARTIFACTS)await page.screenshot({path:path.join(ARTIFACTS,'initial-desktop.png'),fullPage:true});
  await fill(page);await page.click('#generate');await waitFinished(page);
  assert.equal(await page.inputValue('#api-key'),'');
  const run=await downloadJSON(page,'#download-run');
  assert.equal(run.status,'completed');assert.notEqual(run.initial,run.retained);
  assert.equal(await page.locator('#manuscript-tabs [aria-selected=true]').innerText(),'Retained');
  assert.match(run.retained,/The evaluation remains planned/);assert.doesNotMatch(run.retained,/The evaluation was completed/);
  assert.equal(requests.filter(x=>x.stage.startsWith('rewrite_section_')).length,6);
  assert.equal(requests.filter(x=>x.stage==='repair').length,1);
  assert.equal(requests.filter(x=>x.stage==='audit_full_revision').length,1);
  assert.equal(run.ledger.memoryCardsUsed,0);
  assert.equal(await page.evaluate(()=>Boolean(window.injected)),false);
  assert.equal(await page.locator('#manuscript-text img').count(),0);
  const ledger=await downloadJSON(page,'#download-ledger');assert.equal(ledger.retainedSHA256,run.ledger.retainedSHA256);
  assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);
  if(ARTIFACTS){await page.screenshot({path:path.join(ARTIFACTS,'result-fixture-desktop.png'),fullPage:true});await page.locator('#results-panel').screenshot({path:path.join(ARTIFACTS,'result-fixture-detail.png')});}
  assert.deepEqual(errors,[]);
});

test('failure retains partial work; resume reuses completed responses without repeated rewrite calls',async t=>{
  const{page,requests,errors}=await pageFor(t,{failAuditOnce:true});await fill(page);await page.click('#generate');
  await page.locator('#error-panel').waitFor({state:'visible'});assert.equal(await page.inputValue('#api-key'),'');
  const checkpoint=await downloadJSON(page,'#download-checkpoint');assert.ok(checkpoint.responses.length>=6);
  await page.reload();await page.waitForFunction(()=>document.querySelector('#source-notes')?.value.length>0);
  await page.selectOption('#provider-preset','openai');
  await page.fill('#api-key','an-unrelated-provider-credential');await page.check('#consent');
  await page.locator('#restore-run').setInputFiles({name:'checkpoint.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(checkpoint))});
  await page.waitForTimeout(100);assert.equal(await page.inputValue('#api-key'),'');assert.equal(await page.isChecked('#consent'),false);
  await page.fill('#api-key',KEY);await page.check('#consent');await page.click('#resume');await waitFinished(page);
  const run=await downloadJSON(page,'#download-run');assert.equal(run.status,'completed');
  assert.equal(requests.filter(x=>x.stage==='generate_initial_proposal').length,0);
  assert.equal(requests.filter(x=>x.stage.startsWith('rewrite_section_')).length,6);
  assert.equal(requests.filter(x=>x.stage==='audit_sections').length,2);
  assert.deepEqual(errors,[]);
});

test('failed final audit restores original instead of presenting candidate as accepted',async t=>{
  const{page,errors}=await pageFor(t,{rejectFull:true});await fill(page,{existing:true});await page.fill('#topic','');await page.selectOption('#policy','section');await page.click('#generate');await waitFinished(page);
  const run=await downloadJSON(page,'#download-run');assert.equal(run.retained,run.initial);assert.notEqual(run.candidate,run.initial);
  assert.match(await page.locator('#result-summary').innerText(),/original|restor/i);assert.deepEqual(errors,[]);
});

test('invalid inputs do not invoke paid model; mobile layout has no horizontal overflow',async t=>{
  const{page,requests,errors}=await pageFor(t);await fill(page);await page.fill('#source-notes','[S1] Too short\nshort');
  await page.click('#generate');await page.waitForTimeout(100);assert.equal(requests.length,0);
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(50);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
  await page.screenshot({path:path.join(ARTIFACTS||temporary,'mobile-validation.png'),fullPage:true});assert.deepEqual(errors,[]);
});


test('Stop interrupts an in-flight request while preserving the original and completed steps',async t=>{
  const{page,requests,errors}=await pageFor(t,{delayAt:'rewrite_section_2'});await fill(page);await page.click('#generate');
  const deadline=Date.now()+5000;while(!requests.some(x=>x.stage==='rewrite_section_2')&&Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,10));
  assert.ok(requests.some(x=>x.stage==='rewrite_section_2'));await page.click('#cancel');
  await page.waitForFunction(()=>document.querySelector('#generate')?.disabled===false);
  const checkpoint=await downloadJSON(page,'#download-checkpoint');assert.equal(checkpoint.status,'cancelled');assert.equal(checkpoint.retained,checkpoint.initial);
  assert.equal(checkpoint.responses.filter(x=>x.stage==='rewrite_section_1').length,1);assert.equal(await page.inputValue('#api-key'),'');assert.deepEqual(errors,[]);
});


test('API-only pages expose no native controls, scripts or local-service CSP destinations',async t=>{
  for(const name of ['create.html','revise.html']){
    const {page,requests,errors}=await pageFor(t,{page:name});
    assert.equal(await page.inputValue('#provider-preset'),'openai');
    assert.equal(await page.locator('#native-token, #native-base, #native-model, #writer-backend, #ollama-base, #test-ollama').count(),0);
    assert.equal(await page.locator('#provider-preset option[value=codex]').count(),0);
    const csp=await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');assert.doesNotMatch(csp,/localhost|127\.0\.0\.1|1143[467]/);
    const resources=await page.evaluate(()=>performance.getEntriesByType('resource').map(x=>x.name));assert.ok(!resources.some(x=>/native-client|ollama-client/.test(x)));
    assert.equal(requests.length,0);assert.deepEqual(errors,[]);
  }
});

test('optional section writer uses its selected API model while review and repair stay on the main model',async t=>{
  const {page,requests,errors}=await pageFor(t,{repair:true});await fill(page);
  await page.locator('details.endpoint').evaluate(element=>element.open=true);
  await page.fill('#writer-model','synthetic-section-writer');await page.click('#generate');await waitFinished(page);
  const run=await downloadJSON(page,'#download-run');assert.equal(run.status,'completed');
  const writers=requests.filter(x=>x.stage.startsWith('rewrite_section_')),reviewers=requests.filter(x=>!x.stage.startsWith('rewrite_section_'));
  assert.equal(writers.length,6);assert.ok(writers.every(x=>x.body.model==='synthetic-section-writer'));
  assert.deepEqual(reviewers.map(x=>x.stage),['audit_sections','repair','audit_full_revision']);assert.ok(reviewers.every(x=>x.body.model==='gpt-4.1-mini'));
  assert.equal(run.model.writerModel,'synthetic-section-writer');assert.equal(run.model.model,'gpt-4.1-mini');assert.deepEqual(errors,[]);
});

test('create generates once through the API and hands exact proposal and sources to revision without credentials',async t=>{
  const {page,requests,errors}=await pageFor(t,{page:'create.html'});await fill(page,{existing:false});
  await page.click('#generate');await waitFinished(page);
  const generated=await downloadJSON(page,'#download-draft-record');assert.equal(generated.status,'completed');assert.equal(generated.initial,initial);
  assert.deepEqual(requests.map(x=>x.stage),['generate_initial_proposal']);assert.equal(await page.inputValue('#api-key'),'');
  await page.click('#continue-revision');await page.waitForURL('**/revise.html');await page.waitForFunction(()=>document.querySelector('#supplied-draft')?.value.length>300);
  assert.equal(await page.inputValue('#supplied-draft'),generated.initial);assert.equal(await page.inputValue('#source-notes'),notes);assert.equal(await page.inputValue('#api-key'),'');
  assert.equal(await page.evaluate(()=>sessionStorage.getItem('proseledger-proposal-handoff-v1')),null);
  assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);
  await page.fill('#api-key',KEY);await page.check('#consent');await page.click('#generate');await waitFinished(page);
  const revised=await downloadJSON(page,'#download-run');assert.equal(revised.initial,generated.initial);assert.notEqual(revised.retained,revised.initial);
  assert.equal(requests.filter(x=>x.stage==='generate_initial_proposal').length,1);assert.equal(requests.filter(x=>x.stage.startsWith('rewrite_section_')).length,6);
  const pending=page.waitForEvent('download');await page.click('#download-manuscript');const file=await pending;assert.equal(await readFile(await file.path(),'utf8'),revised.retained);
  assert.deepEqual(errors,[]);
});

test('local-runtime checkpoints are rejected explicitly instead of silently converted to API resumes',async t=>{
  const {page,requests,errors}=await pageFor(t);await fill(page);await page.click('#generate');await waitFinished(page);
  const saved=await downloadJSON(page,'#download-run'),paid=requests.length;
  for(const localModel of [
    {primaryBackend:'codex',endpoint:'http://127.0.0.1:11437',model:'account-default',writerBackend:'none',writerModel:'none'},
    {endpoint:'https://api.openai.com/v1/chat/completions',model:'gpt-4.1-mini',writerBackend:'ollama',writerModel:'qwen2.5:7b-instruct-q4_K_M',writerBase:'http://127.0.0.1:11436',writerDigest:'845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'}
  ]){
    const checkpoint={...saved,model:localModel};
    await page.locator('#restore-run').setInputFiles({name:'local-runtime.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(checkpoint))});
    await page.locator('#error-panel').waitFor({state:'visible'});assert.match(await page.locator('#error-message').innerText(),/local|Codex|Ollama|API/i);assert.equal(requests.length,paid);
  }
  assert.deepEqual(errors,[]);
});

test('optional GPTZero checks original and retained snapshots without changing the manuscript or exporting keys',async t=>{
  const {page,requests,errors}=await pageFor(t);const detector=[];
  await page.route('https://api.gptzero.me/v2/predict/text',async route=>{
    const req=route.request();if(req.method()==='OPTIONS'){await route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'}});return;}
    assert.equal(req.headers()['x-api-key'],DETECTOR_KEY);assert.equal(req.headers().authorization,undefined);
    const body=req.postDataJSON();assert.deepEqual(Object.keys(body),['document']);assert.ok(!JSON.stringify(body).includes(DETECTOR_KEY));detector.push(body.document);
    await route.fulfill({status:200,json:{version:'synthetic-fixture',documents:[{class_probabilities:{human:.5,mixed:.2,ai:.3},predicted_class:'human',confidence_category:'synthetic'}]}});
  });
  await fill(page);await page.click('#generate');await waitFinished(page);const run=await downloadJSON(page,'#download-run'),modelCalls=requests.length;
  const panel=page.locator('#external-validation-panel');await panel.locator('summary').click();
  for(const version of ['initial','retained']){
    await panel.getByLabel('Proposal to check').selectOption(version);await panel.getByLabel('GPTZero API key').fill(DETECTOR_KEY);await panel.locator('input[type=checkbox]').check();
    await panel.getByRole('button',{name:'Check selected text',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#external-validation-panel [role=status]').textContent.startsWith('Observation saved'));
    assert.equal(await panel.getByLabel('GPTZero API key').inputValue(),'');assert.equal(await panel.locator('input[type=checkbox]').isChecked(),false);
  }
  assert.deepEqual(detector,[run.initial,run.retained]);assert.equal(requests.length,modelCalls);
  const pending=page.waitForEvent('download');await panel.getByRole('button',{name:'Download detector observations',exact:true}).click();const file=await pending;const text=await readFile(await file.path(),'utf8');assert.ok(!text.includes(DETECTOR_KEY)&&!text.includes(KEY));
  const observations=JSON.parse(text);assert.equal(observations.observations.length,2);assert.ok(observations.observations.every(o=>o.currentDocumentMatch==='current'&&o.runId===run.id));
  const after=await downloadJSON(page,'#download-run');assert.equal(after.retained,run.retained);assert.deepEqual(errors,[]);
});
