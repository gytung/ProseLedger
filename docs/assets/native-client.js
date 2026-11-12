/** Explicit, token-paired access to the user's loopback account connector. */
export function validateNativeConfig({base,token,model='account-default'}) {
 if(typeof base!=='string'||!/^http:\/\/(?:127\.0\.0\.1|localhost):11437\/?$/i.test(base.trim()))throw new Error('Use the local Codex connector at http://127.0.0.1:11437.');
 let u;try{u=new URL(base);}catch{throw new Error('Use the local Codex connector at http://127.0.0.1:11437.');}
 if(u.protocol!=='http:'||!['127.0.0.1','localhost'].includes(u.hostname)||u.port!=='11437'||!['','/'].includes(u.pathname)||u.username||u.password||u.search||u.hash)throw new Error('The account connector must run on this computer at port 11437.');
 if(typeof token!=='string'||!/^[A-Za-z0-9_-]{24,512}$/.test(token))throw new Error('Paste the pairing code printed by your local connector. This is not an API key.');
 if(typeof model==='string')model=model.trim()||'account-default';
 if(typeof model!=='string'||!/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$/.test(model)||model.includes(token))throw new Error('Enter a valid account model ID, or account-default.');
 return {base:u.origin,token,model:model.trim()};
}
const STAGES=/^(generate_initial_proposal|audit_sections|repair_section_findings|audit_full_revision|repair_full_findings_[12]|audit_repaired_full_[12])$/;
const abortError=()=>new DOMException('Account request cancelled.','AbortError');
function raceAbort(promise,signal){
 if(signal.aborted)return Promise.reject(abortError());
 return new Promise((resolve,reject)=>{const stop=()=>{signal.removeEventListener('abort',stop);reject(abortError());};signal.addEventListener('abort',stop,{once:true});Promise.resolve(promise).then(value=>{signal.removeEventListener('abort',stop);resolve(value);},error=>{signal.removeEventListener('abort',stop);reject(error);});});
}
export function createNativeClient(config,{fetchImpl=fetch,onStatus=()=>{},onUsage=()=>{},timeoutMs=260000}={}) {
 const c=validateNativeConfig(config);let secret=c.token;delete c.token;const active=new Set();
 const deadline=Number.isFinite(timeoutMs)?Math.min(260000,Math.max(1,timeoutMs)):260000;
 async function readResponse(response,signal,key){
  const reader=response.body?.getReader();let text='',bytes=0;const dec=new TextDecoder();
  if(!reader){text=await raceAbort(response.text(),signal);if(new TextEncoder().encode(text).length>2000000)throw new Error('The connector returned an oversized response.');}
  else {let complete=false;try{while(true){const {done,value}=await raceAbort(reader.read(),signal);if(done){complete=true;break;}bytes+=value.length;if(bytes>2000000)throw new Error('The connector returned an oversized response.');text+=dec.decode(value,{stream:true});}text+=dec.decode();}finally{if(!complete)Promise.resolve(reader.cancel()).catch(()=>{});reader.releaseLock();}}
  if(key&&text.includes(key))throw new Error('The connector echoed its pairing code; the response was discarded.');
  let data;try{data=JSON.parse(text);}catch{throw new Error('The local connector returned an incomplete response.');}
  if(!response.ok){const messages={401:'The pairing code is incorrect or the connector restarted. Paste the current code.',403:'The connector rejected this website origin. Use the public ProseLedger site.',409:'Your connector is busy with another request. Wait and resume.',413:'This request is too large for the local connector.',503:'Codex is unavailable or not signed in. Open the connector and complete account login.',504:'The account request timed out. Completed stages are saved; resume when ready.'};throw new Error(messages[response.status]||'The Codex connector could not finish this request. Check its local window and resume.');}
  if(!data||typeof data!=='object'||Array.isArray(data))throw new Error('The local connector returned an invalid response.');
  return data;
 }
 async function request(path,body,{signal,stage='account_connection',limit=deadline}={}){
  if(!secret)throw new Error('Reconnect using the pairing code from your local connector.');
  if(signal?.aborted)throw abortError();const key=secret,controller=new AbortController(),id=body?.requestId;let timedOut=false;
  const abort=()=>controller.abort();signal?.addEventListener('abort',abort,{once:true});const timer=setTimeout(()=>{timedOut=true;controller.abort();},limit);active.add(controller);
  const begin=Date.now();let ticker;
  if(path==='/call'){onStatus({stage,phase:'requesting',message:'Codex is processing this stage using your signed-in account.'});ticker=setInterval(()=>onStatus({stage,phase:'waiting',message:'Codex is working · '+Math.round((Date.now()-begin)/1000)+' seconds.'}),1000);}
  try{
   const res=await raceAbort(fetchImpl(c.base+path,{method:body?'POST':'GET',headers:{'X-ProseLedger-Token':key,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:controller.signal,mode:'cors',credentials:'omit',redirect:'error',cache:'no-store',referrerPolicy:'no-referrer'}),controller.signal);
   return await readResponse(res,controller.signal,key);
  }catch(error){
   if(controller.signal.aborted&&id){const stop=new AbortController(),stopTimer=setTimeout(()=>stop.abort(),5000);fetchImpl(c.base+'/cancel',{method:'POST',headers:{'X-ProseLedger-Token':key,'Content-Type':'application/json'},body:JSON.stringify({requestId:id}),signal:stop.signal,mode:'cors',credentials:'omit',redirect:'error',keepalive:true}).catch(()=>{}).finally(()=>clearTimeout(stopTimer));}
   if(timedOut)throw new Error('The Codex connector timed out. The request was cancelled; completed stages are saved for Resume.');
   if(controller.signal.aborted)throw abortError();
   if(error instanceof TypeError)throw new Error('Cannot reach your local Codex connector. Start it, allow this site local-network access in Chrome or Edge, and check the pairing code.');
   throw error;
  }finally{clearTimeout(timer);clearInterval(ticker);signal?.removeEventListener('abort',abort);active.delete(controller);}
 }
 async function probe({signal}={}){const r=await request('/status',null,{signal,limit:Math.min(20000,deadline)});if(r.ready!==true||r.authenticated!==true)throw new Error('Sign in to Codex in the connector window, then test the connection again.');return r;}
 async function callModel(messages,{stage,signal}={}){
  if(!STAGES.test(stage))throw new Error('This connector handles proposal generation, review and repair only.');
  if(!Array.isArray(messages)||messages.length<1||messages.length>8||messages.some(m=>!m||!['system','user'].includes(m.role)||typeof m.content!=='string'||!m.content||Object.keys(m).some(k=>!['role','content'].includes(k))))throw new Error('Only text system and user messages are accepted by this connector.');
  const body={messages,stage,model:c.model,requestId:crypto.randomUUID()},encoded=JSON.stringify(body);
  if(secret&&encoded.includes(secret))throw new Error('Keep the pair code out of research input and model settings.');
  if(new TextEncoder().encode(encoded).length>180000)throw new Error('This account request exceeds the connector size limit.');
  const r=await request('/call',body,{signal,stage});if(typeof r.text!=='string'||!r.text.trim()||r.text.length>100000)throw new Error('Codex returned no complete text response.');
  if(r.requestId!==body.requestId)throw new Error('The connector returned a different request ID. No response was adopted.');
  const count=x=>Number.isInteger(x)&&x>=0?x:null,a=count(r.usage?.input_tokens),b=count(r.usage?.output_tokens);onUsage({stage,model:r.model||c.model,inputTokens:a,outputTokens:b,totalTokens:a!==null&&b!==null?a+b:null,backend:'codex-account'});onStatus({stage,phase:'completed',message:'Codex returned a complete response.'});return r.text;
 }
 return{probe,callModel,clear(){for(const c of active)c.abort();secret='';},base:c.base,model:c.model};
}
