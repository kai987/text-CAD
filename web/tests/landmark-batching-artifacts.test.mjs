import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { OrthographicCamera } from 'three';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { bindCadNodes } from '../src/model-scene.ts';
import { batchLandmarkStairs } from '../src/landmark-stair-batches.ts';
import { batchLandmarkOpaque } from '../src/skytree-opaque-batches.ts';
import { landmarkVisibleGeometry, landmarkPickableMeshes } from '../src/landmark-render-stats.ts';
import { bindLandmarkSteelDetails, readLandmarkSteelNodes } from '../src/landmark-steel-nodes.ts';

function sourceFingerprint(nodes) {
  const hash = createHash('sha256');
  for (const [name, node] of nodes) {
    if (!node.isMesh) continue;
    hash.update(name); hash.update(JSON.stringify(node.userData));
    for (const [key, attribute] of Object.entries(node.geometry.attributes)) {
      hash.update(key); hash.update(Buffer.from(attribute.array.buffer, attribute.array.byteOffset, attribute.array.byteLength));
    }
    if (node.geometry.index) hash.update(Buffer.from(node.geometry.index.array.buffer, node.geometry.index.array.byteOffset, node.geometry.index.array.byteLength));
  }
  return hash.digest('hex');
}

for (const id of ['tokyo-tower', 'tokyo-skytree']) test(`${id}: native named geometry survives display batching with exact triangles and independent steel connections`, async () => {
  const gltf = await loadGlbGeometry(new URL(`../../GLB/${id.replaceAll('-', '_')}.glb`, import.meta.url));
  const root = gltf.scene, nodes = bindCadNodes(gltf), originalFingerprint = sourceFingerprint(nodes);
  const native = landmarkVisibleGeometry(root), stairs = batchLandmarkStairs(root, id);
  const beforeOpaque = landmarkVisibleGeometry(root);
  const connections = [...nodes.values()].filter(node => node.isMesh && node.userData.steelNodeId);
  const visibleConnections = connections.map(node => node.visible);
  const controller = batchLandmarkOpaque(root, id);
  let steel;
  try {
    const batched = landmarkVisibleGeometry(root);
    assert.equal(batched.triangles, native.triangles, 'all original triangles remain displayed');
    assert.ok(controller.sourceMeshes > 1000);
    assert.ok(controller.drawBatches < 60, 'height/material bands keep submission count bounded');
    assert.equal(batched.meshes, beforeOpaque.meshes - controller.sourceMeshes + controller.drawBatches);
    assert.deepEqual(connections.map(node => node.visible), visibleConnections);
    assert.equal(sourceFingerprint(nodes), originalFingerprint, 'neither source arrays, metadata nor names change');
    if (id === 'tokyo-tower') {
      const catalog = readLandmarkSteelNodes(gltf.parser.json.asset.extras.steelNodes);
      assert.equal(catalog.length, 20); assert.equal(connections.length, 296);
      steel = bindLandmarkSteelDetails(nodes, catalog, root);
      const camera = new OrthographicCamera(-100, 100, 200, -200, .1, 1000);
      camera.position.set(0, 160, 500); camera.lookAt(0, 160, 0); camera.updateProjectionMatrix();
      assert.equal(steel.apply(camera, 'off').visibleMicroMeshes, 0);
      assert.equal(steel.apply(camera, 'on').visibleMicroMeshes, 248);
      assert.ok(landmarkPickableMeshes(root).filter(node => node.userData.steelNodeId).length === 296);
      for (const entry of catalog) assert.ok(steel.bounds(entry.id), entry.id);
    }
  } finally {
    steel?.dispose(); controller.dispose(); stairs.dispose();
    assert.deepEqual(landmarkVisibleGeometry(root), native);
    assert.equal(sourceFingerprint(nodes), originalFingerprint);
    const geometries = new Set(), materials = new Set();
    root.traverse(node => { if (node.isMesh) { geometries.add(node.geometry); for (const material of Array.isArray(node.material) ? node.material : [node.material]) materials.add(material); } });
    geometries.forEach(geometry => geometry.dispose()); materials.forEach(material => material.dispose());
  }
});
