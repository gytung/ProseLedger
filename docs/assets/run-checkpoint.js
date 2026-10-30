/** Portable paid-work checkpoints. Imported records are data, not authenticated evidence. */
import { providerEndpoint } from './api-client.js?v=20261030e';

export const CHECKPOINT_CONTRACT = 'proseledger-browser-3-20261030e';
const LEGACY_CONTRACT = 'proseledger-browser-2-20261030d';
export const CHECKPOINT_MAX_BYTES = 8 * 1024 * 1024;
const SCHEMA = 'proseledger-checkpoint-1';
const METHODS = new Set(['targeted', 'planner', 'memory']);
const STAGE = /^(?:draft|audit_initial|revise_(?:targeted|planner|memory)_[123]|review_round_[123])$/;
const SECRET = /^(?:key|api[_-]?key|authorization|auth|token|access[_-]?token|refresh[_-]?token|bearer|password|secret|credentials|cookie|set-cookie)$/i;
const encoder = new TextEncoder();
const fail = message => { throw new Error('Invalid checkpoint: ' + message); };
function need(condition, message) { if (!condition) fail(message); }
function object(value, label) { need(value && typeof value === 'object' && !Array.isArray(value), label + ' must be an object.'); return value; }
function list(value, label, limit) { need(Array.isArray(value) && value.length <= limit, label + ' is not a supported list.'); return value; }
function string(value, label, limit, minimum = 0) { need(typeof value === 'string' && value.length >= minimum && value.length <= limit, label + ' has an unsupported value or length.'); return value; }
function optionalString(value, label, limit) { if (value !== null && value !== undefined) string(value, label, limit); }
function number(value, label, maximum = Number.MAX_SAFE_INTEGER) { need(typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= maximum, label + ' must be a bounded number.'); }
function boundedJSON(value, label, max = CHECKPOINT_MAX_BYTES) {
  let encoded; try { encoded = JSON.stringify(value); } catch { fail(label + ' cannot be serialized.'); }
  need(typeof encoded === 'string' && encoder.encode(encoded).length <= max, label + ' exceeds its size limit.');
  return encoded;
}
function clean(value, secrets = [], depth = 0) {
  need(depth <= 40, 'data nesting is too deep.');
  if (typeof value === 'string') { for (const secret of secrets) value = value.split(secret).join('[credential removed]'); return value; }
  if (value === null || typeof value === 'boolean') return value;
  if (typeof value === 'number') { need(Number.isFinite(value), 'non-finite numeric value.'); return value; }
  if (Array.isArray(value)) return value.map(item => clean(item, secrets, depth + 1));
  if (value && typeof value === 'object') {
    const result = {};
    for (const [key, item] of Object.entries(value)) {
      need(!['__proto__', 'prototype', 'constructor'].includes(key), 'unsupported object property.');
      if (SECRET.test(key) || item === undefined) continue;
      result[key] = clean(item, secrets, depth + 1);
    }
    return result;
  }
  fail('unsupported data value.');
}
function knownSecrets(session) {
  const secrets = [];
  for (const target of [session, session?.snapshot]) if (target && typeof target === 'object') {
    for (const [key, value] of Object.entries(target)) if (SECRET.test(key) && typeof value === 'string' && value.length >= 8) secrets.push(value);
  }
  return secrets;
}
function validateCardFields(card) {
  // These optional fields are consumed by both the card viewer and compactCards.
  // Null means absent, as it does in the engine; array entries must still be valid.
  if (card.conditions !== undefined && card.conditions !== null) for (const condition of list(card.conditions, 'Card conditions', 50)) {
    if (typeof condition === 'string') string(condition, 'Card condition', 6500, 1);
    else { object(condition, 'Card condition'); string(condition.kind, 'Condition kind', 150, 1); string(condition.text, 'Condition text', 6500, 1); optionalString(condition.id, 'Condition ID', 150); }
  }
  for (const key of ['preserve', 'counterexamples']) if (card[key] !== undefined && card[key] !== null) stringArray(card[key], 'Card ' + key, 50, 6500);
  if (card.examples !== undefined && card.examples !== null) for (const example of list(card.examples, 'Card examples', 50)) {
    object(example, 'Card example');
    if (example.payload !== undefined && example.payload !== null) object(example.payload, 'Example payload');
    if (example.provenance !== undefined && example.provenance !== null) { object(example.provenance, 'Example provenance'); optionalString(example.provenance.trace, 'Example provenance trace', 6500); }
    for (const key of ['episode_id', 'episodeId', 'trace']) optionalString(example[key], 'Example ' + key, 6500);
    const payload = example.payload || example;
    for (const key of ['label', 'before', 'after', 'retained_elsewhere', 'retainedElsewhere', 'retained_section', 'retainedSection']) optionalString(payload[key], 'Example ' + key, 6500);
  }
}
function validateSnapshot(snapshot) {
  object(snapshot, 'Input snapshot');
  string(snapshot.base, 'API base URL', 2000, 1);
  string(snapshot.endpoint, 'API endpoint', 2000, 1);
  let endpoint; try { endpoint = providerEndpoint(snapshot.base); } catch { fail('the provider must use a public HTTPS endpoint without credentials.'); }
  need(endpoint === snapshot.endpoint, 'the API base URL and endpoint do not match.');
  string(snapshot.model, 'Model ID', 160, 1); need(snapshot.model === snapshot.model.trim() && !/[\r\n]/.test(snapshot.model), 'invalid model ID.');
  string(snapshot.topic, 'Topic', 1600, 10); need(['draft', 'compare'].includes(snapshot.mode), 'unknown generation mode.');
  list(snapshot.sources, 'Source notes', 10); need(snapshot.sources.length >= 2, 'at least two source notes are required.');
  const ids = new Set(); let evidenceSize = 0;
  for (const source of snapshot.sources) {
    object(source, 'Source note'); string(source.id, 'Source ID', 30, 2); need(/^S\d+$/.test(source.id) && !ids.has(source.id), 'source IDs must be unique S-number identifiers.'); ids.add(source.id);
    string(source.title, 'Source title', 500, 1); string(source.excerpt, 'Source excerpt', 4000, 80); evidenceSize += source.excerpt.length;
    optionalString(source.url, 'Source URL', 2000);
    if (source.authors !== undefined) for (const author of list(source.authors, 'Source authors', 40)) string(author, 'Author', 150);
  }
  need(evidenceSize <= 24000, 'combined source evidence is too long.');
  list(snapshot.cards, 'Editing cards', 8); const cardIds = new Set();
  for (const card of snapshot.cards) {
    object(card, 'Editing card'); string(card.id, 'Card ID', 150, 1); string(card.operation, 'Card operation', 6500, 1);
    need(!cardIds.has(card.id), 'editing card IDs must be unique.'); cardIds.add(card.id); validateCardFields(card); boundedJSON(card, 'Editing card', 6500);
  }
  boundedJSON(snapshot.cards, 'Editing-card catalogue', 24000);
  optionalString(snapshot.suppliedDraft, 'Supplied proposal', 18000);
  if (snapshot.ruleMode !== undefined) need(['explicit', 'standard'].includes(snapshot.ruleMode), 'unknown editorial rule mode.');
  optionalString(snapshot.sourceCatalogSHA256, 'Source catalogue fingerprint', 200);
  return snapshot;
}
function validateResponse(record, snapshot, cached = false) {
  object(record, 'Model response record'); need(STAGE.test(record.stage), 'unknown model stage.');
  need(record.model === snapshot.model, 'response model does not match the input snapshot.');
  number(record.maxTokens, 'Response output limit', 16000); need(Number.isInteger(record.maxTokens) && record.maxTokens > 0, 'invalid output limit.');
  need(typeof record.response === 'string' || (record.response && typeof record.response === 'object'), 'missing model response.');
  boundedJSON(record.response, 'Model response', 150000);
  optionalString(record.receivedAt, 'Response timestamp', 80);
  if (record.invalidated !== undefined) need(typeof record.invalidated === 'boolean', 'invalid response status.');
  if (cached) need(record.invalidated !== true, 'an invalidated response cannot be reused.');
  return record;
}
function validateCache(entries, snapshot) {
  list(entries, 'Cached stages', 14); const keys = new Set(), stages = new Set();
  for (const entry of entries) {
    object(entry, 'Cache entry'); string(entry.request, 'Cached request', 512000, 1);
    let request; try { request = JSON.parse(entry.request); } catch { fail('a cached request is malformed JSON.'); }
    need(Array.isArray(request) && request.length === 4, 'a cached request has an invalid structure.');
    need(request[0] === snapshot.endpoint && request[1] === snapshot.model, 'a cached request uses another endpoint or model.');
    list(request[2], 'Cached messages', 10); need(request[2].length >= 1, 'a cached request has no messages.');
    for (const message of request[2]) { object(message, 'Cached message'); need(['system', 'user', 'assistant'].includes(message.role), 'unsupported cached message role.'); string(message.content, 'Cached message content', 300000, 1); }
    validateResponse(entry.record, snapshot, true); need(request[3] === entry.record.maxTokens, 'cached token limits do not match.');
    need(!keys.has(entry.request) && !stages.has(entry.record.stage), 'duplicate cached request or stage.'); keys.add(entry.request); stages.add(entry.record.stage);
  }
  return entries;
}
function stringArray(value, label, maximum = 20, size = 4000) { for (const item of list(value, label, maximum)) string(item, label + ' entry', size); }
function validateRound(row) {
  object(row, 'Round'); need(Number.isInteger(row.round) && row.round >= 0 && row.round <= 3, 'invalid round number.');
  for (const key of ['text', 'candidateText', 'beforeText']) optionalString(row[key], 'Round ' + key, 18000);
  for (const key of ['reason', 'error']) optionalString(row[key], 'Round ' + key, 12000);
  for (const key of ['route', 'outcome', 'pairwise', 'failureStage']) optionalString(row[key], 'Round ' + key, 150);
  for (const key of ['candidateScore', 'retainedScore']) if (row[key] !== null && row[key] !== undefined) number(row[key], key, 20);
  for (const key of ['accepted', 'changed', 'carriedStop']) if (row[key] !== undefined) need(typeof row[key] === 'boolean', 'invalid round flag.');
  if (row.cardIds !== undefined) stringArray(row.cardIds, 'Card IDs', 8, 150);
  if (row.edits !== undefined) for (const edit of list(row.edits, 'Paragraph edits', 3)) { object(edit, 'Paragraph edit'); for (const key of ['paragraphId', 'before', 'after', 'reason']) optionalString(edit[key], 'Edit ' + key, key === 'paragraphId' ? 30 : 18000); validateRules(edit.rules);  }
  validateRules(row.ruleApplications);
  if (row.memoryApplications !== undefined) for (const application of list(row.memoryApplications, 'Memory applications', 8)) {
    object(application, 'Memory application'); string(application.cardId, 'Applied card ID', 150, 1); stringArray(application.paragraphIds, 'Applied paragraph IDs', 3, 30);
    for (const key of ['conditionEvidence', 'reason']) optionalString(application[key], 'Application ' + key, 2000);
  }
  if (row.guard !== undefined) { object(row.guard, 'Content check'); if (row.guard.passed !== undefined) need(typeof row.guard.passed === 'boolean', 'invalid content check verdict.'); if (row.guard.findings !== undefined) stringArray(row.guard.findings, 'Content findings'); }
  validateAudit(row.audit);
  if (row.plan !== undefined && row.plan !== null) { object(row.plan, 'Editing plan'); if (row.plan.actions !== undefined) for (const action of list(row.plan.actions, 'Planned actions', 3)) { object(action, 'Planned action'); optionalString(action.goal, 'Plan goal', 1000); if (action.keep !== undefined) stringArray(action.keep, 'Protected phrases', 3, 500); } }
  if (row.pairwiseReview !== undefined) { object(row.pairwiseReview, 'Pairwise review'); string(row.pairwiseReview.verdict, 'Pairwise verdict', 30); optionalString(row.pairwiseReview.reason, 'Pairwise reason', 3000); if (row.pairwiseReview.evidence !== undefined) stringArray(row.pairwiseReview.evidence, 'Pairwise evidence', 3, 1000); }
}
function validateRules(rules) {
  if (rules === undefined) return;
  for (const rule of list(rules, 'Rule applications', 18)) {
    object(rule, 'Rule application');
    for (const key of ['ruleId', 'paragraphId', 'beforeQuote', 'afterQuote', 'reason']) optionalString(rule[key], 'Rule ' + key, key.endsWith('Id') ? 100 : 5000);
  }
}
function validateAudit(audit) {
  if (audit === undefined || audit === null) return;
  object(audit, 'Assessment');
  if (audit.issues !== undefined) for (const issue of list(audit.issues, 'Assessment issues', 6)) { object(issue, 'Assessment issue'); for (const key of ['id', 'dimension', 'paragraphId', 'quote', 'advice', 'ruleId']) optionalString(issue[key], 'Assessment ' + key, 2000); }
  if (audit.dimensions !== undefined) { object(audit.dimensions, 'Assessment dimensions'); for (const dimension of Object.values(audit.dimensions)) { object(dimension, 'Assessment dimension'); number(dimension.score, 'Dimension score', 4); optionalString(dimension.reason, 'Dimension reason', 3000); optionalString(dimension.quote, 'Dimension quotation', 2000); } }
  if (audit.preservation !== undefined) { object(audit.preservation, 'Preservation assessment'); need(typeof audit.preservation.passed === 'boolean', 'invalid preservation verdict.'); if (audit.preservation.issues !== undefined) stringArray(audit.preservation.issues, 'Preservation issues'); }
}
function validateResult(result) {
  if (result === null || result === undefined) return null;
  object(result, 'Run result'); need(['proseledger-browser-2', 'proseledger-browser-3'].includes(result.schema), 'unsupported result schema.');
  need(['incomplete', 'cancelled', 'completed', 'completed_with_errors'].includes(result.status), 'unsupported run status.');
  optionalString(result.initialText, 'Initial proposal', 18000); if (result.initialScore !== null && result.initialScore !== undefined) number(result.initialScore, 'Initial score', 20);
  validateAudit(result.initialAudit);
  object(result.branches, 'Revision branches');
  for (const [method, branch] of Object.entries(result.branches)) {
    need(METHODS.has(method), 'unknown revision branch.'); object(branch, 'Revision branch'); string(branch.text, 'Retained proposal', 18000); number(branch.finalScore, 'Final score', 20);
    list(branch.rounds, 'Revision rounds', 4); const rounds = new Set(); for (const row of branch.rounds) { validateRound(row); need(!rounds.has(row.round), 'duplicate revision round.'); rounds.add(row.round); }
  }
  return result;
}
function validate(document) {
  object(document, 'Checkpoint'); need(document.schema === SCHEMA, 'unsupported file format.'); need([CHECKPOINT_CONTRACT, LEGACY_CONTRACT].includes(document.engineContract), 'this file belongs to another engine contract.');
  const session = object(document.session, 'Session'); validateSnapshot(session.snapshot); validateCache(session.cache, session.snapshot);
  for (const record of list(session.responses, 'Response history', 500)) validateResponse(record, session.snapshot);
  for (const usage of list(session.usage, 'Usage history', 500)) { object(usage, 'Usage record'); for (const key of ['totalTokens', 'promptTokens', 'completionTokens']) if (usage[key] !== undefined && usage[key] !== null) number(usage[key], 'Token count'); }
  for (const event of list(session.events, 'Event history', 5000)) object(event, 'Event');
  list(session.attempts, 'Attempt history', 100);
  for (const attempt of session.attempts) { object(attempt, 'Attempt'); if (attempt.result !== undefined) validateResult(attempt.result); }
  number(session.attemptCount, 'Attempt count', 10000); need(Number.isInteger(session.attemptCount), 'invalid attempt count.');
  string(session.createdAt, 'Session timestamp', 80, 1); optionalString(document.exportedAt, 'Export timestamp', 80); validateResult(document.result);
  return document;
}

