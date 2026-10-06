import test from 'node:test';
import assert from 'node:assert/strict';
import { Box3, BoxGeometry, Group, Mesh } from 'three';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { bindCadNodes, centerModelAtFloorDatum, selectionFor, visibleMeshes } from '../src/model-scene.ts';

async function loadHouse() {
  return loadGlbGeometry(new URL('../../GLB/house_3d.glb', import.meta.url));
}

test('the architectural datum comes from the first-floor slab and is independent of site depth', () => {
  for (const depth of [0.5, 0.8, 3.6]) {
    const root = new Group();
    const slab = new Mesh(new BoxGeometry(7.236, 0.2, 7.236));
    slab.position.set(3.64, -0.1, -3.64);
    const site = new Mesh(new BoxGeometry(13, depth, 14));
    site.position.set(3, -depth / 2, -3);
    root.add(slab, site);
    assert.equal(centerModelAtFloorDatum(root, new Map([['F1:floor_slab', slab]])), true);
    assert.ok(Math.abs(new Box3().setFromObject(slab).max.y) < 1e-8, `floor top remains at zero above ${depth} m site depth`);
    assert.ok(Math.abs(new Box3().setFromObject(root).min.y + depth) < 3e-7, 'the foundation remains underground');
    slab.geometry.dispose(); site.geometry.dispose();
  }
  assert.equal(centerModelAtFloorDatum(new Group(), new Map()), false, 'missing datum must not silently fall back to the site bottom');
});

test('saved house and apartment slabs retain their finished-floor datum after placement', async () => {
  for (const filename of ['house_3d.glb', 'apartment_2ldk.glb']) {
    const gltf = await loadGlbGeometry(new URL(`../../GLB/${filename}`, import.meta.url));
    const nodes = bindCadNodes(gltf);
    assert.equal(centerModelAtFloorDatum(gltf.scene, nodes), true, filename);
    assert.ok(Math.abs(new Box3().setFromObject(nodes.get('F1:floor_slab')).max.y) < 1e-8, `${filename}: finished floor at Y=0`);
  }
});

test('loaded CAD names and picked window classification survive GLTF name sanitization', async () => {
  const gltf = await loadHouse();
  const nodes = bindCadNodes(gltf);
  assert.equal(nodes.size, gltf.parser.json.nodes.length, 'every named CAD node is bound');
  const window = nodes.get('F1:W01:glass');
  assert.ok(window?.isMesh);
  assert.notEqual(window.name, 'F1:W01:glass');
  assert.deepEqual(selectionFor(window), { id: 'F1:windows', name: 'F1:W01:glass', label: '一层 · 窗' });
});

test('hidden categories and floors cannot appear in the picking mesh list', async () => {
  const gltf = await loadHouse();
  const nodes = bindCadNodes(gltf);
  const window = nodes.get('F1:W01:glass');
  assert.ok(visibleMeshes(gltf.scene).includes(window));
  nodes.get('F1:windows').visible = false;
  assert.ok(!visibleMeshes(gltf.scene).includes(window));
  nodes.get('F2').visible = false;
  assert.ok(nodes.get('F2:floor_slab')?.isMesh);
  assert.ok(!visibleMeshes(gltf.scene).includes(nodes.get('F2:floor_slab')));
  assert.equal(selectionFor(nodes.get('roof:west_plane')).id, 'roof');
});
test('attic floor and access ladder are selectable independently of the roof and lower floors', async () => {
  const gltf = await loadHouse();
  const nodes = bindCadNodes(gltf);
  const slab = nodes.get('roof:attic_ceiling_slab');
  const finish = nodes.get('attic:deck_finish');
  const tread = nodes.get('attic_access:tread_01');
  assert.ok(slab?.isMesh && finish?.isMesh && tread?.isMesh);
  assert.equal(selectionFor(slab).id, 'attic:floor_slab', 'the preserved CAD slab belongs to the attic');
  assert.equal(selectionFor(finish).id, 'attic:floor_slab');
  assert.equal(selectionFor(nodes.get('attic:guardrail:west_rail')).id, 'attic:guardrails');
  assert.equal(selectionFor(nodes.get('attic:storage:west_shelf:middle')).id, 'attic:storage_fixtures');
  assert.equal(selectionFor(tread).id, 'attic_access');
  for (const group of ['F1', 'F2', 'roof', 'stairs']) nodes.get(group).visible = false;
  assert.ok(visibleMeshes(gltf.scene).includes(slab), 'hiding the roof must retain the attic floor');
  assert.ok(visibleMeshes(gltf.scene).includes(tread));
  nodes.get('attic_access').visible = false;
  assert.ok(!visibleMeshes(gltf.scene).includes(tread), 'ladder visibility does not hide the attic');
  assert.ok(visibleMeshes(gltf.scene).includes(finish));
  nodes.get('attic').visible = false;
  assert.ok(!visibleMeshes(gltf.scene).includes(slab));
});

