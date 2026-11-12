import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {HEADINGS, RULES, PROTOCOL, parseSources, validateInput, splitSections, guard, boundedPatches, runRevision, validateCheckpoint} from '../docs/assets/revision-engine.js';
if (!globalThis.crypto) globalThis.crypto = webcrypto;
const sources = [{id:'S1',title:'Source one',excerpt:'This verified excerpt supports the proposal background and its planned evaluation.'},{id:'S2',title:'Source two',excerpt:'This verified source discusses limitations of automatic scientific revision and validation.'}];
const text = '# Evidence-preserving revision\n\n' + HEADINGS.map((heading,i) => '## '+heading+'\n\n'+`This project proposes a careful procedure for scientific revision. The proposed procedure will preserve evidence and planned study status while allowing precise phrasing [S${i%2+1}]. The study will document its limitations and compare results using verified references.`).join('\n\n');
const input = {topic:'Evidence-preserving scientific revision', draft:text, sources, policy:'section'};
const model = {endpoint:'https://api.example.com/v1/chat/completions', model:'test-model'};
function fakeClient({fail, badAudit, altered, rejectFull=false, withRepair=false}={}) {
  const stages=[];
  const fn = async (messages,{stage}) => {
    stages.push(stage);
    if(fail?.(stage,stages))throw new Error('Temporary provider failure');
    const payload=JSON.parse(messages[1].content.split('\nINPUT DATA:\n')[1]);
    if(stage==='generate_initial_proposal') return JSON.stringify({title:'Evidence-preserving revision',sections:splitSections(text).sections.map(s=>({heading:s.heading,text:s.original}))});
    if(stage.startsWith('rewrite_section_')) {
      let revised = payload.section.original.replace('a careful procedure','a clear procedure');
      if(withRepair && payload.section.id===0) revised=revised.replace('proposes','introduces');
      return JSON.stringify({text:altered?altered(payload.section,revised):revised});
    }
    if(stage==='audit_sections') return JSON.stringify({reviews:HEADINGS.map((_,id)=>({id,approve:!(withRepair&&id===0),readability:'similar',issues:withRepair&&id===0?[{originalQuote:'proposes',revisedQuote:'introduces',problem:'Preserve the proposed status.'}]:[]})).slice(0,badAudit?5:6)});
    if(stage==='repair_section_findings') return JSON.stringify({sections:[{id:0,patches:[{before:'introduces',after:'proposes',issueIndex:0}],reason:'Restore planned status.'}]});
    if(stage.startsWith('audit_')) return JSON.stringify({contentPreserved:!rejectFull,readability:'similar',issues:rejectFull?[{section:'Abstract',originalQuote:'careful',revisedQuote:'clear',problem:'Test unresolved meaning change'}]:[],reason:'Equivalent meaning in the fixture.'});
    throw new Error('Unexpected stage '+stage);
  };
  fn.stages=stages;return fn;
}

test('source parser and input use bounded explicit evidence',()=>{
  assert.deepEqual(parseSources(sources.map(s=>`[${s.id}] ${s.title}\n${s.excerpt}`).join('\n\n')),sources);
  assert.deepEqual(parseSources(JSON.stringify({sources})),sources);
  assert.throws(()=>parseSources('[S1] One\nshort'),/2–10/);
  assert.throws(()=>validateInput({...input,sources:[sources[0],sources[0]]}),/unique/);
  assert.throws(()=>validateInput({...input,policy:'fake'}),/repair/);
  assert.equal(RULES.length,6);
});

test('guard catches citation, numeric and completed-work changes',()=>{
  assert.equal(guard('',text,sources).passed,true);
  assert.equal(guard(text,text.replaceAll('[S2]','[S9]'),sources).passed,false);
  assert.equal(guard(text,text.replace('a careful','42 careful'),sources).passed,false);
  assert.equal(guard(text,text.replace('This project proposes','We found'),sources).passed,false);
  assert.throws(()=>splitSections(text.replace('## Related Work','## Wrong')),/six required/);
});

