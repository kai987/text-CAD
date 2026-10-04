import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  settingsForPreset, activePreset, clampCutHeight, initialPage, groups, parts,
  setGroupVisible, setPartVisible, isolatePart, isPartVisible, groupVisibilityState, anyVisible,
} from '../src/model-state.ts';

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
  for (const part of parts) {
    const parent = gltf.nodes.find(n => n.name === part.group);
    assert.ok(parent.children.some(index => gltf.nodes[index].name === part.id),
      `${part.id} must be a real immediate child of ${part.group}`);
  }
});

test('child visibility respects parents, supports partial checks and restores all children', () => {
  const original = settingsForPreset('exterior');
  const edited = setPartVisible(original, 'F1:external_walls', false);
  assert.equal(isPartVisible(edited, 'F1:external_walls'), false);
  assert.equal(isPartVisible(edited, 'F1:doors'), true);
  assert.equal(groupVisibilityState(edited, 'F1'), 'some');
  assert.equal(activePreset(edited), undefined);
  assert.equal(original.partVisibility['F1:external_walls'], true, 'edits must preserve previous state');
  const hidden = setGroupVisible(edited, 'F1', false);
  assert.equal(groupVisibilityState(hidden, 'F1'), 'none');
  assert.equal(isPartVisible(hidden, 'F1:doors'), false);
  const restored = setGroupVisible(hidden, 'F1', true);
  assert.equal(groupVisibilityState(restored, 'F1'), 'all');
  assert.equal(activePreset(restored), 'exterior');
  const childEnabled = setPartVisible(hidden, 'F1:external_walls', true);
  assert.equal(childEnabled.visibility.F1, true, 'showing a child opens its parent');
});

test('single category isolation shows that category only and presets restore the entire model', () => {
  const original = settingsForPreset('exterior'); original.cutaway = true;
  const isolated = isolatePart(original, 'F2:windows');
  assert.deepEqual(isolated.visibility, { F1: false, F2: true, stairs: false, roof: false });
  assert.deepEqual(parts.filter(part => isPartVisible(isolated, part.id)).map(part => part.id), ['F2:windows']);
  assert.equal(groupVisibilityState(isolated, 'F2'), 'some');
  assert.equal(isolated.cutaway, false, 'isolated parts must not be clipped by a previous cutaway');
  assert.equal(anyVisible(isolated), true);
  assert.equal(activePreset(isolated), undefined);
  const restored = settingsForPreset('second');
  assert.ok(parts.every(part => restored.partVisibility[part.id]));
  assert.equal(activePreset(restored), 'second');
});

test('whole floor and root group isolation remain usable and no visible children is empty', () => {
  for (const id of ['F1', 'F2', 'stairs', 'roof']) {
    const isolated = isolatePart(settingsForPreset('exterior'), id);
    assert.deepEqual(groups.filter(group => isolated.visibility[group.id]).map(group => group.id), [id]);
    assert.equal(anyVisible(isolated), true);
    assert.equal(groupVisibilityState(isolated, id), 'all');
  }
  let empty = isolatePart(settingsForPreset('exterior'), 'F1');
  for (const part of parts.filter(part => part.group === 'F1')) empty = setPartVisible(empty, part.id, false);
  assert.equal(empty.visibility.F1, true, 'a parent can remain enabled while every child is hidden');
  assert.equal(groupVisibilityState(empty, 'F1'), 'none');
  assert.equal(anyVisible(empty), false);
});
test('invalid heights and shared plan URLs are handled safely', () => {
  assert.equal(clampCutHeight(NaN), 4200);
  assert.equal(clampCutHeight(-100), 0);
  assert.equal(clampCutHeight(12000), 8000);
  assert.equal(initialPage('?file=DXF%2F001D0PL2-1FPLAN.DXF'), '1f');
  assert.equal(initialPage('?view=2f'), '2f');
  assert.equal(initialPage('?view=unknown'), '3d');
});
