import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  settingsForPreset, activePreset, clampCutHeight, initialPage, groups, parts,
  setGroupVisible, setPartVisible, isolatePart, isPartVisible, groupVisibilityState, anyVisible,
  initialPreset, modelLayouts, setFurnitureVisible,
} from '../src/model-state.ts';

test('internal views remove the actual covering floor and roof', () => {
  assert.deepEqual(settingsForPreset('first').visibility, { F1: true, F2: false, attic: false, attic_access: false, stairs: true, roof: false, foundation: false, yard: false, fence: false, lighting: false, structure: false });
  assert.deepEqual(settingsForPreset('second').visibility, { F1: false, F2: true, attic: false, attic_access: false, stairs: true, roof: false, foundation: false, yard: false, fence: false, lighting: false, structure: false });
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
  assert.deepEqual(isolated.visibility, { F1: false, F2: true, attic: false, attic_access: false, stairs: false, roof: false, foundation: false, yard: false, fence: false, lighting: false, structure: false });
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
  for (const { id } of groups) {
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
test('attic interior uses its own cut plane, hides the roof and preserves the furniture choice', () => {
  const exterior = settingsForPreset('exterior');
  assert.equal(exterior.visibility.attic, true);
  assert.equal(exterior.visibility.attic_access, false, 'deployed ladder is hidden in the whole-house view');
  const attic = settingsForPreset('attic', modelLayouts.house, setFurnitureVisible(exterior, false));
  assert.deepEqual(attic.visibility, { F1: false, F2: false, attic: true, attic_access: true, stairs: false, roof: false, foundation: false, yard: false, fence: false, lighting: false, structure: false });
  assert.equal(attic.cutaway, true);
  assert.equal(attic.heightMm, 6900, 'the attic cut plane must be above the attic floor');
  assert.ok(parts.filter(part => part.id.endsWith(':furniture')).every(part => attic.partVisibility[part.id] === false));
  assert.equal(activePreset(attic), 'attic');
  assert.equal(initialPreset('?mode=attic'), 'attic');
  assert.equal(initialPreset('?mode=attic', modelLayouts.apartment), 'interior');
  assert.equal(activePreset({ ...attic, heightMm: 6600 }), undefined, 'a moved attic plane is a custom view');
  assert.equal(activePreset({ ...exterior, heightMm: 6600 }), 'exterior', 'uncut presets do not constrain an unused height');
  assert.deepEqual(parts.filter(part => part.group === 'attic').map(part => part.id), [
    'attic:floor_slab', 'attic:partition_walls', 'attic:storage_fixtures', 'attic:guardrails',
  ]);
  assert.ok(parts.filter(part => part.group !== 'attic').every(part => !part.id.endsWith(':guardrails')));
  const hiddenLadder = setGroupVisible(attic, 'attic_access', false);
  assert.equal(isPartVisible(hiddenLadder, 'attic:floor_slab'), true);
  assert.equal(activePreset(hiddenLadder), undefined);
  assert.deepEqual(settingsForPreset('second', modelLayouts.house, attic).visibility,
    { F1: false, F2: true, attic: false, attic_access: false, stairs: true, roof: false, foundation: false, yard: false, fence: false, lighting: false, structure: false });
});

test('exterior site categories can be isolated while all internal presets hide the site', () => {
  const exterior = settingsForPreset('exterior');
  for (const group of ['foundation', 'yard', 'fence']) {
    assert.equal(groupVisibilityState(exterior, group), 'all');
    const only = isolatePart(exterior, group);
    assert.deepEqual(groups.filter(item => only.visibility[item.id]).map(item => item.id), [group]);
    assert.equal(groupVisibilityState(only, group), 'all');
    const restored = settingsForPreset('exterior', modelLayouts.house, only);
    assert.equal(activePreset(restored), 'exterior');
    for (const siteGroup of ['foundation', 'yard', 'fence']) assert.equal(groupVisibilityState(restored, siteGroup), 'all');
  }
  for (const preset of ['first', 'second', 'attic']) {
    const settings = settingsForPreset(preset);
    for (const group of ['foundation', 'yard', 'fence']) assert.equal(groupVisibilityState(settings, group), 'none', `${preset}: ${group}`);
    assert.equal(activePreset(settings), preset);
  }
  const edited = setPartVisible(exterior, 'yard:soil', false);
  assert.equal(groupVisibilityState(edited, 'yard'), 'some');
  assert.equal(isPartVisible(edited, 'yard:planting'), true);
  assert.equal(groupVisibilityState(edited, 'foundation'), 'all', 'soil visibility is independent of the building foundation');
  const isolated = isolatePart(edited, 'foundation:raft');
  assert.deepEqual(groups.filter(group => isolated.visibility[group.id]).map(group => group.id), ['foundation']);
  assert.deepEqual(parts.filter(part => isPartVisible(isolated, part.id)).map(part => part.id), ['foundation:raft']);
  assert.equal(isolated.cutaway, false);
  assert.equal(activePreset(setGroupVisible(edited, 'yard', true)), 'exterior');
  assert.deepEqual(parts.filter(part => part.group === 'fence').map(part => part.id), ['fence:posts', 'fence:panels', 'fence:footings']);
  assert.deepEqual(modelLayouts.apartment.groups.map(group => group.id), ['F1', 'ceiling', 'balcony']);
  assert.ok(modelLayouts.apartment.parts.every(part => part.group === 'F1'));
});
test('attic categories support visibility and isolation without revealing other floors', () => {
  const attic = settingsForPreset('attic');
  const edited = setPartVisible(attic, 'attic:guardrails', false);
  assert.equal(groupVisibilityState(edited, 'attic'), 'some');
  assert.equal(isPartVisible(edited, 'attic:floor_slab'), true);
  assert.equal(isPartVisible(edited, 'attic:guardrails'), false);
  const isolated = isolatePart(edited, 'attic:storage_fixtures');
  assert.deepEqual(groups.filter(group => isolated.visibility[group.id]).map(group => group.id), ['attic']);
  assert.deepEqual(parts.filter(part => isPartVisible(isolated, part.id)).map(part => part.id), ['attic:storage_fixtures']);
  assert.equal(isolated.cutaway, false);
});
test('invalid heights and shared plan URLs are handled safely', () => {
  assert.equal(clampCutHeight(NaN), 4200);
  assert.equal(clampCutHeight(-100), 0);
  assert.equal(clampCutHeight(12000), 8000);
  assert.equal(initialPage('?file=DXF%2F001D0PL2-1FPLAN.DXF'), '1f');
  assert.equal(initialPage('?view=2f'), '2f');
  assert.equal(initialPage('?view=unknown'), '3d');
});


test('structural scheme shows the candidate load path without finished envelopes', () => {
  const previous = setFurnitureVisible(settingsForPreset('second'), false);
  const structural = settingsForPreset('structure', modelLayouts.house, previous);
  assert.deepEqual(groups.filter(group => structural.visibility[group.id]).map(group => group.id), ['structure', 'foundation']);
  assert.equal(structural.cutaway, false, 'complete structural load path is initially visible');
  assert.equal(activePreset(structural), 'structure');
  assert.equal(initialPreset('?mode=structure'), 'structure');
  assert.equal(initialPreset('?mode=structure', modelLayouts.apartment), 'interior');
  assert.ok(parts.filter(part => part.group === 'structure').every(part => isPartVisible(structural, part.id)));
  assert.ok(parts.filter(part => part.id.endsWith(':furniture')).every(part => structural.partVisibility[part.id] === false));
  for (const preset of ['exterior', 'first', 'second', 'attic']) {
    const restored = settingsForPreset(preset, modelLayouts.house, structural);
    assert.equal(groupVisibilityState(restored, 'structure'), 'none', `${preset} must hide overlapping skeleton`);
    assert.equal(activePreset(restored), preset);
  }
  const columns = isolatePart(structural, 'structure:columns');
  assert.deepEqual(parts.filter(part => isPartVisible(columns, part.id)).map(part => part.id), ['structure:columns']);
  assert.equal(groupVisibilityState(columns, 'structure'), 'some');
});
