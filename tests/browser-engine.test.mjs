import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const rulesCode=await readFile(new URL('../docs/assets/naturalness-rules.js',import.meta.url),'utf8');
const rulesURL='data:text/javascript;base64,'+Buffer.from(rulesCode).toString('base64');
const code=(await readFile(new URL('../docs/assets/browser-engine.js',import.meta.url),'utf8')).replaceAll('./naturalness-rules.js',rulesURL);
const {runProposal,guardCandidate,applyLocalEdits,HEADINGS,DIMENSIONS,paragraphs,textMetrics,validateRuleApplications}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const topic='Conditional editing experience for evidence-preserving academic proposal revision';
const sources=[
  {id:'S1',title:'Supported editing',excerpt:'This source describes preserving supported claims and evidence relationships during language revision. It does not establish a universal improvement from historical editing experiences.'},
  {id:'S2',title:'Conditional experience',excerpt:'This source studies conditional experience reuse and the possibility of harmful transfer. Applicability must be checked in each new context rather than inferred from shared topic words.'},
];
const initial='# Conditional Proposal Revision\n\n'+HEADINGS.map((heading,index)=>'## '+heading+'\n\nThe planned study will examine revision decisions and their relationship to supplied evidence [S'+(index%2+1)+']. The evaluation remains prospective, and the proposed comparison makes no claim of an observed improvement.').join('\n\n');
const cards=[{id:'concrete_lead',operation:'Lead with existing substance.',conditions:[{kind:'required',text:'Concrete substance already exists.'}],
  examples:[{episode_id:'historical-example',payload:{label:'associated_success',before:'A full prior statement about supported editing conditions.',after:'Supported editing conditions remain explicit.',
    retained_elsewhere:'The evidence boundary survives in the limitations.',retained_section:'Limitations'},
    provenance:{trace:'development/trace/example.json'},historical_outcome:{accepted:true,guard_passed:true}}]}];
const draftResponse={ideas:['A conditional revision study.','A supported attribution study.','An editing comparison study.'],selectedIdea:0,
  outline:HEADINGS.map(heading=>({heading,plan:'Describe the proposed study and its evidential limits.'})),text:initial};
