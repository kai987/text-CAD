import test from 'node:test';
import assert from 'node:assert/strict';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { bindCadNodes, selectionFor, visibleMeshes } from '../src/model-scene.ts';
import { modelLayouts, settingsForPreset, activePreset, setFurnitureVisible,
  furnitureVisibilityState, setPartVisible, isolatePart } from '../src/model-state.ts';

test('furniture toggle keeps active storey, fixtures, cut height and preset intact', () => {
  for (const layout of Object.values(modelLayouts)) {
    const preset = layout.id === 'house' ? 'second' : 'interior';
    const initial = settingsForPreset(preset, layout);
    const cut = { ...initial, cutaway: true, heightMm: layout.id === 'house' ? 4200 : 900 };
    const off = setFurnitureVisible(cut, false, layout);
    assert.equal(furnitureVisibilityState(off, layout), 'none');
    assert.deepEqual(off.visibility, cut.visibility);
    assert.equal(off.heightMm, cut.heightMm);
    assert.equal(off.cutaway, true);
    for (const part of layout.parts.filter(p => !p.id.endsWith(':furniture'))) {
      assert.equal(off.partVisibility[part.id], initial.partVisibility[part.id]);
    }
    assert.equal(furnitureVisibilityState(initial, layout), 'all', 'previous state is immutable');
    const nextPreset = layout.id === 'house' ? 'first' : 'exterior';
    const changed = settingsForPreset(nextPreset, layout, off);
    assert.equal(furnitureVisibilityState(changed, layout), 'none');
    assert.equal(activePreset(changed, layout), nextPreset);
    assert.equal(furnitureVisibilityState(setFurnitureVisible(off, true, layout), layout), 'all');
  }
});

test('per-floor furniture supports partial checkbox state and category isolation', () => {
  const layout = modelLayouts.house;
  const initial = settingsForPreset('first', layout);
  const partial = setPartVisible(initial, 'F1:furniture', false, layout);
  assert.equal(furnitureVisibilityState(partial, layout), 'some');
  const isolated = isolatePart(initial, 'F2:furniture', layout);
  assert.equal(isolated.visibility.F1, false);
  assert.equal(isolated.visibility.F2, true);
  assert.equal(isolated.partVisibility['F2:fixtures'], false);
  assert.equal(isolated.partVisibility['F2:furniture'], true);
});

test('both downloadable GLBs contain real, independently selectable furniture and fixture groups', async () => {
  for (const [id, filename] of [['house', 'house_3d.glb'], ['apartment', 'apartment_2ldk.glb']]) {
    const gltf = await loadGlbGeometry(new URL(`../../GLB/${filename}`, import.meta.url));
    const nodes = bindCadNodes(gltf), layout = modelLayouts[id];
    for (const part of layout.parts.filter(p => /:(furniture|fixtures)$/.test(p.id))) {
      const group = nodes.get(part.id);
      assert.ok(group?.children.length, `${id} ${part.id}: real nonempty group`);
      const meshes = visibleMeshes(group);
      assert.ok(meshes.length > 4, 'detailed separate parts');
      assert.equal(selectionFor(meshes[0], layout)?.id, part.id);
      group.visible = false;
      assert.ok(!visibleMeshes(gltf.scene).includes(meshes[0]), 'hidden furniture is not pickable');
    }
  }
});
