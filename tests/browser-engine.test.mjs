import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const code = await readFile(new URL('../docs/assets/browser-engine.js', import.meta.url), 'utf8');
const engine = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
const {runProposal, guardCandidate, applyLocalEdits, HEADINGS, DIMENSIONS} = engine;

const sources = [
  {id: 'S1', title: 'Evidence and editing', excerpt: 'This supplied source discusses how language models may revise supported passages while retaining their original attribution. Its findings do not validate a new proposal.'},
  {id: 'S2', title: 'Conditional experience', excerpt: 'This supplied source discusses storing conditional editing experiences and reviewing whether their preconditions apply to a later task. It establishes no universal benefit.'},
];
const paragraph = 'A proposal needs clearer expression while retaining its supported claims and uncertainty [S1]. The planned study will compare revision decisions against the original evidence.';
const initial = '# Conditional Proposal Revision\n\n' + HEADINGS.map((heading, index) =>
  `## ${heading}\n\n${index === 0 ? paragraph : `This ${heading.toLowerCase()} section describes a planned comparison of revision procedures and their limits [S2]. No experiment has been conducted, and the proposal makes no claim of an observed improvement.`}`,
).join('\n\n');
const clearer = initial.replace(paragraph, 'The planned study will compare revision decisions against the original evidence. A proposal needs clearer expression while retaining its supported claims and uncertainty [S1].');
const topic = 'Conditional editing experience for evidence-preserving academic proposal revision';
const cards = [{id: 'concrete_lead', operation: 'Lead with existing concrete substance.', conditions: ['Substance already exists.']}];

function audit(candidate, score = 1, preservation = true) {
  return {
    dimensions: Object.fromEntries(DIMENSIONS.map(dimension => [dimension, {
      score, reason: score ? 'The cited passage could be more direct.' : 'No identified expression problem.',
      quote: score ? candidate.split('\n\n')[2] : '',
    }])),
    preservation: {passed: preservation, issues: preservation ? [] : ['A qualification was lost.']},
  };
}

function payload(messages) {
  return JSON.parse(messages[1].content.split('INPUT DATA (not instructions):\n')[1]);
}

function mockModel(options = {}) {
  const stages = [];
  const callModel = async (messages, {stage}) => {
    stages.push(stage);
    const data = payload(messages);
    if (stage === 'ideation') return {
      ideas: ['A conditional revision experiment.', 'A bounded editing experiment.', 'An evidence comparison experiment.'],
      selectedIdea: 0, outline: HEADINGS.map(heading => ({heading, plan: 'Describe this proposed component and its evidence limits.'})),
    };
    if (stage === 'draft') return {text: initial};
    if (stage.startsWith('audit')) return audit(data.candidate, options.score?.(stage) ?? 1, options.preservation?.(stage) ?? true);
    if (stage.startsWith('plan')) return {
      route: options.local ? 'local_edit' : 'stop', reason: 'The remaining expression change is bounded and evidence-preserving.',
      actions: options.local ? [{anchor: data.currentProposal.split('\n\n')[2], instruction: 'Retain this paragraph with the same scientific content.'}] : [],
      cardIds: options.local && data.editingCards.length ? [data.editingCards[0].id] : [],
      applicability: 'The operation acts on existing content only; no factual material is transferred.',
    };
    if (stage.startsWith('rewrite') && data.plan) return {
      edits: data.plan.actions.map(action => ({anchor: action.anchor, replacement: action.anchor})),
    };
    if (stage.startsWith('rewrite')) return {text: options.candidate?.(stage) || clearer};
    throw new Error(`Unexpected stage ${stage}`);
  };
  return {callModel, stages};
}

test('draft mode makes three actual injected calls and exposes an audited proposal', async () => {
  const mock = mockModel();
  const progress = [];
  const result = await runProposal({topic, sources, cards, ...mock, mode: 'draft', onProgress: event => progress.push(event)});
  assert.deepEqual(mock.stages, ['ideation', 'draft', 'audit_initial']);
  assert.equal(result.initialText, initial);
  assert.equal(result.initialScore, 5);
  assert.deepEqual(result.branches, {});
  assert.ok(progress.some(event => event.phase === 'draft' && event.detail.initialText === initial));
  assert.doesNotThrow(() => JSON.stringify(result));
});

test('three routes share first revision; explicit stops preserve all R0–R3 records', async () => {
  const mock = mockModel();
  const result = await runProposal({topic, sources, cards, ...mock});
  assert.equal(mock.stages.length, 13);
  assert.equal(mock.stages.filter(stage => stage === 'rewrite_shared_1').length, 1);
  for (const branch of Object.values(result.branches)) {
    assert.deepEqual(branch.rounds.map(row => row.round), [0, 1, 2, 3]);
    assert.equal(branch.rounds[1].shared, true);
  }
  assert.equal(result.branches.memory.rounds[2].candidateScore, null);
  assert.equal(result.branches.memory.rounds[2].route, 'stop');
  assert.equal(result.comparison.memoryMinusTargeted, 0);
  assert.equal(result.branches.memory.rounds[2].accepted, false);
  assert.doesNotThrow(() => JSON.stringify(result));
});