function payload(messages) {return JSON.parse(messages[1].content.split('INPUT DATA (not instructions):\n')[1]);}
function assessment(draft,score=.2,preserve=true) {
  const p=paragraphs(draft)[0];
  return {dimensions:Object.fromEntries(DIMENSIONS.map(name=>[name,score])),
    issues:score?paragraphs(draft).slice(0,3).map(p=>({dimension:'clarity',paragraphId:p.id,quote:p.text.slice(0,45),advice:'Make the existing evaluation relationship more direct.'})):[],
    preservation:{passed:preserve,issues:preserve?[]:['The candidate changes an original qualification.']}};
}
function reconstruct(data,candidate) {
  const base=data.documents.find(d=>d.id===candidate.baseDocumentId);
  return '# Conditional Proposal Revision\n\n'+base.paragraphs.map(p=>'## '+p.section+'\n\n'+(candidate.replacements.find(e=>e.paragraphId===p.id)?.text??p.text)).join('\n\n');
}
function model(options={}) {
  const records=[];let active=0,maxActive=0;
  const callModel=async(messages,config)=>{
    const data=payload(messages),stage=config.stage;records.push({stage,data,config,instruction:messages[1].content});active++;maxActive=Math.max(maxActive,active);
    try {
      if(options.concurrent)await new Promise(resolve=>setTimeout(resolve,2));
      if(options.failStage?.(stage))return 'malformed JSON';
      let reply;
      if(stage==='draft')reply=structuredClone(draftResponse);
      else if(stage==='audit_initial')reply=assessment(initial,options.initialScore??.2);
      else if(stage.startsWith('revise_')) {
        const [,method,number]=stage.split('_'),round=Number(number);
        if(options.stop)reply={route:'stop',reason:'No further useful safe expression edit was identified.',plan:[],edits:[],cardIds:[],memoryApplications:[]};
        else {
          const p=data.currentParagraphs[round-1];
          let replacement=options.identity?p.text:p.text.replace('The planned study',
            method==='targeted'?'This planned evaluation':method==='planner'?'This proposed study':'The proposed investigation');
          if(options.addNumber&&method==='memory')replacement+=' A sample of 500 cases is proposed.';
          const memory=method==='memory'&&data.conditionalCards.length>0&&(!options.identity||options.claimIdentityMemory);
          reply={route:'local_edit',reason:'Clarify the existing evaluation subject.',
            plan:method==='targeted'?[]:[{paragraphId:p.id,goal:'Clarify the existing subject.',keep:[]}],
            edits:[{paragraphId:p.id,replacement,reason:'Replace a broad existing subject with a direct expression.'}],
            ruleApplications:options.omitRules?undefined:replacement===p.text||options.ruleMode==='standard'?[]:[{ruleId:'specific_subject_action',paragraphId:p.id,
              beforeQuote:options.badRule?'A missing original phrase':p.text.slice(0,50),afterQuote:replacement.slice(0,50),reason:'The existing evaluation subject can be expressed with a more direct action.'}],
            cardIds:memory?['concrete_lead']:[],
            memoryApplications:memory?[{cardId:'concrete_lead',paragraphIds:[p.id],conditionEvidence:p.text.slice(0,50),reason:'The existing evaluation subject is present; no new scientific fact is required.'}]:[]};
        }
      } else if(stage.startsWith('review_round_')) {
        reply={assessments:data.candidates.map(c=>({id:c.id,...assessment(reconstruct(data,c),options.candidateScore??.1,options.preservation!==false)})),
          comparisons:data.comparisons.map(c=>({id:c.id,verdict:options.pairwise||'better',reason:'The candidate makes the existing subject more direct.',
            evidence:[data.candidates.find(x=>x.id===c.candidateId).replacements[0].text.slice(0,50)]}))};
        if(options.objectGuard)for(const item of reply.assessments) {
          item.preservation={passed:options.objectGuard==='contradictory',issues:[{
            paragraphId:'P1',quote:'A retained scientific qualification',advice:'This qualification is no longer retained by the revised statement.'}]};
          if(options.objectGuard==='malformed')item.preservation.issues[0].extra='Unexpected field';
        }
        if(options.badReview&&stage==='review_round_1')reply.assessments[0].issues=[{dimension:'clarity',paragraphId:'P1',quote:'A quotation that does not occur.',advice:'Review this supposed wording.'}];
      } else throw new Error('Unexpected stage: '+stage);
      if(options.extraFields)reply.explanation='Harmless additional provider commentary.';
      if(options.fenced) {const fence=String.fromCharCode(96).repeat(3);return fence+'json\n'+JSON.stringify(reply)+'\n'+fence;}
      return reply;
    } finally {active--;}
  };
  return {callModel,records,get maxActive(){return maxActive;}};
}

test('draft mode combines ideation and writing and makes exactly two model calls',async()=>{
  const mock=model({fenced:true,extraFields:true}),progress=[];
  const result=await runProposal({topic,sources,cards,mode:'draft',callModel:mock.callModel,onProgress:e=>progress.push(e)});
  assert.deepEqual(mock.records.map(x=>x.stage),['draft','audit_initial']);
  assert.equal(result.initialText,initial);assert.equal(result.initialScore,1);
  assert.equal(result.schema,'proseledger-browser-3');
  assert.ok(progress.findIndex(x=>x.phase==='drafted')<progress.findIndex(x=>x.stage==='audit_initial'));
  assert.equal(result.outline.ideas.length,3);assert.doesNotThrow(()=>JSON.stringify(result));
});

