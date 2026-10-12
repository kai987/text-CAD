import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { bindCadNodes, isObjectVisible } from '../src/model-scene.ts';
import { initialRiverView, residentialUrl, riverCopy, riverDownloadFiles, riverGroups, riverUrl, riverViews } from '../src/river-copy.ts';

test('river routes preserve each host path and discard house-only floor, city and lighting state', () => {
  for (const base of ['http://127.0.0.1:4197/', 'https://kai987.github.io/text-CAD/', 'https://example.chatgpt.site/']) {
    for (const view of riverViews) {
      const url = new URL(riverUrl(`${base}?model=house&city=kyoto&system=RC&mode=attic&environment=night`, view));
      assert.equal(url.pathname, new URL(base).pathname);
      assert.equal(url.searchParams.get('model'), 'river');
      assert.equal(url.searchParams.get('view'), view);
      assert.deepEqual([...url.searchParams.keys()], ['model', 'view']);
      assert.equal(initialRiverView(url.search), view);
    }
    for (const model of ['house', 'apartment']) {
      const back = new URL(residentialUrl(`${base}?model=river&view=section`, model));
      assert.equal(back.pathname, new URL(base).pathname);
      assert.equal(back.searchParams.get('model'), model);
      assert.equal(back.searchParams.get('view'), '3d');
    }
  }
  assert.equal(initialRiverView('?view=1f'), 'plan');
  assert.equal(initialRiverView('?view=2f'), 'plan');
  assert.equal(initialRiverView('?view=invalid'), '3d');
});

test('every river group, view and deliverable has visible copy in all three languages', () => {
  assert.equal(Object.keys(riverGroups).length, 7);
  assert.equal(new Set(Object.values(riverGroups).flat()).size, Object.values(riverGroups).flat().length);
  for (const locale of ['zh', 'ja', 'en']) {
    const copy = riverCopy[locale];
    for (const view of riverViews) assert.ok(copy.tabs[view].length > 0);
    for (const group of Object.keys(riverGroups)) assert.ok(copy.groups[group].length > 0);
    for (const file of riverDownloadFiles) {
      assert.ok(copy.fileNames[file.id].length > 0);
      assert.ok(copy.fileDetails[file.id].length > 0);
    }
    assert.ok(copy.note.length > 30);
    assert.ok(copy.drawingNote.length > 30);
  }
  assert.equal(new Set(riverDownloadFiles.map(file => file.path)).size, riverDownloadFiles.length);
  assert.deepEqual(new Set(riverDownloadFiles.map(file => file.type)), new Set(['GLB', 'STEP', 'DXF', 'JSON', 'PY']));
});

test('river visibility groups are bound to actual native GLB nodes, including hidden landscape and access parts', async () => {
  const bytes = await readFile(new URL('../../GLB/river_demo.glb', import.meta.url));
  assert.equal(bytes.subarray(0, 4).toString(), 'glTF');
  assert.equal(bytes.readUInt32LE(4), 2);
  assert.equal(bytes.readUInt32LE(8), bytes.length);
  const jsonLength = bytes.readUInt32LE(12);
  assert.equal(bytes.subarray(16, 20).toString(), 'JSON');
  const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString());
  const names = new Set(gltf.nodes.map(node => node.name));
  for (const name of Object.values(riverGroups).flat()) assert.ok(names.has(name), `Missing native river node: ${name}`);
});

test('Three runtime resolves all river groups by original CAD names after GLTFLoader sanitizes colons', async t => {
  const bytes = await readFile(new URL('../../GLB/river_demo.glb', import.meta.url));
  // Parse the unmodified native file using the browser's real Three loader.
  // This asset has embedded geometry and material factors, so no DOM/polyfill is needed.
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const gltf = await new GLTFLoader().parseAsync(buffer, '');
  t.after(() => {
    const geometries = new Set(), materials = new Set();
    gltf.scene.traverse(node => {
      if (!node.isMesh) return;
      geometries.add(node.geometry);
      for (const material of Array.isArray(node.material) ? node.material : [node.material]) materials.add(material);
    });
    for (const geometry of geometries) geometry.dispose();
    for (const material of materials) material.dispose();
  });
  const cadNodes = bindCadNodes(gltf);
  const declared = Object.values(riverGroups).flat();
  assert.equal(declared.length, 16);
  for (const name of declared) {
    const node = cadNodes.get(name);
    assert.ok(node, `Runtime lookup must preserve CAD name ${name}`);
    assert.notEqual(node.name, name, 'GLTFLoader actually sanitized this colon-containing name');
    assert.equal(node.userData.cadName, name);
    assert.equal(gltf.scene.getObjectByName(name), undefined, 'unsanitized getObjectByName cannot be used by the river viewer');
    let firstMesh;
    node.traverse(child => { if (child.isMesh) firstMesh ??= child; });
    assert.ok(firstMesh, `Runtime river group ${name} contains visible geometry`);
    assert.equal(isObjectVisible(firstMesh), true);
    node.visible = false;
    assert.equal(isObjectVisible(firstMesh), false, 'the mapped category controls its actual descendants');
    node.visible = true;
    assert.equal(isObjectVisible(firstMesh), true);
  }
});
