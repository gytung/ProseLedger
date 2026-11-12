/** Deterministic preservation checks extracted unchanged from the project browser engine. */
export const HEADINGS = Object.freeze([
  'Abstract', 'Introduction', 'Related Work', 'Methodology',
  'Planned Evaluation', 'Limitations and Conclusion',
]);
export const DIMENSIONS = Object.freeze(['clarity','specificity','flow','concision','academic_style']);
export const LIMITS = Object.freeze({
  topic:1600, sources:10, excerpt:4000, totalEvidence:24000, draft:18000,
  cards:8, card:6500, cardBudget:24000, localParagraphs:3, localChars:4500, calls:14,
});
function citations(value) {return new Set([...value.matchAll(/\[(S\d+)\]/g)].map(m=>m[1]));}
function numbers(value) {
  return new Set(value.replace(/\[S\d+\]/g,'').replace(/^#{1,6}[^\n]*$/gm,'').match(/(?<![\p{L}\d])\d+(?:[.,]\d+)*(?:%|\b)/gu)||[]);
}
function difference(left,right) {return [...left].filter(x=>!right.has(x));}
function structured(value) {
  const headings=[...value.matchAll(/^## (.+)$/gm)].map(m=>m[1].trim());
  return headings.length===HEADINGS.length&&headings.every((x,i)=>x===HEADINGS[i]);
}
export function guardCandidate(original,candidate,sources) {
  const findings=[];
  if(typeof candidate!=='string'||candidate.length<300||candidate.length>LIMITS.draft)findings.push('Candidate length is outside the supported range.');
  if(typeof candidate!=='string')return {passed:false,findings};
  if(!structured(candidate))findings.push('The six required proposal headings changed or are missing.');
  const used=citations(candidate),allowed=new Set(sources.map(x=>x.id));
  const unknown=difference(used,allowed);
  if(unknown.length)findings.push('Unknown source identifiers: '+unknown.join(', ')+'.');
  if(used.size<Math.min(2,sources.length))findings.push('At least two supplied sources must be cited.');
  const completed=[...candidate.matchAll(/\b(?:we\s+(?:found|observed|achieved|demonstrated|measured)|our\s+(?:results|experiments)\s+(?:show|confirm|demonstrate))\b/gi)].map(m=>m[0]);
  if(completed.length)findings.push('Possible completed-study claim: '+[...new Set(completed)].join('; ')+'.');
  if(original) {
    const removed=difference(citations(original),used);
    if(removed.length)findings.push('Source identifiers removed: '+removed.join(', ')+'.');
    const addedNumbers=difference(numbers(candidate),numbers(original)),removedNumbers=difference(numbers(original),numbers(candidate));
    if(addedNumbers.length)findings.push('Numeric tokens added: '+addedNumbers.join(', ')+'.');
    if(removedNumbers.length)findings.push('Numeric tokens removed: '+removedNumbers.join(', ')+'.');
  }
  return {passed:findings.length===0,findings};
}