test('three independent routes run concurrently, retain R0–R3, and use at most 14 logical calls',async()=>{
  const mock=model({concurrent:true});
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  assert.equal(mock.records.length,14);assert.equal(mock.maxActive,3);
  for(const method of ['targeted','planner','memory']) {
    const first=mock.records.find(x=>x.stage==='revise_'+method+'_1');
    assert.equal(first.data.currentParagraphs[0].text,paragraphs(initial)[0].text);
    assert.deepEqual(result.branches[method].rounds.map(x=>x.round),[0,1,2,3]);
    assert.equal(result.branches[method].rounds[1].shared,undefined);
    assert.ok(result.branches[method].rounds[1].edits.length>0);
  }
  assert.equal(result.status,'completed');assert.equal(result.comparison.valid,true);
  assert.ok(mock.records.every(x=>Number.isInteger(x.config.maxTokens)));
  assert.doesNotThrow(()=>JSON.stringify(result));
});

test('a better pairwise judgment can retain real edits despite absolute-score jitter',async()=>{
  const mock=model({initialScore:.2,candidateScore:.4,pairwise:'better'});
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  const row=result.branches.memory.rounds[1];
  assert.equal(row.accepted,true);assert.equal(row.candidateScore,2);assert.equal(row.retainedScore,2);
  assert.equal(row.scoreChange,1);assert.equal(row.pairwise,'better');assert.equal(row.outcome,'success');
  assert.notEqual(row.beforeText,row.text);
});

test('a lower absolute score cannot override a worse pairwise judgment',async()=>{
  const mock=model({candidateScore:0,pairwise:'worse'});
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  const row=result.branches.targeted.rounds[1];
  assert.equal(row.candidateScore,0);assert.equal(row.retainedScore,1);assert.equal(row.accepted,false);
});

test('numeric drift or a content-preservation failure cannot win through pairwise preference',async()=>{
  const mock=model({addNumber:true,candidateScore:0});
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  assert.equal(result.branches.memory.rounds[1].accepted,false);
  assert.equal(result.branches.memory.rounds[1].outcome,'failure_guard');
  assert.ok(result.branches.memory.rounds[1].guard.findings.some(x=>x.includes('Numeric tokens')));
  const failed=model({preservation:false,candidateScore:0});
  const other=await runProposal({topic,sources,callModel:failed.callModel});
  assert.equal(other.branches.targeted.rounds[1].accepted,false);
  assert.equal(other.branches.targeted.rounds[1].audit.preservation.passed,false);
});

test('identity candidates never claim success or refresh a retained score',async()=>{
  const mock=model({identity:true,candidateScore:0,pairwise:'better'});
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  const row=result.branches.memory.rounds[1];
  assert.equal(row.changed,false);assert.equal(row.outcome,'no_change');assert.equal(row.accepted,false);
  assert.equal(row.candidateScore,0);assert.equal(row.retainedScore,1);assert.equal(row.pairwiseReview.verdict,'better');
});

test('one invalid candidate does not block peers and invalidates its resumable raw response',async()=>{
  const mock=model({failStage:s=>s==='revise_memory_1'}),events=[];
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel,onProgress:e=>events.push(e)});
  assert.equal(result.branches.memory.rounds[1].outcome,'generation_failed');
  assert.equal(result.branches.memory.rounds[1].candidateScore,null);
  assert.equal(result.branches.targeted.rounds[1].accepted,true);
  assert.equal(result.status,'completed_with_errors');assert.equal(result.comparison.valid,false);
  assert.ok(events.some(e=>e.stage==='revise_memory_1'&&e.phase==='invalidated'));
});

test('one bad assessment isolates its route without discarding valid peer assessments',async()=>{
  const mock=model({badReview:true}),events=[];
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel,onProgress:e=>events.push(e)});
  // R1 opaque candidate order is Planner, Memory, Targeted.
  assert.equal(result.branches.planner.rounds[1].outcome,'review_failed');
  assert.equal(result.branches.targeted.rounds[1].accepted,true);
  assert.equal(result.branches.memory.rounds[1].accepted,true);
  assert.equal(result.comparison.valid,false);
  assert.ok(events.some(e=>e.stage==='review_round_1'&&e.phase==='invalidated'));
});