test('bounded patches reject ambiguous, overlapping or excessive edits',()=>{
  const body='The proposed procedure will preserve scope and evidence. Other content remains unchanged.';
  assert.equal(boundedPatches(body,[{before:'proposed',after:'planned',issueIndex:0}],1).ok,true);
  assert.equal(boundedPatches('word word',[{before:'word',after:'clear',issueIndex:0}],1).reason,'ambiguous_anchor');
  assert.equal(boundedPatches(body,[{before:body,after:'Replacement',issueIndex:0}],1).reason,'coverage');
  assert.equal(boundedPatches(body,[{before:'proposed procedure',after:'x',issueIndex:0},{before:'procedure',after:'y',issueIndex:0}],1).reason,'overlap');
  assert.equal(boundedPatches(body,[{before:'proposed',after:'planned',issueIndex:9}],1).reason,'issue_index');
});

test('complete generate-to-retained workflow records real edits and no memory claims',async()=>{
  const client=fakeClient(); const snapshots=[];
  const run=await runRevision({...input,draft:''},{callModel:client,model,onUpdate:r=>snapshots.push(r)});
  assert.equal(run.status,'completed'); assert.equal(client.stages.length,9);
  assert.equal(run.changedSections,6);assert.equal(run.retainedSource,'candidate');
  assert.equal(run.ledger.memoryCardsUsed,0); assert.equal(run.ledger.detectorUsedForAdmission,false);
  assert.equal(run.ledger.edits.length,6); assert.equal(run.ledger.retainedSHA256.length,64);
  assert.equal(run.checks.eligible,true);assert.equal(run.checks.audit.readability,'similar');
  assert.equal(run.responses.length,9);assert.equal(snapshots[0].initial,'');
  assert.equal(run.protocol,PROTOCOL);assert.doesNotMatch(JSON.stringify(run),/apiKey|authorization/i);
});

test('bounded repair is actually applied and included in retained ledger',async()=>{
  const run=await runRevision(input,{callModel:fakeClient({withRepair:true}),model});
  assert.equal(run.sections[0].repair.ok,true);
  assert.match(run.sections[0].candidate,/introduces/);
  assert.match(run.sections[0].retained,/proposes/);
  assert.equal(run.sections[0].status,'verified_edit');
});

test('unresolved full-audit issues restore original, even after better-looking edits',async()=>{
  const run=await runRevision(input,{callModel:fakeClient({rejectFull:true}),model});
  assert.equal(run.retained,text);assert.equal(run.retainedSource,'original');
  assert.equal(run.changedSections,0);assert.equal(run.checks.eligible,false);
  assert.notEqual(run.candidate,text);assert.match(run.checks.reasons.join(' '),/Unresolved/);
});

test('resume reuses validated stages and binds input plus both model IDs',async()=>{
  let saved;const first=fakeClient({fail:stage=>stage==='rewrite_section_3'});
  await assert.rejects(runRevision(input,{callModel:first,model,onUpdate:r=>saved=r}),/Temporary/);
  assert.equal(saved.status,'failed'); assert.equal(saved.responses.length,2);
  assert.equal(saved.retained,text);
  const second=fakeClient();const completed=await runRevision(input,{callModel:second,model,resume:saved});
  assert.equal(completed.cachedCalls,2);assert.equal(second.stages[0],'rewrite_section_3');
  assert.equal(completed.totalCompletedCalls,8);
  await assert.rejects(runRevision({...input,topic:'Different input'},{callModel:fakeClient(),model,resume:saved}),/Resume requires/);
  await assert.rejects(runRevision(input,{callModel:fakeClient(),model:{...model,writerModel:'different-writer'},resume:saved}),/Resume requires/);
});

test('invalid schema never enters cache and resume retries failed review',async()=>{
  let saved;
  await assert.rejects(runRevision(input,{callModel:fakeClient({badAudit:true}),model,onUpdate:r=>saved=r}),/missing or duplicate/);
  assert.equal(saved.responses.length,6);
  const next=fakeClient();const result=await runRevision(input,{callModel:next,model,resume:saved});
  assert.equal(next.stages[0],'audit_sections');assert.equal(result.cachedCalls,6);
});

