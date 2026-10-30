import test from 'node:test';
import assert from 'node:assert/strict';
import { BoxGeometry, Group, Mesh, MeshStandardMaterial, OrthographicCamera, Vector3 } from 'three';
import { bindLandmarkSteelDetails, readLandmarkSteelNodes } from '../src/landmark-steel-nodes.ts';
import { isObjectVisible } from '../src/model-scene.ts';

function fixture(t) {
  const root = new Group(), structure = new Group(); root.add(structure);
  const material = new MeshStandardMaterial(), geometries = [];
  const nodes = new Map([['structure', structure]]), entries = [], rivets = [], plates = [];
  const add = (name, x, y, size, metadata = {}) => {
    const geometry = new BoxGeometry(...size); geometries.push(geometry);
    const mesh = new Mesh(geometry, material); mesh.name = name; mesh.position.set(x, y, 0);
    Object.assign(mesh.userData, metadata); structure.add(mesh); nodes.set(name, mesh); return mesh;
  };
  for (let i = 0; i < 2; i++) {
    const id = `TT-N0${i + 1}`, x = i * 50, y = 10 + i * 20;
    const plate = add(`structure:${id}_plate`, x, y, [.8, 1, .08], { steelNodeId: id, steelDetailKind: 'plate' }); plates.push(plate);
    const member = add(`structure:${id}_member`, x, y + 40, [.2, 100, .2]);
    const nodeRivets = [];
    for (let j = 0; j < 2; j++) {
      const rivet = add(`structure:${id}_rivet_${j}`, x + (j ? .2 : -.2), y, [.05, .05, .06],
        { steelNodeId: id, steelDetailKind: 'rivet', steelMicro: true, landmarkRole: 'rivet_head' });
      nodeRivets.push(rivet); rivets.push(rivet);
    }
    entries.push({ id, type: 'illustrative_connection', names: { zh: `节点 ${i + 1}`, ja: `接合部 ${i + 1}`, en: `Connection ${i + 1}` },
      anchor_mm: [x * 1000, 0, y * 1000], member_names: [member.name], part_names: [plate.name, ...nodeRivets.map(node => node.name)],
      local_frame: { normal: [0, -1, 0] } });
  }
  rivets[1].visible = false;
  const lamp = add('structure:light_lens', 0, 10, [.1, .1, .1], { steelNodeId: 'TT-N01', steelDetailKind: 'rivet', steelMicro: true, landmarkRole: 'light_lens' });
  entries[0].part_names.push(lamp.name);
  const catalog = readLandmarkSteelNodes(entries);
  t.after(() => { geometries.forEach(geometry => geometry.dispose()); material.dispose(); });
  const camera = new OrthographicCamera(-4, 4, 4, -4, .1, 1000); camera.position.set(0, 10, 100); camera.lookAt(0, 10, 0); camera.updateProjectionMatrix();
  return { root, structure, nodes, entries, catalog, rivets, plates, lamp, camera, material, geometries };
}

test('steel catalog validates translations, finite CAD anchors and unique connection IDs', () => {
  for (const invalid of [null, {}, [null], [{ id: 'TT-N01' }]]) assert.throws(() => readLandmarkSteelNodes(invalid));
  const entry = { id: 'TT-N01', type: 'plate', names: { zh: '板', ja: '板', en: 'Plate' }, anchor_mm: [1, 2, 3], member_names: ['structure:member'], part_names: ['structure:plate'] };
  assert.equal(readLandmarkSteelNodes([entry])[0].names.en, 'Plate');
  assert.throws(() => readLandmarkSteelNodes([entry, entry]));
  assert.throws(() => readLandmarkSteelNodes([{ ...entry, anchor_mm: [1, Infinity, 3] }]));
  assert.throws(() => readLandmarkSteelNodes([{ ...entry, names: { ...entry.names, ja: '' } }]));
  assert.throws(() => readLandmarkSteelNodes([{ ...entry, part_names: [] }]));
});

test('each close-up frames only its local CAD plate and rivets, with one metre of margin', t => {
  const f = fixture(t), controller = bindLandmarkSteelDetails(f.nodes, f.catalog, f.root); t.after(() => controller.dispose());
  const first = controller.bounds('TT-N01'), second = controller.bounds('TT-N02');
  assert.deepEqual(first.getCenter(new Vector3()).toArray(), [0, 10, 0]);
  assert.deepEqual(second.getCenter(new Vector3()).toArray(), [50, 30, 0]);
  assert.ok(first.min.y > 8 && first.max.y < 12, 'the 100m member referenced for context must not inflate the ROI');
  assert.equal(controller.bounds('TT-N99'), null);
});

test('close-up bounds and CAD face directions respect parent translations, rotations and scale', t => {
  const f = fixture(t), controller = bindLandmarkSteelDetails(f.nodes, f.catalog, f.root); t.after(() => controller.dispose());
  f.root.position.set(100, 20, -3); f.root.rotation.y = Math.PI / 2; f.root.scale.setScalar(2);
  const first = controller.bounds('TT-N01');
  assert.ok(first.getCenter(new Vector3()).distanceTo(new Vector3(100, 40, -3)) < 1e-8);
  assert.equal(first.min.y, 38); assert.equal(first.max.y, 42);
  assert.ok(controller.direction('TT-N01').x > .95, 'CAD -Y normal maps through Y-up and the transformed root');
});

