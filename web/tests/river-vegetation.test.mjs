import test, { after, before } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { Box3, DoubleSide, Mesh } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { bindCadNodes, isObjectVisible } from '../src/model-scene.ts';
import { riverGroups } from '../src/river-copy.ts';

let gltf, manifest, cadNodes, crowns;

before(async () => {
  const [bytes, metadata] = await Promise.all([
    readFile(new URL('../../GLB/river_demo.glb', import.meta.url)),
    readFile(new URL('../../output/review/river_demo_manifest.json', import.meta.url), 'utf8'),
  ]);
  manifest = JSON.parse(metadata);
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  // Exercise the downloadable file with the same loader and CAD-name binding as the viewer.
  gltf = await new GLTFLoader().parseAsync(buffer, '');
  cadNodes = bindCadNodes(gltf);
  gltf.scene.updateMatrixWorld(true);
  crowns = [...cadNodes].filter(([name]) => name.startsWith('Landscape:trees:') && name.endsWith(':crown'));
});

after(() => {
  if (!gltf) return;
  const geometries = new Set(), materials = new Set();
  gltf.scene.traverse(node => {
    if (!(node instanceof Mesh)) return;
    geometries.add(node.geometry);
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) materials.add(material);
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) material.dispose();
});

test('all fourteen downloadable river crowns load as colored, opaque, double-sided foliage meshes', () => {
  assert.equal(manifest.trees.length, 14);
  assert.equal(crowns.length, 14);
  assert.deepEqual(new Set(crowns.map(([name]) => name)),
    new Set(manifest.trees.map(tree => `Landscape:trees:${tree.id}:crown`)));

  for (const [name, crown] of crowns) {
    assert.ok(crown instanceof Mesh, `${name} remains one directly selectable CAD mesh`);
    assert.equal(crown.userData.cadName, name);
    const position = crown.geometry.getAttribute('position');
    const color = crown.geometry.getAttribute('color');
    assert.ok(position && position.count > 0, `${name} has decoded leaf geometry`);
    assert.ok(crown.geometry.index && crown.geometry.index.count > 0);
    assert.ok(color, `${name} exposes COLOR_0 as a Three color attribute`);
    assert.equal(color.itemSize, 3);
    assert.equal(color.count, position.count);
    let darkest = Infinity, brightest = -Infinity;
    for (let i = 0; i < color.count; i++) {
      for (const value of [color.getX(i), color.getY(i), color.getZ(i)]) {
        assert.ok(Number.isFinite(value) && value >= 0 && value <= 1, `${name} has usable vertex colors`);
        darkest = Math.min(darkest, value);
        brightest = Math.max(brightest, value);
      }
    }
    assert.ok(brightest - darkest > 0.1, `${name} retains natural color variation`);
    const materials = Array.isArray(crown.material) ? crown.material : [crown.material];
    assert.equal(materials.length, 1, `${name} does not require one material per leaf`);
    assert.equal(materials[0].vertexColors, true, `${name} actually uses its decoded colors`);
    assert.equal(materials[0].side, DoubleSide);
    assert.equal(materials[0].transparent, false);
    assert.equal(materials[0].opacity, 1);
    assert.equal(materials[0].alphaTest, 0);
  }
});

test('decoded river crowns retain finite world bounds within their recorded planting footprints', () => {
  for (const tree of manifest.trees) {
    const name = `Landscape:trees:${tree.id}:crown`;
    const crown = cadNodes.get(name);
    assert.ok(crown instanceof Mesh, name);
    const bounds = new Box3().setFromObject(crown);
    assert.equal(bounds.isEmpty(), false, name);
    assert.ok([...bounds.min.toArray(), ...bounds.max.toArray()].every(Number.isFinite));
    assert.ok(bounds.max.x > bounds.min.x && bounds.max.y > bounds.min.y && bounds.max.z > bounds.min.z);
    const east = tree.x / 1000, south = -tree.y / 1000, radius = tree.radius / 1000;
    const tolerance = 0.001;
    assert.ok(bounds.min.x >= east - radius - tolerance && bounds.max.x <= east + radius + tolerance, `${name} respects east-west planting bounds`);
    assert.ok(bounds.min.z >= south - radius - tolerance && bounds.max.z <= south + radius + tolerance, `${name} respects north-south planting bounds`);
    assert.ok(bounds.min.y > tree.z / 1000, `${name} sits above its ground datum in metre/Y-up coordinates`);
  }
});

test('landscape visibility hides and restores actual foliage descendants without hiding the river water', () => {
  const landscape = riverGroups.landscape.map(name => {
    const node = cadNodes.get(name);
    assert.ok(node, `Actual GLB contains ${name}`);
    return node;
  });
  const water = cadNodes.get('River:water');
  assert.ok(water);
  try {
    for (const [, crown] of crowns) assert.equal(isObjectVisible(crown), true);
    for (const node of landscape) node.visible = false;
    for (const [, crown] of crowns) assert.equal(isObjectVisible(crown), false);
    assert.equal(isObjectVisible(water), true);
    for (const node of landscape) node.visible = true;
    for (const [, crown] of crowns) assert.equal(isObjectVisible(crown), true);
  } finally {
    for (const node of landscape) node.visible = true;
  }
});
