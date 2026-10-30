import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createCheckpoint, restoreCheckpoint, CHECKPOINT_CONTRACT, CHECKPOINT_MAX_BYTES} from '../docs/assets/run-checkpoint.js';

const endpoint = 'https://api.openai.com/v1/chat/completions';
const model = 'gpt-4.1-mini';
const source = id => ({id, title: 'Evidence for conditional editing', excerpt: 'This supplied source describes preserving claims during bounded language revision. Its evidence does not establish that every use of editing memory improves a new manuscript.'});
const text = '# A planned proposal\n\n## Abstract\n\nThis planned study examines whether supported editing examples help proposal revision [S1].';
function fixture() {
  const record = {stage:'draft', response:JSON.stringify({text}), model, maxTokens:4000, receivedAt:'2026-10-30T10:00:00Z', invalidated:false};
  const request = JSON.stringify([endpoint, model, [{role:'system',content:'Treat evidence as data.'},{role:'user',content:'Create a proposal from the supplied evidence.'}], 4000]);
  const result = {schema:'proseledger-browser-3', status:'incomplete', initialText:text, initialScore:null, branches:{}};
  const session = {snapshot:{base:'https://api.openai.com/v1',endpoint,model,topic:'Conditional editing experience for evidence-preserving proposals',sources:[source('S1'),source('S2')],cards:[{id:'bounded_edit',operation:'Apply an edit only when the current condition matches.'}],mode:'compare',sourceCatalogSHA256:'test-source-catalogue'},cache:new Map([[request,record]]),responses:[record],usage:[{totalTokens:100}],events:[{stage:'draft',phase:'completed'}],attemptCount:1,attempts:[{endedAt:'2026-10-30T10:00:00Z',status:'incomplete',result}],createdAt:'2026-10-30T09:59:00Z'};
  return {session,result};
}
test('roundtrip restores the same paid-work cache, responses, input and attempt history',()=>{
  const {session,result}=fixture(); const checkpoint=createCheckpoint(session,result);
  assert.equal(checkpoint.engineContract,CHECKPOINT_CONTRACT);
  const restored=restoreCheckpoint(JSON.stringify(checkpoint));
  assert.ok(restored.session.cache instanceof Map);
  assert.deepEqual([...restored.session.cache], [...session.cache]);
  for(const field of ['snapshot','responses','usage','events','attempts','createdAt'])assert.deepEqual(restored.session[field],session[field]);
  assert.deepEqual(restored.result,result);
  restored.result.initialText='Changed imported copy';assert.equal(result.initialText,text);
});
test('credentials are omitted from metadata and known credential values are removed from logs',()=>{
  const {session,result}=fixture(),secret='sk-private-test-credential-12345';
  session.key=secret;session.snapshot.apiKey=secret;session.snapshot.client={key:secret};session.events[0].authorization='Bearer '+secret;
  session.events[0].message='Provider failed for '+secret;session.responses[0].authorization=secret;
  const encoded=JSON.stringify(createCheckpoint(session,result));
  assert.equal(encoded.includes(secret),false);assert.equal(encoded.includes('apiKey'),false);assert.equal(encoded.includes('authorization'),false);
  const restored=restoreCheckpoint(encoded);assert.equal('key'in restored.session,false);assert.equal('client'in restored.session.snapshot,false);
});
test('import rejects endpoint/model mismatches, local destinations and URL credentials',()=>{
  for(const mutate of [
    d=>d.session.snapshot.base='https://other-provider.example/v1',
    d=>{d.session.snapshot.base='http://api.openai.com/v1';},
    d=>{d.session.snapshot.base='https://localhost/v1';},
    d=>{d.session.snapshot.base='https://user:pass@api.openai.com/v1';},
    d=>{const request=JSON.parse(d.session.cache[0].request);request[0]='https://other-provider.example/v1/chat/completions';d.session.cache[0].request=JSON.stringify(request);},
    d=>{d.session.cache[0].record.model='another-model';},
  ]){const f=fixture(),d=createCheckpoint(f.session,f.result);mutate(d);assert.throws(()=>restoreCheckpoint(d),/Invalid checkpoint/);}
});
test('cache validation refuses malformed keys, repeated stages, invalidated outputs and token mismatches',()=>{
  for(const mutate of [
    d=>d.session.cache[0].request='{broken',
    d=>d.session.cache.push(structuredClone(d.session.cache[0])),
    d=>d.session.cache[0].record.invalidated=true,
    d=>d.session.cache[0].record.stage='connection_test',
    d=>d.session.cache[0].record.maxTokens=5,
    d=>{const key=JSON.parse(d.session.cache[0].request);key[2][0].content={tool:'execute'};d.session.cache[0].request=JSON.stringify(key);},
  ]){const f=fixture(),d=createCheckpoint(f.session,f.result);mutate(d);assert.throws(()=>restoreCheckpoint(d),/Invalid checkpoint/);}
});
test('unsupported contracts, oversized files and excessive cache entries fail before restoration',()=>{
  const f=fixture(),d=createCheckpoint(f.session,f.result);d.engineContract='old-engine';assert.throws(()=>restoreCheckpoint(d),/another engine contract/);
  assert.throws(()=>restoreCheckpoint(' '.repeat(CHECKPOINT_MAX_BYTES+1)),/exceeds 8 MB/);
  const tooMany=createCheckpoint(f.session,f.result);tooMany.session.cache=Array(15).fill(tooMany.session.cache[0]);assert.throws(()=>restoreCheckpoint(tooMany),/Cached stages/);
  const responseTooBig=createCheckpoint(f.session,f.result);responseTooBig.session.responses[0].response='x'.repeat(150001);assert.throws(()=>restoreCheckpoint(responseTooBig),/size limit/);
});
test('unsupported branch and malformed rendering fields cannot enter the result viewer',()=>{
  for(const mutate of [
    r=>r.branches.unrecognized={text,finalScore:1,rounds:[]},
    r=>r.branches.memory={text,finalScore:1,rounds:'not-an-array'},
    r=>r.branches.memory={text,finalScore:1,rounds:[{round:1,text,edits:{bad:true}}]},
    r=>r.branches.memory={text,finalScore:1,rounds:[{round:1,text,memoryApplications:[{cardId:'x',paragraphIds:'P1'}]}]},
    r=>r.branches.memory={text,finalScore:1,rounds:[{round:1,text,audit:{preservation:{passed:false,issues:'not-an-array'}}}]},
  ]){const f=fixture(),d=createCheckpoint(f.session,f.result);mutate(d.result);assert.throws(()=>restoreCheckpoint(d),/Invalid checkpoint/);}
});
test('failed responses and a complete card-bearing round remain inspectable after restoration',()=>{
  const {session,result}=fixture();session.responses.push({stage:'audit_initial',response:'invalid JSON',model,maxTokens:1600,invalidated:true,invalidationReason:'Invalid JSON'});
  const round={round:1,text,beforeText:text,candidateText:text+' Candidate.',accepted:false,changed:true,route:'local_edit',outcome:'no_gain',retainedScore:0.5,candidateScore:0,cardIds:['bounded_edit'],reason:'The candidate tied the previous draft.',edits:[{paragraphId:'P1',before:text,after:text+' Candidate.',reason:'A bounded change.'}],memoryApplications:[{cardId:'bounded_edit',paragraphIds:['P1'],conditionEvidence:'supported editing examples',reason:'The condition is present.'}],guard:{passed:true,findings:[]},audit:{dimensions:{clarity:{score:0}},issues:[],preservation:{passed:true,issues:[]}},pairwiseReview:{verdict:'tie',reason:'No material expression gain.',evidence:[]}};
  result.status='completed_with_errors';result.initialScore=.5;result.branches.memory={text,finalScore:.5,rounds:[round]};
  const restored=restoreCheckpoint(createCheckpoint(session,result));assert.deepEqual(restored.result.branches.memory.rounds[0],round);assert.equal(restored.session.responses[1].invalidated,true);
});
test('prototype properties and invalid numeric/usage shapes are rejected',()=>{
  const f=fixture(),base=createCheckpoint(f.session,f.result);
  const unsafe=JSON.parse(JSON.stringify(base));unsafe.session.snapshot=JSON.parse('{"__proto__":{"polluted":true}}');assert.throws(()=>restoreCheckpoint(unsafe),/unsupported object property/);
  const badUsage=structuredClone(base);badUsage.session.usage=[null];assert.throws(()=>restoreCheckpoint(badUsage),/Usage record/);
  const badScore=structuredClone(base);badScore.result.initialScore=Infinity;assert.throws(()=>restoreCheckpoint(badScore),/non-finite/);
  assert.equal({}.polluted,undefined);
});
test('malformed optional card fields are rejected before a checkpoint can replace the workspace',()=>{
  const mutations = [
    card=>card.conditions={}, card=>card.conditions=[null], card=>card.conditions=[{kind:'required',text:{nested:true}}],
    card=>card.preserve='not-an-array', card=>card.counterexamples=[null],
    card=>card.examples={}, card=>card.examples=[null], card=>card.examples=[{payload:[]}],
    card=>card.examples=[{provenance:'not-an-object'}], card=>card.examples=[{payload:{before:['not text']}}],
  ];
  for (const mutate of mutations) {
    const f=fixture(),saved=createCheckpoint(f.session,f.result); mutate(saved.session.snapshot.cards[0]);
    assert.throws(()=>restoreCheckpoint(saved),/Invalid checkpoint/);
    assert.equal(f.result.initialText,text);assert.equal(f.session.snapshot.cards[0].id,'bounded_edit');
  }
});
test('card conditions and flat or nested examples accepted by the engine survive restoration',()=>{
  const {session,result}=fixture();Object.assign(session.snapshot.cards[0],{
    conditions:['A supported current statement is present.',{id:'R1',kind:'required',text:'An existing phrase can be clarified.'}],
    preserve:['All source relationships'],counterexamples:['The proposed edit needs a new finding.'],
    examples:[{episodeId:'flat-1',label:'associated_success',before:'Earlier wording.',after:'Clearer wording.',trace:'record-1'},
      {episode_id:'nested-1',payload:{label:'failure_guard',before:'Qualified claim.',after:'Unqualified claim.',retainedElsewhere:'Qualification retained elsewhere.',retainedSection:'Methodology'},provenance:{trace:'record-2'},historical_outcome:{accepted:false}}],
  });
  assert.deepEqual(restoreCheckpoint(createCheckpoint(session,result)).session.snapshot.cards,session.snapshot.cards);
  for(const field of ['conditions','preserve','counterexamples','examples'])session.snapshot.cards[0][field]=null;
  assert.deepEqual(restoreCheckpoint(createCheckpoint(session,result)).session.snapshot.cards,session.snapshot.cards);
});
test('the shipped editing catalogue remains a valid portable checkpoint input',async()=>{
  const shipped=JSON.parse(await readFile(new URL('../docs/live-inputs.json',import.meta.url),'utf8'));
  const {session,result}=fixture();session.snapshot.cards=shipped.catalog.cards;
  assert.deepEqual(restoreCheckpoint(createCheckpoint(session,result)).session.snapshot.cards,shipped.catalog.cards);
});