test('all four base cameras look from radial outside and above, including transformed parents', t => {
  const f = fixture(t);
  for (const x of [-40000, 40000]) for (const y of [-40000, 40000]) {
    const entry = { ...f.catalog[0], type: 'base', anchor_mm: [x, y, 1200], local_frame: { normal: [0, 0, 1] } };
    const controller = bindLandmarkSteelDetails(f.nodes, [entry], f.root);
    try {
      const radial = new Vector3(x, 0, -y).normalize(), up = new Vector3(0, 1, 0);
      const direction = controller.direction(entry.id);
      assert.ok(direction.dot(radial) > .85, 'every tower foot must be viewed from its own exterior quadrant');
      assert.ok(direction.dot(up) > .45 && direction.dot(up) < .55);
      assert.ok(direction.clone().cross(up).length() > .85, 'the base camera cannot collapse into a near-top view');
      f.root.position.set(100, 20, -3); f.root.rotation.set(.2, Math.PI / 3, 0); f.root.scale.setScalar(2);
      f.root.updateWorldMatrix(true, false);
      const expected = radial.multiplyScalar(1.2).addScaledVector(up, .7).normalize().transformDirection(f.root.matrixWorld);
      assert.ok(controller.direction(entry.id).distanceTo(expected) < 1e-12, 'parent rotation and scale also transform the chosen observation direction');
    } finally {
      controller.dispose(); f.root.position.set(0, 0, 0); f.root.rotation.set(0, 0, 0); f.root.scale.setScalar(1);
    }
  }
});

test('auto micro visibility follows view scale, zoom and framing without hiding plates or lamps', t => {
  const f = fixture(t), controller = bindLandmarkSteelDetails(f.nodes, f.catalog, f.root); t.after(() => controller.dispose());
  assert.deepEqual(controller.apply(f.camera, 'auto'), { microMeshes: 4, visibleMicroMeshes: 1 });
  assert.equal(f.rivets[0].visible, true); assert.equal(f.rivets[1].visible, false); assert.equal(f.rivets[2].visible, false);
  assert.ok(f.plates.every(node => node.visible)); assert.equal(f.lamp.visible, true);
  f.camera.top = 50; f.camera.bottom = -50; f.camera.updateProjectionMatrix();
  assert.equal(controller.apply(f.camera, 'auto').visibleMicroMeshes, 0);
  f.camera.zoom = 20; f.camera.updateProjectionMatrix();
  assert.equal(controller.apply(f.camera, 'auto').visibleMicroMeshes, 1, 'zooming to the same connection enables micro details');
  f.camera.position.set(50, 30, 100); f.camera.lookAt(50, 30, 0);
  assert.equal(controller.apply(f.camera, 'auto').visibleMicroMeshes, 2, 'orbit/pan target changes update the visible connection');
  assert.equal(f.rivets[0].visible, false);
});

test('manual micro controls preserve category visibility and leave original named meshes available for picking', t => {
  const f = fixture(t), controller = bindLandmarkSteelDetails(f.nodes, f.catalog, f.root); t.after(() => controller.dispose());
  assert.equal(controller.apply(f.camera, 'on').visibleMicroMeshes, 3);
  f.structure.visible = false;
  assert.equal(controller.apply(f.camera, 'on').visibleMicroMeshes, 0);
  assert.equal(isObjectVisible(f.rivets[0]), false);
  f.structure.visible = true;
  assert.equal(controller.apply(f.camera, 'on').visibleMicroMeshes, 3);
  assert.equal(f.nodes.get(f.rivets[0].name), f.rivets[0]);
  assert.equal(f.rivets[0].userData.steelNodeId, 'TT-N01');
  assert.equal(controller.apply(f.camera, 'off').visibleMicroMeshes, 0);
  assert.equal(f.lamp.visible, true);
});

test('connections with different rivet counts use their exported parts rather than a fixed head pattern', t => {
  const f = fixture(t);
  for (let index = 0; index < 7; index++) {
    const rivet = f.rivets[0].clone(); rivet.name = `structure:TT-N01_additional_rivet_${index}`; rivet.position.x += index * .05;
    f.structure.add(rivet); f.nodes.set(rivet.name, rivet); f.entries[0].part_names.push(rivet.name);
  }
  const controller = bindLandmarkSteelDetails(f.nodes, readLandmarkSteelNodes(f.entries), f.root); t.after(() => controller.dispose());
  assert.deepEqual(controller.apply(f.camera, 'on'), { microMeshes: 11, visibleMicroMeshes: 10 });
  assert.equal(controller.apply(f.camera, 'auto').visibleMicroMeshes, 8);
  f.camera.position.set(50, 30, 100); f.camera.lookAt(50, 30, 0);
  assert.equal(controller.apply(f.camera, 'auto').visibleMicroMeshes, 2);
});

test('dispose restores source visibility once and never disposes shared CAD resources', t => {
  const f = fixture(t), controller = bindLandmarkSteelDetails(f.nodes, f.catalog, f.root);
  const originals = f.rivets.map(node => node.visible); let disposed = 0;
  f.material.addEventListener('dispose', () => disposed++); f.geometries.forEach(geometry => geometry.addEventListener('dispose', () => disposed++));
  controller.apply(f.camera, 'off'); controller.dispose(); controller.dispose();
  assert.deepEqual(f.rivets.map(node => node.visible), originals); assert.equal(disposed, 0);
  assert.equal(controller.bounds('TT-N01'), null);
  assert.deepEqual(controller.apply(f.camera, 'on'), { microMeshes: 0, visibleMicroMeshes: 0 });
});

test('incomplete or inconsistent CAD references fail without changing source visibility', t => {
  const f = fixture(t), original = f.rivets.map(node => node.visible);
  assert.throws(() => bindLandmarkSteelDetails(f.nodes, [{ ...f.catalog[0], part_names: ['structure:missing'] }]));
  assert.throws(() => bindLandmarkSteelDetails(f.nodes, [{ ...f.catalog[0], id: 'TT-N20' }]));
  assert.deepEqual(f.rivets.map(node => node.visible), original);
});