test('tampered response hashes are discarded instead of trusted',async()=>{
  const done=await runRevision(input,{callModel:fakeClient(),model});
  done.responses[0].text='{"text":"fabricated"}';
  const client=fakeClient();const next=await runRevision(input,{callModel:client,model,resume:done});
  assert.equal(client.stages[0],'rewrite_section_1');assert.equal(next.status,'completed');
});

test('cancellation retains initial draft and makes no later calls',async()=>{
  const controller=new AbortController();const base=fakeClient();let saved;
  const client=async(m,o)=>{const r=await base(m,o);controller.abort();return r;};
  await assert.rejects(runRevision(input,{callModel:client,model,signal:controller.signal,onUpdate:r=>saved=r}),{name:'AbortError'});
  assert.equal(base.stages.length,1);assert.equal(saved.retained,text);assert.equal(saved.status,'cancelled');
});

test('checkpoint import rejects old formats, duplicate stages and unbounded metadata',async()=>{
  const run=await runRevision(input,{callModel:fakeClient(),model});
  assert.equal(validateCheckpoint(run).protocol,PROTOCOL);
  assert.throws(()=>validateCheckpoint({...run,protocol:'old'}),/compatible/);
  assert.throws(()=>validateCheckpoint({...run,responses:[...run.responses,run.responses[0]]}),/duplicated/);
  assert.throws(()=>validateCheckpoint({...run,initial:'x'.repeat(19000)}),/record fields/);
  const imported=validateCheckpoint({...run,apiKey:'MUST_NOT_SURVIVE',model:{...run.model,key:'MUST_NOT_SURVIVE'}});
  assert.doesNotMatch(JSON.stringify(imported),/MUST_NOT_SURVIVE/);
  assert.throws(()=>validateCheckpoint({...run,sections:{bad:true}}),/record fields/);
  assert.throws(()=>validateCheckpoint({...run,attemptHistory:'bad'}),/record fields/);
  assert.throws(()=>validateCheckpoint({...run,checks:{...run.checks,guard:{passed:true,findings:'bad'}}}),/record fields/);
  const nested=structuredClone(run);nested.sections[0].apiKey='MUST_NOT_SURVIVE';nested.checks.audit.secret='MUST_NOT_SURVIVE';
  assert.doesNotMatch(JSON.stringify(validateCheckpoint(nested)),/MUST_NOT_SURVIVE/);
});

test('extended repair re-audits bounded fixes and stops when content is preserved',async()=>{
  const base=fakeClient();const stages=[];
  const callModel=async(messages,options)=>{
    stages.push(options.stage);
    if(options.stage==='audit_full_revision')return JSON.stringify({contentPreserved:false,issues:[{section:'Abstract',originalQuote:'careful',revisedQuote:'clear',problem:'Retain the stated methodological qualification.'}],readability:'similar',reason:'Repair required.'});
    if(options.stage==='repair_full_findings_1')return JSON.stringify({sections:[{id:0,patches:[{before:'a clear procedure',after:'a careful procedure',issueIndex:0}],reason:'Restore qualification.'}]});
    return base(messages,options);
  };
  const run=await runRevision({...input,policy:'full-audit'},{callModel,model});
  assert.equal(run.status,'completed');assert.equal(run.ledger.repairHistory.length,1);
  assert.ok(stages.includes('audit_repaired_full_1'));
  assert.ok(!stages.includes('repair_full_findings_2'));
  assert.equal(run.sections[0].retained,run.sections[0].original);
  assert.equal(run.changedSections,5);
  assert.equal(validateCheckpoint(run).ledger.repairHistory[0].changes[0].ok,true);
});

test('a malformed repair cannot change the manuscript outside a valid anchor',async()=>{
  const base=fakeClient({withRepair:true});
  const callModel=async(messages,options)=> options.stage==='repair_section_findings'
    ? JSON.stringify({sections:[{id:0,patches:[{before:'absent text',after:'invented fact',issueIndex:0}],reason:'Invalid fixture.'}]})
    :base(messages,options);
  const run=await runRevision(input,{callModel,model});
  assert.equal(run.sections[0].repair.ok,false);
  assert.equal(run.sections[0].retained,run.sections[0].original);
  assert.doesNotMatch(run.retained,/invented fact/);
});