/** Returns plain JSON data. API credentials are never part of this file format. */
export function createCheckpoint(session, result) {
  object(session, 'Session'); need(session.cache instanceof Map, 'the live cache must be a Map.');
  const snapshot = {}; for (const key of ['base', 'endpoint', 'model', 'topic', 'sources', 'mode', 'cards', 'sourceCatalogSHA256', 'suppliedDraft', 'ruleMode']) if (session.snapshot?.[key] !== undefined) snapshot[key] = session.snapshot[key];
  const source = {schema: SCHEMA, engineContract: session.readOnly ? LEGACY_CONTRACT : CHECKPOINT_CONTRACT, exportedAt: new Date().toISOString(), session: {
    snapshot, cache: [...session.cache].map(([request, record]) => ({request, record})),
    responses: session.responses || [], usage: session.usage || [], events: session.events || [],
    attemptCount: session.attemptCount || 0, attempts: session.attempts || [], createdAt: session.createdAt,
  }, result: result ?? null};
  const document = clean(source, knownSecrets(session)); boundedJSON(document, 'Checkpoint'); return validate(document);
}

/** Validates offline data only; importing never performs requests or restores a key. */
export function restoreCheckpoint(input) {
  let document = input;
  if (typeof input === 'string') { need(encoder.encode(input).length <= CHECKPOINT_MAX_BYTES, 'file exceeds 8 MB.'); try { document = JSON.parse(input); } catch { fail('file is not valid JSON.'); } }
  else boundedJSON(input, 'Checkpoint');
  document = validate(clean(document));
  const legacy = document.engineContract !== CHECKPOINT_CONTRACT || document.result?.schema === 'proseledger-browser-2'
    || document.session.attempts.some(attempt => attempt.result?.schema === 'proseledger-browser-2');
  const session = {...document.session, readOnly: legacy, cache: new Map(document.session.cache.map(entry => [entry.request, entry.record]))};
  if (legacy) session.cache.clear();
  return {session, result: document.result ?? null, readOnly: legacy};
}
