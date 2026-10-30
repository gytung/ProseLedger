import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const code=await readFile(new URL('../docs/assets/naturalness-rules.js',import.meta.url),'utf8');
const {NATURALNESS_RULES,RULE_IDS,naturalnessInstructions}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));

test('six distinct editorial operations each include applicability limits and a counterexample',()=>{
  assert.deepEqual(RULE_IDS,['specific_subject_action','concrete_wording','remove_redundancy','information_flow','sentence_focus','calibrated_claims']);
  for(const rule of NATURALNESS_RULES) {
    for(const field of ['label','goal','when','notWhen','before','after','avoid','caution'])assert.ok(typeof rule[field]==='string'&&rule[field].length>15,rule.id+': '+field);
    assert.notEqual(rule.before,rule.after);
    assert.notEqual(rule.after,rule.avoid);
    assert.ok(Object.isFrozen(rule));
  }
  assert.ok(Object.isFrozen(NATURALNESS_RULES));
});

test('editorial guidance distinguishes meaningful rewriting from detector gaming or blanket style bans',()=>{
  const instruction=naturalnessInstructions();
  assert.ok(instruction.includes('not empirically proven gains'));
  assert.ok(instruction.includes('Do not ban hyphens, passive voice, technical terms'));
  assert.ok(instruction.includes('supply no facts for the proposal'));
  assert.ok(instruction.includes('NOT-WHEN'));
});
