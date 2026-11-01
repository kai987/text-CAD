import test from 'node:test';
import assert from 'node:assert/strict';
import { Box3, BoxGeometry, Group, Mesh, MeshStandardMaterial, Raycaster, Vector3 } from 'three';
import { batchSkytreeOpaque } from '../src/skytree-opaque-batches.ts';
import { bindLandmarkMaterialLighting, landmarkLightRole } from '../src/landmark-lighting.ts';
import { landmarkCloseupBounds } from '../src/landmark-camera-bounds.ts';
import { landmarkCameraOptions, landmarkGroupForName } from '../src/landmark-copy.ts';
import { isObjectVisible } from '../src/model-scene.ts';

function fixture(t) {
  const root = new Group(), geometries = new Set(), materials = new Set();
  t.after(() => { for (const geometry of geometries) geometry.dispose(); for (const material of materials) material.dispose(); });
  const group = (name, parent = root) => {
    const node = new Group(); node.name = name; node.userData.cadName = name; parent.add(node); return node;
  };
  const material = (color = '#d7dfdf', options = {}) => {
    const value = new MeshStandardMaterial({ color, ...options }); materials.add(value); return value;
  };
  const box = (parent, name, position, options = {}) => {
    const geometry = options.geometry ?? new BoxGeometry(...(options.size ?? [2, 2, 2])); geometries.add(geometry);
    // One GLTF primitive has one material; BoxGeometry's six demo face groups are not native CAD geometry.
    geometry.clearGroups();
    const finish = options.material ?? material();
    for (const value of Array.isArray(finish) ? finish : [finish]) materials.add(value);
    const node = new Mesh(geometry, finish); node.name = name;
    node.userData = { cadName: name, landmarkGroup: name.split(':')[0], landmarkRole: options.role ?? 'body_brace' };
    node.position.fromArray(position); parent.add(node); return node;
  };
  return { root, group, material, box };
}
function proxies(root) {
  const result = []; root.traverse(node => { if (node.isMesh && node.userData.landmarkRole === 'opaque_display_batch') result.push(node); }); return result;
}
function positions(mesh) {
  mesh.updateWorldMatrix(true, false);
  const attribute = mesh.geometry.getAttribute('position');
  return Array.from({ length: attribute.count }, (_, i) => new Vector3().fromBufferAttribute(attribute, i).applyMatrix4(mesh.matrixWorld));
}
function boundsEqual(a, b, message) {
  assert.ok(a.min.distanceTo(b.min) < 1e-4 && a.max.distanceTo(b.max) < 1e-4, message);
}
function snapshotGeometry(mesh) {
  return { index: mesh.geometry.index && Array.from(mesh.geometry.index.array),
    attributes: Object.fromEntries(Object.entries(mesh.geometry.attributes).map(([key, value]) => [key, Array.from(value.array)])) };
}
function expectedLighting(root) {
  const counts = { 'warm-lens': 0, 'obstruction-lens': 0, 'lit-window': 0 };
  root.traverse(node => {
    if (!node.isMesh || !isObjectVisible(node)) return;
    const role = landmarkLightRole(String(node.userData.cadName ?? node.name), node.userData.landmarkRole);
    if (role in counts) counts[role] += (Array.isArray(node.material) ? node.material : [node.material]).filter(value => value.isMeshStandardMaterial).length;
  });
  return { mode: 'local-fixtures', warmFixtures: 0, coolFixtures: counts['warm-lens'], obstructionFixtures: counts['obstruction-lens'], litWindows: counts['lit-window'] };
}