test('site meshes select their real categories and support independent yard and fence visibility', async () => {
  const gltf = await loadHouse();
  const nodes = bindCadNodes(gltf);
  const foundation = nodes.get('foundation:raft:slab');
  const lawn = nodes.get('yard:planting:lawn_front');
  const fence = nodes.get('fence:panels:north_01');
  assert.ok(foundation?.isMesh && lawn?.isMesh && fence?.isMesh);
  assert.equal(selectionFor(foundation).id, 'foundation:raft');
  assert.equal(selectionFor(nodes.get('F1:exterior:foundation:west')).id, 'foundation:existing_plinth');
  assert.equal(selectionFor(nodes.get('foundation:stem_walls:west')).id, 'foundation:stem_walls');
  assert.equal(selectionFor(lawn).id, 'yard:planting');
  assert.equal(selectionFor(nodes.get('yard:entrance_path:lower_step')).id, 'yard:entrance_path');
  assert.equal(selectionFor(fence).id, 'fence:panels');
  assert.equal(selectionFor(nodes.get('fence:footings:north_01')).id, 'fence:footings');
  nodes.get('yard').visible = false;
  assert.ok(!visibleMeshes(gltf.scene).includes(lawn));
  assert.ok(visibleMeshes(gltf.scene).includes(foundation));
  assert.ok(visibleMeshes(gltf.scene).includes(fence));
  nodes.get('fence').visible = false;
  assert.ok(!visibleMeshes(gltf.scene).includes(fence));
  assert.ok(visibleMeshes(gltf.scene).includes(foundation));
});


test('R06 structure leaves select their independent categories without changing the floor datum', async () => {
  const gltf = await loadHouse();
  const nodes = bindCadNodes(gltf);
  assert.ok(nodes.get('structure')?.children.length);
  const samples = [
    ['structure:F1:column_C01', 'structure:columns'],
    ['structure:F2:beam_B01', 'structure:beams'],
    ['structure:F1:sill_B01', 'structure:sills'],
    ['structure:attic:trimmer_west', 'structure:attic_headers'],
    ['structure:roof:ridge_beam', 'structure:roof_framing'],
    ['structure:F1:bearing_wall_BW01', 'structure:bearing_walls'],
  ];
  for (const [name, category] of samples) {
    const mesh = nodes.get(name);
    assert.ok(mesh?.isMesh, `${name} is a named saved solid`);
    assert.equal(selectionFor(mesh).id, category);
  }
  nodes.get('structure').visible = false;
  assert.ok(!visibleMeshes(gltf.scene).includes(nodes.get(samples[0][0])), 'hidden skeleton cannot be picked');
  assert.equal(centerModelAtFloorDatum(gltf.scene, nodes), true);
  assert.ok(Math.abs(new Box3().setFromObject(nodes.get('F1:floor_slab')).max.y) < 1e-8);
});
