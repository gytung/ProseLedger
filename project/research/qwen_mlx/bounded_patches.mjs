/** Apply exact, disjoint patches without allowing a second unrestricted rewrite. */
export function applyBoundedPatches(text, patches, issueCount, maxPatches=3, maxFraction=.35) {
  if (!Array.isArray(patches) || !patches.length || patches.length>maxPatches) return {ok:false,reason:'patch_count'};
  const spans=[];
  for (const patch of patches) {
    if(typeof patch.before!=='string'||!patch.before||typeof patch.after!=='string'||!patch.after.trim()) return {ok:false,reason:'patch_type'};
    if(!Number.isInteger(patch.issueIndex)||patch.issueIndex<0||patch.issueIndex>=issueCount) return {ok:false,reason:'issue_index'};
    const start=text.indexOf(patch.before);
    if(start<0||text.indexOf(patch.before,start+1)!==-1) return {ok:false,reason:'ambiguous_anchor'};
    spans.push({...patch,start,end:start+patch.before.length});
  }
  spans.sort((a,b)=>a.start-b.start);
  if(spans.some((s,i)=>i&&s.start<spans[i-1].end)) return {ok:false,reason:'overlap'};
  if(spans.reduce((n,s)=>n+s.before.length,0)>maxFraction*text.length) return {ok:false,reason:'coverage'};
  let result=text;
  for(const s of [...spans].reverse()) result=result.slice(0,s.start)+s.after+result.slice(s.end);
  return {ok:true,text:result,spans};
}
