/** Optional detector observation. Never used by generation, retention or memory admission. */
export const GPTZERO_ENDPOINT = 'https://api.gptzero.me/v2/predict/text';

export async function textFingerprint(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(x => x.toString(16).padStart(2, '0')).join('');
}

export function parseDetectorResponse(raw) {
  const document = raw?.documents?.[0];
  if (!document || !document.class_probabilities) throw new Error('GPTZero returned no document classification. No result was inferred.');
  const probabilities = {};
  for (const label of ['human', 'mixed', 'ai']) {
    const p = document.class_probabilities[label];
    if (typeof p !== 'number' || !Number.isFinite(p) || p < 0 || p > 1) throw new Error('GPTZero returned an invalid class probability.');
    probabilities[label] = p;
  }
  const sum = Object.values(probabilities).reduce((a,b) => a+b, 0);
  if (Math.abs(sum - 1) > 0.02) throw new Error('GPTZero probabilities do not form a supported distribution.');
  const predicted = String(document.predicted_class || document.document_classification || '').toLowerCase().replace('_only', '');
  if (!['human', 'mixed', 'ai'].includes(predicted)) throw new Error('GPTZero returned an unknown class.');
  return {
    predictedClass: predicted, probabilities,
    confidence: typeof document.confidence_category === 'string' ? document.confidence_category.slice(0,100) : 'not reported',
    detectorVersion: typeof raw.version === 'string' ? raw.version.slice(0,200) : 'not reported',
    note: 'Authorship-pattern estimate, not a naturalness or factual-accuracy score.',
  };
}

export async function checkWithGPTZero({text, key, signal, fetchImpl = globalThis.fetch, timeoutMs = 60000}) {
  if (typeof text !== 'string' || text.length < 250 || text.length > 18000) throw new Error('Select a proposal of 250–18,000 characters.');
  if (typeof key !== 'string' || !key.trim() || /[\r\n]/.test(key)) throw new Error('Enter a valid GPTZero API key. This is separate from your model API key.');
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal?.aborted) abort();
  signal?.addEventListener('abort', abort, {once:true});
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const response = await fetchImpl(GPTZERO_ENDPOINT, {
      method:'POST', mode:'cors', credentials:'omit', redirect:'error',
      headers:{'Content-Type':'application/json', 'x-api-key':key.trim()},
      body:JSON.stringify({document:text}), signal:controller.signal,
    });
    if (!response.ok) {
      const messages = {401:'GPTZero did not accept this key.',403:'This GPTZero account does not have access.',429:'GPTZero rate or usage limit reached. Try later or check your allowance.',400:'GPTZero could not scan this text with the current account limits.'};
      throw new Error(messages[response.status] || `GPTZero request failed (HTTP ${response.status}). Your writing is unaffected.`);
    }
    const raw = await response.json();
    const observation = parseDetectorResponse(raw);
    return {...observation, textSHA256:await textFingerprint(text), checkedAt:new Date().toISOString(), source:'GPTZero API'};
  } catch (error) {
    if (timedOut) throw new Error('GPTZero timed out after 60 seconds. No detector result was recorded.');
    if (signal?.aborted) throw new DOMException('GPTZero check cancelled.', 'AbortError');
    if (error instanceof TypeError) throw new Error('GPTZero could not be reached from this browser. Check the network and browser access; your generated writing is still available.');
    throw error;
  } finally { clearTimeout(timer); signal?.removeEventListener('abort', abort); key = ''; }
}

/** Builds a self-contained, opt-in panel. All keys remain in memory and are cleared after one scan. */
export function mountExternalValidation(panel, {getDocuments, isBusy = () => false}) {
  if (!panel) return;
  const e = (tag, value, cls) => {const n=document.createElement(tag); if(value)n.textContent=value; if(cls)n.className=cls; return n;};
  const details = e('details'), summary = e('summary', 'Optional external check · GPTZero');
  const intro = e('p', 'Compare detector observations with human judgments. A lower AI probability is not proof of better writing. These results never change the manuscript, editing decisions or memory cards.');
  const selected = e('select'); selected.setAttribute('aria-label', 'Proposal to check');
  const input = e('input'); input.type='password'; input.autocomplete='off'; input.placeholder='Your GPTZero API key'; input.setAttribute('aria-label','GPTZero API key');
  const consent = e('input'); consent.type='checkbox';
  const consentLabel = e('label'); consentLabel.append(consent, document.createTextNode(' Send the selected manuscript directly to api.gptzero.me. This may use my separate GPTZero allowance.'));
  const scan = e('button','Check selected text'); scan.type='button'; scan.className='secondary';
  const cancel = e('button','Cancel check'); cancel.type='button'; cancel.disabled=true;
  const exportButton = e('button','Download detector observations'); exportButton.type='button'; exportButton.disabled=true;
  const status=e('p','No detector scan has been run.'); status.setAttribute('role','status');
  const list=e('div'); let documents=[], observations=[], controller=null;
  const controls=e('div',null,'detector-controls'); controls.append(selected,input,consentLabel,scan,cancel,exportButton);
  details.append(summary,intro,controls,status,list); panel.replaceChildren(details);
  function refresh() {const previous=selected.value; documents=getDocuments(); selected.replaceChildren(); for(const doc of documents){const option=e('option',doc.label);option.value=doc.id;selected.append(option);}if(documents.some(d=>d.id===previous))selected.value=previous;scan.disabled=!documents.length||isBusy()||Boolean(controller);}
  details.addEventListener('toggle',()=>{if(details.open)refresh();});
  scan.addEventListener('click',async()=>{
    if(controller || isBusy()) return;
    refresh(); const doc=documents.find(d=>d.id===selected.value); if(!doc){status.textContent='Generate or open a proposal first.';return;}
    if(!consent.checked){status.textContent='Confirm the destination before sending your text.';return;}
    controller=new AbortController(); scan.disabled=true;cancel.disabled=false; selected.disabled=true;input.disabled=true;
    status.textContent='Checking the selected text with GPTZero. The manuscript will not change.';
    try {
      const observation = await checkWithGPTZero({text:doc.text,key:input.value,signal:controller.signal});
      observations.push({...observation,documentId:doc.id,label:doc.label});
      const row=e('p',`${doc.label}: ${observation.predictedClass} · human ${(100*observation.probabilities.human).toFixed(1)}%, mixed ${(100*observation.probabilities.mixed).toFixed(1)}%, AI ${(100*observation.probabilities.ai).toFixed(1)}% · confidence ${observation.confidence}. Text fingerprint ${observation.textSHA256.slice(0,12)}.`, 'detector-observation');
      list.append(row);status.textContent='Observation saved. Percentages describe class probabilities, not the fraction of text written by AI. Re-enter your key to check another version.';exportButton.disabled=false;
    } catch(error) {status.textContent=error.message;}
    finally {input.value='';input.disabled=false;consent.checked=false;selected.disabled=false;controller=null;cancel.disabled=true;refresh();}
  });
  cancel.addEventListener('click',()=>controller?.abort());
  window.addEventListener('pagehide',()=>{controller?.abort();input.value='';});
  exportButton.addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({schema:'proseledger-detector-observations-1',observations,limitation:'External detector observations; not human naturalness ratings. No credentials included.'},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),link=e('a');link.href=url;link.download='proseledger_detector_observations.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);
  });
}
