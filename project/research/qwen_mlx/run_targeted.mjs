/** Run the archived Targeted control policy from an explicitly supplied frozen manuscript. */
import {parseArgs} from 'node:util';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {runProposal} from './targeted_engine.mjs';
const {values}=parseArgs({options:{input:{type:'string'},out:{type:'string'},help:{type:'boolean'}}});
if(values.help){console.log('node run_targeted.mjs --input archive/heldout/case01/dev_input.json --out NEW_DIRECTORY\nUses the frozen supplied manuscript; calls the authenticated hosted reviewer/writer.');process.exit(0);}
if(!values.input||!values.out)throw new Error('Both --input and --out are required.');
const input=JSON.parse(await readFile(resolve(values.input),'utf8'));
if(typeof input.text!=='string'||!input.text.trim())throw new Error('Input requires the frozen text field.');
const folder=resolve(values.out);await mkdir(folder,{recursive:false});
await writeFile(join(folder,'input.json'),JSON.stringify(input,null,2));
const callModel=async(messages,{stage})=>{
 const hash=createHash('sha256').update(JSON.stringify(messages)).digest('hex');
 const response=await new Promise((ok,bad)=>{
  const child=spawn(process.env.PROSELEDGER_PYTHON||'python3',[fileURLToPath(new URL('./model_bridge.py',import.meta.url))],{stdio:['pipe','pipe','pipe']});
  let out='',err='';child.stdout.on('data',b=>out+=b);child.stderr.on('data',b=>err+=b);child.on('error',bad);
  child.on('close',code=>{if(code)bad(new Error('Review service failed: '+err.slice(-250)));else try{ok(JSON.parse(out));}catch{bad(new Error('Unreadable transport response'));}});
  child.stdin.end(JSON.stringify({stage,messages}));
 });
 await writeFile(join(folder,stage+'.response.json'),JSON.stringify({stage,hash,messages,...response},null,2));
 console.log('Completed '+stage);return response.text;
};
const result=await runProposal({topic:input.topic,sources:input.sources,cards:[],ruleMode:'explicit',suppliedDraft:input.text,callModel});
await writeFile(join(folder,'targeted_result.json'),JSON.stringify(result,null,2));
await writeFile(join(folder,'proposal.md'),result.branches.targeted.text);
console.log('Saved '+join(folder,'proposal.md'));