test('opaque display batches preserve transformed vertices, triangles, names and source arrays', t => {
  const f = fixture(t), structure = f.group('structure');
  structure.position.set(3, 2, -4); structure.rotation.y = .41; structure.scale.set(1.7, 1.2, .8);
  const sources = Array.from({ length: 4 }, (_, i) => {
    const mesh = f.box(structure, `structure:brace_${i}`, [i * 3, 8 + i, i % 2]); mesh.rotation.set(.06 * i, .1 * i, .03 * i); return mesh;
  });
  f.root.updateWorldMatrix(true, true);
  const expectedBounds = new Box3().setFromObject(f.root, true), expectedVertices = sources.flatMap(positions);
  const names = sources.map(node => node.name), snapshots = sources.map(snapshotGeometry), materialRefs = sources.map(node => node.material);
  const controller = batchSkytreeOpaque(f.root, 'tokyo-skytree'); t.after(() => controller.dispose());
  assert.equal(controller.sourceMeshes, 4); assert.equal(controller.drawBatches, 1);
  const [batch] = proxies(f.root); assert.ok(batch); assert.equal(batch.parent, structure);
  assert.equal(batch.userData.landmarkGroup, 'structure'); assert.match(batch.userData.cadName, /^structure:opaque_display_batch_/);
  assert.equal(batch.userData.sourceMeshes, 4);
  assert.equal(batch.geometry.index.count, sources.reduce((sum, node) => sum + node.geometry.index.count, 0));
  const actualVertices = positions(batch);
  assert.equal(actualVertices.length, expectedVertices.length);
  for (const expected of expectedVertices) {
    const index = actualVertices.findIndex(actual => actual.distanceTo(expected) < 1e-4);
    assert.notEqual(index, -1, 'every original world-space vertex must survive baking the parent transform'); actualVertices.splice(index, 1);
  }
  boundsEqual(new Box3().setFromObject(batch, true), expectedBounds, 'merged bounds must match actual original geometry');
  sources.forEach((node, index) => {
    assert.equal(node.visible, false); assert.equal(node.name, names[index]); assert.equal(node.userData.cadName, names[index]);
    assert.equal(node.material, materialRefs[index]); assert.equal(node.parent, structure); assert.deepEqual(snapshotGeometry(node), snapshots[index]);
  });
});

test('same finish across material IDs batches while 50m bands, parent, finish and schema remain separate', t => {
  const f = fixture(t), structure = f.group('structure'), otherParent = f.group('structure:other_parent');
  const createPair = (parent, prefix, y, color = '#dde4e2', removeUv = false) => Array.from({ length: 2 }, (_, index) => {
    const finish = f.material(color); finish.name = `${prefix}_material_${index}`;
    const mesh = f.box(parent, `structure:${prefix}_${index}`, [index * 3, y, 0], { material: finish });
    if (removeUv) mesh.geometry.deleteAttribute('uv'); return mesh;
  });
  const sources = [...createPair(structure, 'low', 10), ...createPair(structure, 'high', 70),
    ...createPair(structure, 'red', 10, '#aa493e'), ...createPair(structure, 'no_uv', 10, '#dde4e2', true),
    ...createPair(otherParent, 'other', 10)];
  const controller = batchSkytreeOpaque(f.root, 'tokyo-skytree'); t.after(() => controller.dispose());
  assert.equal(controller.sourceMeshes, 10); assert.equal(controller.drawBatches, 5);
  assert.ok(sources.every(node => !node.visible));
  assert.deepEqual(proxies(f.root).map(node => node.userData.sourceMeshes), [2, 2, 2, 2, 2]);
  assert.equal(proxies(f.root).filter(node => node.parent === otherParent).length, 1);
});

test('transparent, emissive, shader, hidden, lens, glazing, array and morph sources retain original behavior', t => {
  const f = fixture(t), structure = f.group('structure'), core = f.group('core'), decks = f.group('decks');
  const accepted = [f.box(structure, 'structure:ordinary_0', [0, 10, 0]), f.box(structure, 'structure:ordinary_1', [3, 10, 0])];
  const excluded = [];
  const pair = (prefix, parent, configure) => {
    for (let index = 0; index < 2; index++) {
      const node = f.box(parent, `${parent.name}:${prefix}_${index}`, [index * 3, 10, 5]); configure?.(node, index); excluded.push(node);
    }
  };
  pair('transparent', structure, node => { node.material.transparent = true; node.material.opacity = .4; });
  pair('emissive', structure, node => { node.material.emissive.set('#112233'); });
  pair('shader', structure, node => { node.material.onBeforeCompile = () => {}; });
  pair('material_hidden', structure, node => { node.material.visible = false; });
  pair('material_hook', structure, node => { node.material.onBeforeRender = () => {}; });
  pair('node_hook', structure, node => { node.onBeforeRender = () => {}; });
  pair('light_lens', structure, node => { node.userData.landmarkRole = 'obstruction_light_lens'; });
  pair('glazing', structure, node => { node.userData.landmarkRole = 'glazing'; });
  pair('array', core, node => { node.material = [node.material]; });
  pair('morph', core, node => { node.geometry.morphAttributes.position = [node.geometry.getAttribute('position').clone()]; });
  pair('excluded_group', decks);
  const hiddenParent = f.group('structure:hidden_parent', structure); hiddenParent.visible = false;
  pair('ancestor_hidden', hiddenParent);
  pair('self_hidden', structure, node => { node.visible = false; });
  const original = excluded.map(node => ({ node, visible: node.visible, material: node.material, geometry: snapshotGeometry(node) }));
  const controller = batchSkytreeOpaque(f.root, 'tokyo-skytree'); t.after(() => controller.dispose());
  assert.equal(controller.sourceMeshes, 2); assert.equal(controller.drawBatches, 1); assert.ok(accepted.every(node => !node.visible));
  for (const value of original) {
    assert.equal(value.node.visible, value.visible, value.node.name); assert.equal(value.node.material, value.material, value.node.name);
    assert.deepEqual(snapshotGeometry(value.node), value.geometry, value.node.name);
  }
});

