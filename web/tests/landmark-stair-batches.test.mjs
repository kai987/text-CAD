import test from 'node:test';
import assert from 'node:assert/strict';
import { Box3, BoxGeometry, Group, Mesh, MeshStandardMaterial } from 'three';
import { batchLandmarkStairs } from '../src/landmark-stair-batches.ts';

function fixture(t) {
  const root = new Group(), group = new Group(); group.name = 'core'; group.position.set(2, 0, -3); root.add(group);
  const material = new MeshStandardMaterial({ color: '#ddd6c9' });
  const treads = Array.from({ length: 600 }, (_, i) => {
    const geometry = new BoxGeometry(1.2, .08, .24);
    const mesh = new Mesh(geometry, material); mesh.name = `core:stair_flight_${Math.floor(i / 25)}_tread_${i}`;
    mesh.userData.landmarkRole = 'stair_tread'; mesh.position.set(i % 25 * .2, i * .21 + 18, (Math.floor(i / 25) % 2) * 2);
    group.add(mesh); return mesh;
  });
  root.updateWorldMatrix(true, true);
  t.after(() => { for (const mesh of treads) mesh.geometry.dispose(); material.dispose(); });
  return { root, group, treads, material };
}
test('all 600 treads retain geometry and bounds while using one display draw batch', t => {
  const f = fixture(t), before = new Box3().setFromObject(f.root);
  const sourceArrays = f.treads.map(node => Array.from(node.geometry.attributes.position.array));
  const controller = batchLandmarkStairs(f.root, 'tokyo-tower'); t.after(() => controller.dispose());
  assert.equal(controller.sourceMeshes, 600); assert.equal(controller.drawBatches, 1);
  const batch = f.group.children.find(node => node.userData.landmarkRole === 'stair_tread_batch');
  assert.ok(batch); assert.ok(f.treads.every(node => !node.visible));
  assert.equal(batch.geometry.index.count, f.treads.reduce((sum, node) => sum + node.geometry.index.count, 0));
  const after = new Box3().setFromObject(batch);
  assert.ok(before.min.distanceTo(after.min) < 1e-4); assert.ok(before.max.distanceTo(after.max) < 1e-4);
  f.treads.forEach((node, index) => assert.deepEqual(Array.from(node.geometry.attributes.position.array), sourceArrays[index]));
  assert.equal(batch.material, f.material);
  f.group.visible = false; assert.equal(batch.parent.visible, false);
});
test('disposing restores named source visibility and releases only the owned combined geometry once', t => {
  const f = fixture(t), controller = batchLandmarkStairs(f.root, 'tokyo-tower');
  const batch = f.group.children.find(node => node.userData.landmarkRole === 'stair_tread_batch');
  let geometryDisposals = 0, materialDisposals = 0;
  batch.geometry.addEventListener('dispose', () => geometryDisposals++);
  f.material.addEventListener('dispose', () => materialDisposals++);
  controller.dispose(); controller.dispose();
  assert.equal(geometryDisposals, 1); assert.equal(materialDisposals, 0);
  assert.ok(f.treads.every(node => node.visible)); assert.equal(f.group.children.length, 600);
});
test('Sky and prehidden tread sets retain their original display behavior', t => {
  const f = fixture(t), sky = batchLandmarkStairs(f.root, 'tokyo-skytree');
  assert.equal(sky.sourceMeshes, 0); assert.equal(f.group.children.length, 600); sky.dispose();
  f.treads[0].visible = false;
  const tokyo = batchLandmarkStairs(f.root, 'tokyo-tower');
  assert.equal(tokyo.sourceMeshes, 0); assert.equal(f.treads[0].visible, false); tokyo.dispose();
});

test('distinct CAD material IDs with equal finishes batch together without merging a different finish', t => {
  const root = new Group(), geometry = new BoxGeometry(1, .1, .25);
  const materials = Array.from({ length: 4 }, (_, index) => {
    const material = new MeshStandardMaterial({ color: index < 2 ? '#ccc4b9' : '#944126' });
    material.name = `native_finish_${index}`; return material;
  });
  const meshes = materials.map((material, index) => {
    const mesh = new Mesh(geometry, material); mesh.name = `core:stair_tread_${index}`;
    mesh.userData.landmarkRole = 'stair_tread'; root.add(mesh); return mesh;
  });
  const controller = batchLandmarkStairs(root, 'tokyo-tower');
  t.after(() => { controller.dispose(); geometry.dispose(); materials.forEach(material => material.dispose()); });
  assert.equal(controller.sourceMeshes, 4); assert.equal(controller.drawBatches, 2);
  const proxies = root.children.filter(node => node.userData.landmarkRole === 'stair_tread_batch');
  assert.deepEqual(proxies.map(node => node.material.color.getHex()).sort(), [materials[0].color.getHex(), materials[2].color.getHex()].sort());
  assert.ok(meshes.every(mesh => !mesh.visible));
});
