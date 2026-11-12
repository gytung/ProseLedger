import assert from 'node:assert/strict';
import {applyBoundedPatches as patch} from './bounded_patches.mjs';
const source='This work motivates the method, while its effectiveness remains unknown.';
assert.equal(patch(source,[{before:'motivates',after:'informs',issueIndex:0}],1).text,
  'This work informs the method, while its effectiveness remains unknown.');
assert.equal(patch('same same',[{before:'same',after:'other',issueIndex:0}],1).ok,false);
assert.equal(patch(source,[{before:'work motivates',after:'work informs',issueIndex:0},
  {before:'motivates',after:'supports',issueIndex:0}],1).ok,false);
assert.equal(patch(source,[{before:source,after:'A replacement',issueIndex:0}],1).ok,false);
assert.equal(patch(source,[{before:'work',after:'study',issueIndex:2}],1).ok,false);
assert.equal(patch(source,[{before:null,after:'text',issueIndex:0}],1).ok,false);
console.log('Bounded editing validation: 6 checks passed');