test('metadata lighting, group picking and all eight camera bounds remain native after batching', t => {
  const f = fixture(t), groups = Object.fromEntries(['base', 'structure', 'core', 'decks', 'antenna'].map(name => [name, f.group(name)]));
  f.box(groups.base, 'base:floor', [0, -1, 0]);
  for (let index = 0; index < 4; index++) f.box(groups.structure, `structure:brace_${index}`, [index * 3, 20, 0]);
  for (let index = 0; index < 4; index++) f.box(groups.core, `core:guide_${index}`, [index * 3, 60, 0]);
  f.box(groups.decks, 'decks:tembo_deck_crown_roof', [0, 375, 0], { role: 'deck_roof' });
  f.box(groups.decks, 'decks:tembo_galleria_roof', [0, 460, 0], { role: 'deck_roof' });
  f.box(groups.antenna, 'antenna:tmd_tip', [0, 633, 0]);
  for (let index = 0; index < 6; index++) f.box(groups.base, `base:plaza_light_lens_${index}`, [30 + index, 1.33, 0], { role: 'light_lens', size: [.3, .3, .3] });
  for (let index = 0; index < 11; index++) {
    const group = [groups.structure, groups.decks, groups.antenna][index % 3];
    f.box(group, `${group.name}:obstruction_light_lens_${index}`, [30 + index, 100 + index * 30, 0], { role: 'obstruction_light_lens', size: [.3, .3, .3] });
  }
  const litNames = Array.from({ length: 30 }, (_, i) => `decks:tembo_deck_glazing_fixture_${i}`)
    .filter(name => landmarkLightRole(name, 'glazing') === 'lit-window').slice(0, 2);
  assert.equal(litNames.length, 2);
  for (const [index, name] of litNames.entries()) f.box(groups.decks, name, [index * 3, 350, 0],
    { role: 'glazing', material: f.material('#7295a8', { transparent: true, opacity: .3 }) });
  f.root.updateWorldMatrix(true, true);
  const nodes = new Map(); f.root.traverse(node => { if (node.userData.cadName) nodes.set(node.userData.cadName, node); });
  const nativeSize = nodes.size, nativeBounds = new Box3().setFromObject(f.root);
  const before = landmarkCloseupBounds('tokyo-skytree', nodes, nativeBounds);
  const lights = bindLandmarkMaterialLighting(f.root, 'tokyo-skytree'); t.after(() => lights.dispose());
  const initialStats = lights.apply(true); assert.equal(initialStats.coolFixtures, 6); assert.equal(initialStats.obstructionFixtures, 11);
  const controller = batchSkytreeOpaque(f.root, 'tokyo-skytree'); t.after(() => controller.dispose());
  assert.equal(controller.sourceMeshes, 8); assert.equal(controller.drawBatches, 2);
  assert.equal(nodes.size, nativeSize, 'display proxies must not enter the native CAD catalog');
  assert.deepEqual(lights.apply(true), initialStats, 'native lenses and sparse glazing must not be counted twice or hidden');
  f.root.updateWorldMatrix(true, true);
  const afterBounds = new Box3().setFromObject(f.root), after = landmarkCloseupBounds('tokyo-skytree', nodes, afterBounds);
  for (const camera of landmarkCameraOptions('tokyo-skytree')) {
    boundsEqual(after.get(camera) ?? afterBounds, before.get(camera) ?? nativeBounds, camera);
  }
  const hits = new Raycaster(new Vector3(0, 20, 25), new Vector3(0, 0, -1)).intersectObject(f.root, true).filter(hit => isObjectVisible(hit.object));
  assert.ok(hits.length); assert.equal(hits[0].object.userData.landmarkRole, 'opaque_display_batch');
  assert.equal(landmarkGroupForName(hits[0].object.userData.cadName), 'structure');
  for (const name of ['structure', 'core', 'decks', 'antenna']) {
    groups[name].visible = false;
    assert.deepEqual(lights.apply(true), expectedLighting(f.root), `${name}: native night statistics follow the same visible category`);
    for (const proxy of proxies(f.root).filter(node => node.userData.landmarkGroup === name)) assert.equal(isObjectVisible(proxy), false);
    groups[name].visible = true;
  }
  assert.deepEqual(lights.apply(true), initialStats);
});