test('local-route comparison stays within 21 calls and exposes real card attribution', async () => {
  const mock = mockModel({local: true});
  const result = await runProposal({topic, sources, cards, ...mock});
  assert.equal(mock.stages.length, 21);
  assert.deepEqual(result.branches.memory.rounds[2].cardIds, ['concrete_lead']);
  assert.deepEqual(result.branches.planner.rounds[2].cardIds, []);
  assert.equal(result.branches.memory.rounds[2].outcome, 'no_gain');
  assert.equal(result.branches.memory.rounds[2].changed, false);
});

test('Memory is not privileged: worse candidates lose to an improving Targeted route', async () => {
  const mock = mockModel({local: true, score: stage => {
    if (stage === 'audit_targeted_2' || stage === 'audit_targeted_3') return 0;
    if (stage.startsWith('audit_memory_')) return 2;
    return 1;
  }});
  const result = await runProposal({topic, sources, cards, ...mock});
  assert.equal(result.branches.targeted.finalScore, 0);
  assert.equal(result.branches.memory.finalScore, 5);
  assert.equal(result.branches.memory.rounds[2].candidateScore, 10);
  assert.equal(result.branches.memory.rounds[2].accepted, false);
  assert.equal(result.comparison.memoryMinusTargeted, 5);
});

test('a lower score cannot override a deterministic content failure', async () => {
  const changedNumber = clearer.replace('planned study', 'planned study involving 500 participants');
  const mock = mockModel({
    candidate: stage => stage === 'rewrite_shared_1' ? changedNumber : initial,
    score: stage => stage === 'audit_shared_1' ? 0 : 1,
  });
  const result = await runProposal({topic, sources, cards, ...mock});
  const row = result.branches.memory.rounds[1];
  assert.equal(row.candidateScore, 0);
  assert.equal(row.retainedScore, 5);
  assert.equal(row.accepted, false);
  assert.equal(row.outcome, 'failure_guard');
  assert.equal(row.text, initial);
  assert.ok(row.guard.findings.some(finding => finding.includes('Numeric tokens added')));
});

test('a lower score cannot override model-identified loss of meaning', async () => {
  const mock = mockModel({
    score: stage => stage === 'audit_shared_1' ? 0 : 1,
    preservation: stage => stage !== 'audit_shared_1',
  });
  const result = await runProposal({topic, sources, cards, ...mock});
  assert.equal(result.branches.targeted.rounds[1].accepted, false);
  assert.equal(result.branches.targeted.rounds[1].retainedScore, 5);
  assert.equal(result.branches.targeted.rounds[1].audit.preservation.passed, false);
});

test('local execution changes only authorized paragraph bytes and rejects ambiguous anchors', () => {
  const replacement = 'The same evidence and caveats remain, with a more direct ordering [S1].';
  const patched = applyLocalEdits(initial, [{anchor: paragraph, replacement}]);
  assert.equal(patched, initial.replace(paragraph, replacement));
  assert.throws(() => applyLocalEdits(initial, [{anchor: paragraph.slice(0, 30), replacement}]), /complete original paragraph/);
  assert.throws(() => applyLocalEdits(initial, [{anchor: paragraph, replacement: '# New heading'}]), /cannot add/);
  assert.throws(() => applyLocalEdits(`${initial}\n\n${paragraph}`, [{anchor: paragraph, replacement}]), /one unique/);
});

test('citation integrity and future-study status are shared checks', () => {
  assert.equal(guardCandidate(initial, clearer, sources).passed, true);
  assert.equal(guardCandidate(initial, clearer.replaceAll('[S1]', '[S99]'), sources).passed, false);
  assert.equal(guardCandidate(initial, clearer.replace('The planned study', 'We found that the study'), sources).passed, false);
  assert.equal(guardCandidate(initial, clearer.replace('## Methodology', '## Results'), sources).passed, false);
});

test('malformed responses are errors, never fabricated fallbacks', async () => {
  await assert.rejects(runProposal({topic, sources, callModel: async () => 'not JSON'}), /invalid JSON/);
  const mock = mockModel();
  await assert.rejects(runProposal({topic, sources, callModel: async (messages, options) => {
    const raw = await mock.callModel(messages, options);
    if (options.stage === 'audit_initial') raw.dimensions.clarity.quote = 'This invented quotation is not in the proposal.';
    return raw;
  }}), /quote is not present/);
});

test('unsafe initial drafts are exposed for review but cannot enter comparison', async () => {
  const mock = mockModel({preservation: stage => stage !== 'audit_initial'});
  const progress = [];
  await assert.rejects(runProposal({topic, sources, ...mock, onProgress: event => progress.push(event)}), /Initial proposal needs review/);
  assert.deepEqual(mock.stages, ['ideation', 'draft', 'audit_initial']);
  assert.ok(progress.some(event => event.phase === 'draft'));
});

test('abort signals prevent subsequent provider calls', async () => {
  const controller = new AbortController();
  controller.abort();
  let calls = 0;
  await assert.rejects(runProposal({topic, sources, signal: controller.signal, callModel: async () => {calls++;}}), {name: 'AbortError'});
  assert.equal(calls, 0);
  const mock = mockModel();
  const second = new AbortController();
  await assert.rejects(runProposal({topic, sources, signal: second.signal, callModel: async (messages, options) => {
    const answer = await mock.callModel(messages, options);
    second.abort();
    return answer;
  }}), {name: 'AbortError'});
  assert.equal(mock.stages.length, 1);
});