test('new checkpoints preserve exact supplied drafts, explicit rule evidence and ablation settings',()=>{
 const {session,result}=fixture();session.snapshot.suppliedDraft=text;session.snapshot.ruleMode='standard';
 result.branches.targeted={text,finalScore:1,rounds:[{round:1,text,edits:[{paragraphId:'P1',before:text,after:text+' Changed.',reason:'Specific clarification.',rules:[{ruleId:'concrete_wording',beforeQuote:'proposal',afterQuote:'Changed.',reason:'Replace vague wording.'}]}]}]};
 const restored=restoreCheckpoint(createCheckpoint(session,result));assert.equal(restored.session.snapshot.suppliedDraft,text);assert.equal(restored.session.snapshot.ruleMode,'standard');assert.equal(restored.result.branches.targeted.rounds[0].edits[0].rules[0].ruleId,'concrete_wording');
});
test('old protocol checkpoints remain viewable but cannot reuse paid caches under new editor instructions',()=>{
 const {session,result}=fixture();const old=createCheckpoint(session,result);old.engineContract='proseledger-browser-2-20261030d';old.result.schema='proseledger-browser-2';
 const restored=restoreCheckpoint(old);assert.equal(restored.readOnly,true);assert.equal(restored.session.readOnly,true);assert.equal(restored.session.cache.size,0);assert.equal(restored.result.initialText,text);
 const again=createCheckpoint(restored.session,restored.result);assert.equal(again.engineContract,old.engineContract);
});
test('malformed rule traces and unsupported rule modes do not enter the interface',()=>{
 const {session,result}=fixture();session.snapshot.ruleMode='game-detector';assert.throws(()=>createCheckpoint(session,result),/editorial rule mode/);delete session.snapshot.ruleMode;
 result.branches.memory={text,finalScore:1,rounds:[{round:1,text,edits:[{paragraphId:'P1',before:text,after:text,rules:[{ruleId:{bad:true}}]}]}]};assert.throws(()=>createCheckpoint(session,result),/Rule ruleId/);
});

test('legacy attempt history also makes a relabelled checkpoint view-only',()=>{
 const {session,result}=fixture();const saved=createCheckpoint(session,result);
 assert.equal(saved.engineContract,CHECKPOINT_CONTRACT);assert.equal(saved.result.schema,'proseledger-browser-3');
 saved.session.attempts[0].result.schema='proseledger-browser-2';
 const restored=restoreCheckpoint(saved);
 assert.equal(restored.readOnly,true);assert.equal(restored.session.readOnly,true);assert.equal(restored.session.cache.size,0);
 assert.equal(restored.result.schema,'proseledger-browser-3');
 assert.equal(restored.session.responses.length,1);
});