test('dispose is idempotent, restores source visibility and releases only owned merged geometry', t => {
  const f = fixture(t), structure = f.group('structure'), material = f.material(), geometry = new BoxGeometry(2, 2, 2);
  const sources = [f.box(structure, 'structure:brace_0', [0, 10, 0], { material, geometry }),
    f.box(structure, 'structure:brace_1', [3, 10, 0], { material, geometry }),
    f.box(structure, 'structure:already_hidden', [6, 10, 0], { material, geometry })];
  sources[2].visible = false;
  let sourceGeometryDisposals = 0, materialDisposals = 0, batchDisposals = 0;
  geometry.addEventListener('dispose', () => sourceGeometryDisposals++); material.addEventListener('dispose', () => materialDisposals++);
  const controller = batchSkytreeOpaque(f.root, 'tokyo-skytree');
  const [batch] = proxies(f.root); assert.ok(batch); batch.geometry.addEventListener('dispose', () => batchDisposals++);
  controller.dispose(); controller.dispose();
  assert.equal(batchDisposals, 1); assert.equal(sourceGeometryDisposals, 0); assert.equal(materialDisposals, 0);
  assert.deepEqual(sources.map(node => node.visible), [true, true, false]); assert.equal(proxies(f.root).length, 0);
  assert.equal(structure.children.length, 3); assert.ok(sources.every(node => node.material === material && node.geometry === geometry));
});

test('unrelated models remain an untouched no-op even when their structure has eligible geometry', t => {
  const f = fixture(t), structure = f.group('structure');
  const sources = [f.box(structure, 'structure:brace_0', [0, 10, 0]), f.box(structure, 'structure:brace_1', [3, 10, 0])];
  const before = sources.map(snapshotGeometry), controller = batchSkytreeOpaque(f.root, 'river');
  assert.equal(controller.sourceMeshes, 0); assert.equal(controller.drawBatches, 0); assert.equal(structure.children.length, 2);
  assert.ok(sources.every(node => node.visible)); controller.dispose(); controller.dispose();
  sources.forEach((node, index) => assert.deepEqual(snapshotGeometry(node), before[index]));
});

test('Tokyo batches ordinary frame members while connection picking and micro visibility stay independent', t => {
  const f = fixture(t), structure = f.group('structure'), core = f.group('core');
  const accepted = [f.box(structure, 'structure:brace_0', [0, 10, 0]), f.box(structure, 'structure:brace_1', [3, 10, 0])];
  const excluded = [
    f.box(structure, 'structure:node_plate', [0, 15, 0]),
    f.box(structure, 'structure:node_rivet', [1, 15, 0]),
    f.box(structure, 'structure:detail', [2, 15, 0]),
    f.box(core, 'core:stair_proxy_0', [0, 20, 0], { role: 'stair_tread_batch' }),
    f.box(core, 'core:stair_proxy_1', [2, 20, 0], { role: 'stair_tread_batch' }),
  ];
  excluded[0].userData.steelNodeId = 'TT-N01';
  excluded[1].userData.steelMicro = true;
  excluded[2].userData.steelDetailKind = 'plate';
  const originals = [...accepted, ...excluded].map(snapshotGeometry);
  const controller = batchSkytreeOpaque(f.root, 'tokyo-tower'); t.after(() => controller.dispose());
  assert.equal(controller.sourceMeshes, 2); assert.equal(controller.drawBatches, 1);
  assert.ok(accepted.every(node => !node.visible)); assert.ok(excluded.every(node => node.visible));
  excluded[1].visible = false;
  assert.equal(excluded[0].visible, true, 'hiding a rivet cannot hide its connection plate or the frame batch');
  assert.equal(proxies(f.root)[0].visible, true);
  [...accepted, ...excluded].forEach((node, index) => assert.deepEqual(snapshotGeometry(node), originals[index]));
  controller.dispose();
  assert.deepEqual(accepted.map(node => node.visible), [true, true]);
  assert.equal(excluded[1].visible, false, 'disposing the batching must not undo micro-detail state');
});
