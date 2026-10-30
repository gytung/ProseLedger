import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
const read=p=>readFile(new URL('../'+p,import.meta.url),'utf8');
const html=await read('docs/writing-demo.html');
const embedded=html.match(/<script id="evidence" type="application\/json">([\s\S]*?)<\/script>/)[1];
const data=JSON.parse(embedded),app=html.match(/<script>\s*('use strict';[\s\S]*?)<\/script>/)[1];
class Element {
 constructor(){this.children=[];this.attributes={};this.content='';this.value='';this.disabled=false;}
 set textContent(v){this.content=String(v);this.children=[];}get textContent(){return this.content+this.children.map(x=>x.textContent).join('');}
 append(...nodes){this.children.push(...nodes);nodes.forEach(n=>n.parent=this);}replaceChildren(...nodes){this.content='';this.children=[];this.append(...nodes);}setAttribute(k,v){this.attributes[k]=v;}click(){if(!this.disabled)this.onclick?.();}remove(){if(this.parent)this.parent.children=this.parent.children.filter(x=>x!==this);}
}
function mount(){const nodes=new Map([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));nodes.get('evidence').textContent=embedded;let now=0,next=0,network=0;const timers=new Map();const get=id=>{assert.ok(nodes.has(id),id);return nodes.get(id);};
 const document={getElementById:get,createElement:()=>new Element(),body:new Element()};
 const context=vm.createContext({document,console,Blob,URL:{createObjectURL:()=>'',revokeObjectURL(){}},Date:{now:()=>now},setInterval:fn=>{timers.set(++next,fn);return next;},clearInterval:id=>timers.delete(id),setTimeout:()=>0,fetch:()=>{network++;throw new Error('No network allowed');}});
 vm.runInContext(app,context);return {get,network:()=>network,advance:s=>{now+=s*1000;[...timers.values()].forEach(fn=>fn());}};
}
test('walkthrough embeds the full evidence unchanged and has no model or external runtime call',async()=>{
 assert.deepEqual(data,JSON.parse(await read('docs/natural-writing-evidence.json')));assert.equal(html,(await read('scripts/writing-demo.template.html')).replace('__EVIDENCE__',embedded));
 assert.match(html,/Recorded real-model run/);const ui=mount();assert.equal(ui.network(),0);
});
test('displayed round scores and actual edits come from the selected record',()=>{
 const ui=mount();for(const run of data.runs){ui.get('run-select').value=run.id;ui.get('run-select').onchange();for(const label of ['targeted','planner','memory']){ui.get('branch').value=label;ui.get('branch').onchange();const edits=run.result.branches[label].rounds.flatMap(row=>row.edits.map(edit=>({row,edit})));if(edits.length){const entry=edits.find(x=>x.row.accepted)||edits[0];assert.equal(ui.get('before').textContent,entry.edit.rules?.[0]?.beforeQuote||entry.edit.before);assert.equal(ui.get('after').textContent,entry.edit.rules?.[0]?.afterQuote||entry.edit.after);assert.ok(ui.get('decision').textContent.startsWith(entry.row.accepted?'RETAINED':'NOT RETAINED'));}}
 const rows=ui.get('score-table').children[0].children.slice(1);['targeted','planner','memory'].forEach((k,i)=>{assert.deepEqual(rows[i].children.slice(1,5).map(n=>n.textContent),[0,1,2,3].map(n=>String(run.result.branches[k].rounds.find(r=>r.round===n).retainedScore)));});}
});
test('the 120-second tour reaches all five chapters and can restart without altering results',()=>{
 const ui=mount(),original=ui.get('score-table').textContent;ui.get('tour').click();for(const [advance,chapter]of [[0,0],[15,1],[25,2],[35,3],[25,4],[20,4]]){ui.advance(advance);assert.equal(ui.get('stage-'+chapter).hidden,false);}assert.equal(ui.get('clock').textContent,'2:00 / 2:00');ui.get('restart').click();assert.equal(ui.get('stage-0').hidden,false);assert.equal(ui.get('score-table').textContent,original);
});
test('all recorded accepted edits have actual changes and their rule quotes match exact text',()=>{
 for(const run of data.runs)for(const branch of Object.values(run.result.branches))for(const row of branch.rounds){if(row.accepted&&row.round>0){assert.equal(row.changed,true);assert.equal(row.guard.passed,true);assert.equal(row.audit.preservation.passed,true);assert.equal(row.pairwise,'better');}for(const edit of row.edits)for(const rule of edit.rules||[]){assert.ok(edit.before.includes(rule.beforeQuote));assert.ok(edit.after.includes(rule.afterQuote));assert.notEqual(rule.beforeQuote,rule.afterQuote);}}
});
