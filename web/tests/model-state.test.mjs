import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { settingsForPreset, activePreset, clampCutHeight, initialPage, groups } from '../src/model-state.ts';

test('internal views remove the actual covering floor and roof', () => {
  assert.deepEqual(settingsForPreset('first').visibility, { F1: true, F2: false, stairs: true, roof: false });
  assert.deepEqual(settingsForPreset('second').visibility, { F1: false, F2: true, stairs: true, roof: false });
  const edited = settingsForPreset('first'); edited.visibility.F2 = true;
  assert.equal(activePreset(edited), undefined);
  assert.equal(activePreset(settingsForPreset('first')), 'first');
});
test('published GLB contains all real group names targeted by the controls', async () => {
  const bytes = await readFile(new URL('../../GLB/house_3d.glb', import.meta.url));
  const jsonLength = bytes.readUInt32LE(12);
  const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString());
  for (const { id } of groups) assert.ok(gltf.nodes.some(n => n.name === id && n.children?.length));
});
test('invalid heights and shared plan URLs are handled safely', () => {
  assert.equal(clampCutHeight(NaN), 4200);
  assert.equal(clampCutHeight(-100), 0);
  assert.equal(clampCutHeight(12000), 8000);
  assert.equal(initialPage('?file=DXF%2F001D0PL2-1FPLAN.DXF'), '1f');
  assert.equal(initialPage('?view=2f'), '2f');
  assert.equal(initialPage('?view=unknown'), '3d');
});
