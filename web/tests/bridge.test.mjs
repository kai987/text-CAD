import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { Box3, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { bindCadNodes } from '../src/model-scene.ts';
import { bridgeDisplay } from '../src/bridge-batches.ts';
import { bridgeActorPose, parseBridgeActivity } from '../src/bridge-motion.ts';
import { bridgeCameras, bridgeCopy, bridgeDownloads, bridgeGroupForName, bridgeGroups, bridgeUrl, bridgeViews, initialBridgeView } from '../src/bridge-copy.ts';

test('bridge routes retain the deployment base and environment without residential state', () => {
  for (const base of ['http://127.0.0.1:4215/text-CAD/', 'https://example.chatgpt.site/', 'https://kai987.github.io/text-CAD/']) {
    for (const view of bridgeViews) {
      const url = new URL(bridgeUrl(`${base}?view=2f&city=tokyo&system=RC&mode=attic&environment=night`, view));
      assert.equal(url.pathname, new URL(base).pathname);
      assert.deepEqual([...url.searchParams.keys()], ['model', 'view', 'environment']);
      assert.equal(url.searchParams.get('model'), 'seto-ohashi');
      assert.equal(url.searchParams.get('environment'), 'night'); assert.equal(initialBridgeView(url.search), view);
    }
  }
  assert.equal(initialBridgeView('?view=2f'), 'plan'); assert.equal(initialBridgeView('?view=__proto__'), '3d');
});

test('all bridge controls and downloads have Chinese, Japanese and English labels', () => {
  for (const locale of ['zh', 'ja', 'en']) {
    const copy = bridgeCopy[locale];
    for (const view of bridgeViews) assert.ok(copy.tabs[view]?.trim());
    for (const camera of bridgeCameras) assert.ok(copy.cameras[camera]?.trim());
    for (const group of bridgeGroups) assert.ok(copy.groups[group]?.trim());
    for (const file of bridgeDownloads) { assert.ok(copy.fileNames[file.id]?.trim()); assert.ok(copy.fileDetails[file.id]?.trim()); }
    assert.ok(copy.note.length > 30);
    for (const key of ['title', 'play', 'pause', 'waves', 'note', 'reduced']) assert.ok(copy.motion[key]?.trim());
  }
  assert.equal(new Set(bridgeDownloads.map(file => file.path)).size, bridgeDownloads.length);
  for (const group of bridgeGroups) { assert.equal(bridgeGroupForName(`${group}:north:part`), group); assert.equal(bridgeGroupForName(`${group}-north-part`), group); }
  assert.equal(bridgeGroupForName('unknown:part'), null);
});

test('native bridge batching retains every visibility group, triangle and world-space extent', async () => {
  // A staged candidate can be inspected read-only before native gate promotion.
  const bytes = await readFile(process.env.SETO_NATIVE_GLB ?? new URL('../../GLB/seto_ohashi.glb', import.meta.url));
  const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
  bindCadNodes(gltf);
  const originalBounds = new Box3().setFromObject(gltf.scene);
  let triangles = 0, meshes = 0;
  gltf.scene.traverse(node => { if (node.isMesh) { triangles += (node.geometry.index?.count ?? node.geometry.getAttribute('position').count) / 3; meshes++; } });
  const activity = parseBridgeActivity(gltf.parser.json.asset.extras.activity);
  const byName = new Map(); gltf.scene.traverse(node => { if (node.isMesh) byName.set(node.userData.cadName ?? node.name, node); });
  const { display, groups, actors, ownedMaterials } = bridgeDisplay(gltf.scene, activity);
  display.applyMatrix4(gltf.scene.matrixWorld);
  try {
    const actualBounds = new Box3().setFromObject(display);
    assert.ok(originalBounds.min.distanceTo(actualBounds.min) < 1e-3);
    assert.ok(originalBounds.max.distanceTo(actualBounds.max) < 1e-3);
    assert.ok(originalBounds.getSize(new Vector3()).x > 3300, 'full twin-bridge layout is expressed in metres');
    let actualTriangles = 0;
    display.traverse(node => { if (node.isMesh) actualTriangles += (node.geometry.index?.count ?? node.geometry.getAttribute('position').count) / 3; });
    assert.equal(actualTriangles, triangles);
    assert.ok(display.children.length < meshes / 5, 'identical CAD finishes are batched');
    assert.deepEqual(new Set(groups.keys()), new Set(bridgeGroups));
    assert.equal(actors.size, 36);
    for (const actor of activity.actors) {
      const before = new Box3(); for (const name of actor.part_names) before.expandByObject(byName.get(name), true);
      const after = new Box3().setFromObject(actors.get(actor.id).object, true);
      assert.ok(before.min.distanceTo(after.min) < 1e-3 && before.max.distanceTo(after.max) < 1e-3, actor.id + ': origin localization preserves precise native vertex bounds');
    }
    assert.ok([...actors.values()].every(actor => actor.object.children.length < 4), 'actor colours share the native PBR finish');
    const crossbeams = [...byName].filter(([name]) => /^towers:(north|south):tower_[12]:crossbeam_2$/.test(name));
    assert.equal(crossbeams.length, 0, 'photo portal has no above-road crossbar');
    const portals = [...byName].filter(([name]) => /^towers:(north|south):tower_[12]:leg_1$/.test(name));
    assert.equal(portals.length, 4);
    for (const actor of activity.actors.filter(item => item.group === 'traffic')) {
      for (const [legName, leg] of portals) {
        const station = new Box3().setFromObject(leg, true).getCenter(new Vector3()).x * 1000;
        const length = actor.route.max_mm - actor.route.min_mm;
        const distance = ((station - actor.origin_mm[0]) * actor.direction % length + length) % length;
        const pose = bridgeActorPose(actor, activity, distance / (actor.speed_mps * 1000), false);
        const object = actors.get(actor.id).object; object.position.copy(pose.position); object.quaternion.copy(pose.rotation);
        const vehicleBounds = new Box3().setFromObject(object, true);
        assert.ok(Math.abs(pose.position.x * 1000 - station) < .01);
        const prefix=legName.replace(/leg_1$/, '');
        for (const [name, part] of byName) {
          if (!name.startsWith(prefix)) continue;
          const bounds=new Box3().setFromObject(part,true);
          const gap=Math.max(bounds.min.x-vehicleBounds.max.x,vehicleBounds.min.x-bounds.max.x,
            bounds.min.y-vehicleBounds.max.y,vehicleBounds.min.y-bounds.max.y,
            bounds.min.z-vehicleBounds.max.z,vehicleBounds.min.z-bounds.max.z);
          assert.ok(gap>1,actor.id+': needs >1m separation from actual tower member '+name);
        }
      }
    }
    for (const [group, nodes] of groups) {
      assert.ok(nodes.length > 0); nodes.forEach(node => { assert.equal(node.userData.bridgeGroup, group); node.visible = false; });
      assert.ok(nodes.every(node => !node.visible));
      nodes.forEach(node => { node.visible = true; });
    }
  } finally {
    display.traverse(node => { if (node.isMesh) node.geometry.dispose(); }); ownedMaterials.forEach(material => material.dispose());
    gltf.scene.traverse(node => { if (node.isMesh) { node.geometry.dispose(); for (const material of Array.isArray(node.material) ? node.material : [node.material]) material.dispose(); } });
  }
});
