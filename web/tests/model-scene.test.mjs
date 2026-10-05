import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { bindCadNodes, selectionFor, visibleMeshes } from '../src/model-scene.ts';

async function loadHouse() {
  const bytes = await readFile(new URL('../../GLB/house_3d.glb', import.meta.url));
  return new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
}

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