test('review payloads carry neutral IDs and patches, not methods, cards, plans, or old scores',async()=>{
  const mock=model();await runProposal({topic,sources,cards,callModel:mock.callModel});
  const review=mock.records.find(x=>x.stage==='review_round_1').data;
  const encoded=JSON.stringify(review);
  for(const prohibited of ['targeted','planner','memory','concrete_lead','currentDiagnosis','priorDecisions'])assert.equal(encoded.includes(prohibited),false);
  assert.equal(review.documents.length,1);
  assert.equal(review.candidates.length,3);
  assert.equal(review.sources.length,2);
});

test('memory receives complete reusable context; controls do not receive historical cards',async()=>{
  const mock=model();const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  const memory=mock.records.find(x=>x.stage==='revise_memory_1').data.conditionalCards[0];
  assert.equal(memory.examples[0].retainedElsewhere,cards[0].examples[0].payload.retained_elsewhere);
  assert.equal(memory.examples[0].retainedSection,'Limitations');
  assert.equal(memory.examples[0].trace,'development/trace/example.json');
  assert.equal(mock.records.find(x=>x.stage==='revise_planner_1').data.conditionalCards.length,0);
  assert.equal(result.branches.memory.rounds[1].memoryApplications[0].cardId,'concrete_lead');
});

test('paragraph-ID edits preserve all bytes outside authorized windows and reject invalid targets',()=>{
  const first=paragraphs(initial)[0],replacement='The same planned comparison preserves evidence relationships [S1].';
  const result=applyLocalEdits(initial,[{paragraphId:first.id,replacement}]);
  assert.equal(result,initial.slice(0,first.start)+replacement+initial.slice(first.end));
  assert.throws(()=>applyLocalEdits(initial,[{paragraphId:'P99',replacement}]),/Unknown paragraph/);
  assert.throws(()=>applyLocalEdits(initial,[{paragraphId:'P1',replacement:'# New heading'}]),/cannot insert/);
  assert.throws(()=>applyLocalEdits(initial,[{paragraphId:'P1',replacement},{paragraphId:'P1',replacement}]),/unique/);
  assert.equal(guardCandidate(initial,initial.replaceAll('[S1]','[S99]'),sources).passed,false);
  assert.ok(textMetrics(initial).words>0);
});

test('intentional stops are not model failures and preserve all round records',async()=>{
  const mock=model({stop:true});const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  assert.equal(mock.records.length,5);
  assert.equal(result.status,'completed');assert.equal(result.comparison.valid,true);
  assert.equal(result.branches.memory.rounds[3].route,'stop');
  assert.equal(result.branches.memory.rounds[3].carriedStop,true);
  assert.equal(result.branches.memory.rounds[3].candidateScore,null);
});

test('initial schema errors invalidate cached response and aborted runs send no new calls',async()=>{
  const events=[];
  await assert.rejects(runProposal({topic,sources,callModel:async()=>({text:initial}),onProgress:e=>events.push(e)}),/missing required/);
  assert.ok(events.some(e=>e.stage==='draft'&&e.phase==='invalidated'));
  const controller=new AbortController();controller.abort();let called=false;
  await assert.rejects(runProposal({topic,sources,signal:controller.signal,callModel:async()=>{called=true;}}),{name:'AbortError'});
  assert.equal(called,false);
});


test('an identity replacement cannot claim that a historical editing card was applied',async()=>{
  const mock=model({identity:true,claimIdentityMemory:true});
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  const row=result.branches.memory.rounds[1];
  assert.equal(row.outcome,'generation_failed');
  assert.equal(row.accepted,false);
  assert.equal(row.candidateScore,null);
  assert.deepEqual(row.memoryApplications,[]);
  assert.ok(row.reason.includes('actual text change'));
  assert.equal(result.branches.targeted.rounds[1].outcome,'no_change');
  assert.equal(result.comparison.valid,false);
});


