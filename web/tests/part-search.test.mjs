import test from 'node:test';
import assert from 'node:assert/strict';
import { filterPartTree } from '../src/part-search.ts';
import { modelLayouts, settingsForPreset } from '../src/model-state.ts';
import { messages } from '../src/localization.ts';
function search(locale,query,model='house') {
  const copy=messages[locale]; return filterPartTree(modelLayouts[model],query,id=>copy.groups[id],id=>copy.partKinds[id.split(':')[1]]);
}
test('localized part searches retain group hierarchy and never modify model state',()=>{
  for (const [locale,word] of [['zh','窗'],['ja','窓'],['en','WINDOWS']]) {
    const state=settingsForPreset('exterior');const snapshot=JSON.stringify(state);
    const result=search(locale,word);
    assert.equal(result.length,3);assert.ok(result.every(group=>group.children.every(part=>part.id.endsWith(':windows'))));
    assert.equal(JSON.stringify(state),snapshot);
  }
});
test('whole group, empty, technical and no-match searches work for both models',()=>{
  assert.equal(search('zh','一层')[0].children.length,modelLayouts.house.parts.filter(part=>part.group==='F1').length);
  assert.equal(search('en','  ').length,modelLayouts.house.groups.length);
  assert.equal(search('en','F2:windows')[0].children[0].id,'F2:windows');
  assert.equal(search('ja','バルコニー','apartment')[0].group.id,'balcony');
  assert.equal(search('zh','不存在的部件').length,0);
});