test('structured negative content findings stay readable and cannot become accepted candidates',async()=>{
  const mock=model({objectGuard:'negative',candidateScore:0,pairwise:'better'});
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  const row=result.branches.memory.rounds[1];
  assert.equal(row.accepted,false);
  assert.equal(row.outcome,'failure_guard');
  assert.equal(row.audit.preservation.passed,false);
  assert.equal(typeof row.audit.preservation.issues[0],'string');
  assert.ok(row.reason.includes('P1'));
  assert.ok(row.reason.includes('A retained scientific qualification'));
  assert.ok(row.reason.includes('no longer retained'));
  assert.deepEqual(row.audit.preservation.rawIssues[0],{paragraphId:'P1',quote:'A retained scientific qualification',advice:'This qualification is no longer retained by the revised statement.'});
  assert.equal(result.status,'completed');
  for(const objectGuard of ['contradictory','malformed']) {
    const bad=model({objectGuard});
    const invalid=await runProposal({topic,sources,cards,callModel:bad.callModel});
    assert.equal(invalid.branches.targeted.rounds[1].outcome,'review_failed');
    assert.equal(invalid.branches.targeted.rounds[1].accepted,false);
    assert.equal(invalid.comparison.valid,false);
  }
});


test('a tied candidate cannot replace the retained draft even with a lower absolute score',async()=>{
  const mock=model({candidateScore:0,pairwise:'tie'});
  const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  for(const method of ['targeted','planner','memory']) {
    const row=result.branches[method].rounds[1];
    assert.equal(row.changed,true);
    assert.equal(row.candidateScore,0);
    assert.equal(row.retainedScore,1);
    assert.equal(row.pairwise,'tie');
    assert.equal(row.accepted,false);
    assert.equal(row.text,initial);
    assert.notEqual(row.candidateText,initial);
    assert.equal(row.outcome,'no_gain');
  }
  assert.equal(result.comparison.valid,true);
});

test('supplied proposals skip idea generation and preserve the same D0 across all routes',async()=>{
  const mock=model();
  const result=await runProposal({topic,sources,cards,suppliedDraft:initial,callModel:mock.callModel});
  assert.equal(result.draftOrigin,'user_supplied');
  assert.equal(result.initialText,initial);
  assert.equal(result.input.suppliedDraft,initial);
  assert.deepEqual(result.outline.ideas,[]);
  assert.equal(result.outline.selectedIdea,null);
  assert.equal(result.outline.outline.length,6);
  assert.equal(mock.records.length,13);
  assert.equal(mock.records[0].stage,'audit_initial');
  for(const method of ['targeted','planner','memory']) {
    assert.equal(result.branches[method].rounds[0].text,initial);
    assert.equal(mock.records.find(x=>x.stage==='revise_'+method+'_1').data.currentParagraphs[0].text,paragraphs(initial)[0].text);
  }
  const fresh=await runProposal({topic,sources,mode:'draft',callModel:model().callModel});
  assert.equal(fresh.draftOrigin,'model_generated');
});

test('supplied-draft structure, citations, size, and rule mode fail before paid calls',async()=>{
  for(const suppliedDraft of [initial.replace('## Abstract','## Summary'),initial.replaceAll('[S2]','[S99]'),'Too short.',initial+'x'.repeat(18000)]) {
    let called=false;
    await assert.rejects(runProposal({topic,sources,suppliedDraft,callModel:async()=>{called=true;}}));
    assert.equal(called,false);
  }
  await assert.rejects(runProposal({topic,sources,ruleMode:'force_win',callModel:async()=>{}}),/Unknown editorial rule mode/);
});

test('explicit edits expose exact rule evidence without giving rule labels to the reviewer',async()=>{
  const mock=model();const result=await runProposal({topic,sources,cards,callModel:mock.callModel});
  const row=result.branches.targeted.rounds[1],edit=row.edits[0];
  assert.equal(result.ruleMode,'explicit');
  assert.equal(row.ruleApplications[0].paragraphId,edit.paragraphId);
  assert.equal(edit.rules[0].ruleId,'specific_subject_action');
  assert.ok(edit.before.includes(edit.rules[0].beforeQuote));
  assert.ok(edit.after.includes(edit.rules[0].afterQuote));
  assert.notEqual(edit.rules[0].beforeQuote,edit.rules[0].afterQuote);
  const review=mock.records.find(x=>x.stage==='review_round_1');
  for(const prohibited of ['specific_subject_action','ruleApplications','editorial specifications'])assert.equal(JSON.stringify(review).includes(prohibited),false);
});

test('missing or fabricated rule anchors reject the candidate rather than inventing evidence',async()=>{
  for(const options of [{omitRules:true},{badRule:true}]) {
    const result=await runProposal({topic,sources,cards,callModel:model(options).callModel});
    for(const method of ['targeted','planner','memory']) {
      assert.equal(result.branches[method].rounds[1].outcome,'generation_failed');
      assert.equal(result.branches[method].rounds[1].accepted,false);
      assert.deepEqual(result.branches[method].rounds[1].ruleApplications,[]);
    }
    assert.equal(result.comparison.valid,false);
  }
});

test('the standard editing control changes neither audit nor blinded review instructions',async()=>{
  const explicit=model(),standard=model({ruleMode:'standard'});
  const one=await runProposal({topic,sources,cards,suppliedDraft:initial,callModel:explicit.callModel});
  const two=await runProposal({topic,sources,cards,suppliedDraft:initial,ruleMode:'standard',callModel:standard.callModel});
  for(const stage of ['audit_initial','review_round_1']) {
    assert.equal(explicit.records.find(x=>x.stage===stage).instruction,standard.records.find(x=>x.stage===stage).instruction);
  }
  assert.ok(explicit.records.find(x=>x.stage==='revise_targeted_1').instruction.includes('calibrated_claims'));
  assert.equal(standard.records.find(x=>x.stage==='revise_targeted_1').instruction.includes('calibrated_claims'),false);
  assert.equal(two.ruleMode,'standard');
  assert.equal(one.initialText,two.initialText);
  assert.equal(two.branches.targeted.rounds[1].accepted,true);
  assert.deepEqual(two.branches.targeted.rounds[1].edits[0].rules,[]);
});

test('optional diagnostic rule labels never invalidate otherwise useful anchored feedback',async()=>{
  const mock=model();
  const result=await runProposal({topic,sources,cards,mode:'draft',callModel:async(messages,config)=>{
    const reply=await mock.callModel(messages,config);
    if(config.stage==='audit_initial') {
      reply.issues[0].ruleId='specific_subject_action';
      reply.issues[1].ruleId='unrecognised_optional_label';
    }
    return reply;
  }});
  assert.equal(result.initialAudit.issues[0].ruleId,'specific_subject_action');
  assert.equal(result.initialAudit.issues[1].ruleId,undefined);
  assert.equal(result.initialAudit.issues[2].ruleId,undefined);
});

test('rule evidence cannot claim unchanged text, absent phrases, or unknown operations',()=>{
  const original=paragraphs(initial)[0];
  const replacement=original.text.replace('The planned study','The proposed evaluation');
  const edit={paragraphId:original.id,replacement};
  const valid={ruleId:'specific_subject_action',paragraphId:original.id,beforeQuote:'The planned study',afterQuote:'The proposed evaluation',reason:'The planned actor is expressed more directly without adding a finding.'};
  assert.equal(validateRuleApplications([valid],initial,[edit]).length,1);
  for(const altered of [{...valid,ruleId:'guaranteed_human'},{...valid,beforeQuote:'A missing phrase'},{...valid,afterQuote:'Another missing phrase'},
    {...valid,beforeQuote:'supplied evidence',afterQuote:'supplied evidence'}]) {
    assert.throws(()=>validateRuleApplications([altered],initial,[edit]));
  }
  assert.throws(()=>validateRuleApplications([valid,valid],initial,[edit]),/Repeated editorial rule/);
  assert.throws(()=>validateRuleApplications([],initial,[edit]),/Every changed paragraph/);
  assert.throws(()=>validateRuleApplications([valid],initial,[{...edit,replacement:original.text}]),/actual changed paragraph/);
});
