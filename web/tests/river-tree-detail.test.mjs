import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { BufferGeometry, Float32BufferAttribute, Mesh, OrthographicCamera, Raycaster, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { bindCadNodes, isObjectVisible } from '../src/model-scene.ts';
import { chooseTreeDetail, createCrownProxy, createRiverTreeDetail } from '../src/river-tree-detail.ts';

let gltf, nodes, crowns;
const hash = array => createHash('sha256').update(Buffer.from(array.buffer, array.byteOffset, array.byteLength)).digest('hex');
before(async () => {
  const bytes = await readFile(new URL('../../GLB/river_demo.glb', import.meta.url));
  gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
  nodes = bindCadNodes(gltf); gltf.scene.updateMatrixWorld(true);
  crowns = [...nodes].filter(([name, node]) => node instanceof Mesh && name.startsWith('Landscape:trees:') && name.endsWith(':crown'));
});
after(() => {
  const geometries = new Set(), materials = new Set();
  gltf?.scene.traverse(node => {
    if (!(node instanceof Mesh)) return;
    geometries.add(node.geometry);
    for (const m of Array.isArray(node.material) ? node.material : [node.material]) materials.add(m);
  });
  geometries.forEach(g => g.dispose()); materials.forEach(m => m.dispose());
});
function camera() {
  const value = new OrthographicCamera(-100, 100, 100, -100, .1, 2000);
  value.position.set(180, 180, 220); value.lookAt(0, 0, 0); value.updateMatrixWorld(); return value;
}

test('actual crown proxies preserve bounds, colors and CAD identity with at least 70% fewer crown triangles', t => {
  const originals = new Map(crowns.map(([name, mesh]) => [name, { geometry: mesh.geometry, material: mesh.material, parent: mesh.parent,
    positionHash: hash(mesh.geometry.getAttribute('position').array), indexHash: hash(mesh.geometry.index.array) }]));
  const water = nodes.get('River:water'), waterGeometry = water.geometry;
  const detail = createRiverTreeDetail(gltf.scene); t.after(() => detail.dispose());
  assert.equal(detail.stats().crowns, 14);
  assert.equal(detail.update(camera(), 800, 80), true);
  const stats = detail.stats(); assert.equal(stats.coarse, 14); assert.ok(stats.triangles < stats.fullTriangles * .3);
  for (const [name, mesh] of crowns) {
    const original = originals.get(name), proxy = mesh.geometry;
    assert.notEqual(proxy, original.geometry); assert.equal(mesh.material, original.material); assert.equal(mesh.parent, original.parent);
    assert.equal(mesh.userData.cadName, name);
    assert.equal(hash(original.geometry.getAttribute('position').array), original.positionHash);
    assert.equal(hash(original.geometry.index.array), original.indexHash);
    for (const axis of ['x', 'y', 'z']) {
      assert.ok(Math.abs(proxy.boundingBox.min[axis] - original.geometry.boundingBox.min[axis]) < 1e-5, `${name} minimum ${axis}`);
      assert.ok(Math.abs(proxy.boundingBox.max[axis] - original.geometry.boundingBox.max[axis]) < 1e-5, `${name} maximum ${axis}`);
    }
    const p = proxy.getAttribute('position'), c = proxy.getAttribute('color'), n = proxy.getAttribute('normal');
    assert.equal(c.count, p.count); assert.equal(n.count, p.count);
    assert.ok([...p.array, ...c.array, ...n.array].every(Number.isFinite));
    assert.ok(Math.max(...c.array) - Math.min(...c.array) > .1, `${name} retains foliage color variation`);
    for (let i = 0; i < n.count; i++) assert.ok(Math.abs(Math.hypot(n.getX(i), n.getY(i), n.getZ(i)) - 1) < 1e-5);
  }
  assert.equal(water.geometry, waterGeometry, 'water is outside foliage LOD');
});

test('orthographic zoom restores original leaves; camera distance and unchanged views do not switch LOD', t => {
  const originals = crowns.map(([, mesh]) => mesh.geometry), detail = createRiverTreeDetail(gltf.scene), view = camera();
  t.after(() => detail.dispose());
  detail.update(view, 800, 80); assert.equal(detail.stats().coarse, 14);
  view.position.multiplyScalar(2); view.updateMatrixWorld();
  assert.equal(detail.update(view, 800, 80), false, 'orthographic camera distance is not apparent size');
  view.zoom = 12; view.updateProjectionMatrix();
  assert.equal(detail.update(view, 800, 80), true); assert.equal(detail.stats().detailed, 14);
  crowns.forEach(([, mesh], i) => assert.equal(mesh.geometry, originals[i]));
  assert.equal(detail.update(view, 800, 80), false);
  view.zoom = 1; detail.update(view, 800, 80);
  assert.equal(detail.update(view, 800, 0), true, 'detailed quality always uses original leaf geometry');
  assert.equal(detail.stats().detailed, 14);
});

test('threshold hysteresis prevents rapid geometry and shadow changes during zoom damping', () => {
  for (const pixels of [75, 81, 79, 89, 74]) {
    assert.equal(chooseTreeDetail('coarse', pixels, 80), 'coarse');
    assert.equal(chooseTreeDetail('detailed', pixels, 80), 'detailed');
  }
  assert.equal(chooseTreeDetail('coarse', 93, 80), 'detailed');
  assert.equal(chooseTreeDetail('detailed', 67, 80), 'coarse');
  assert.equal(chooseTreeDetail('coarse', 1, 0), 'detailed');
});

test('the displayed coarse crown remains ray-selectable and follows ancestor visibility', t => {
  const detail = createRiverTreeDetail(gltf.scene); t.after(() => detail.dispose());
  detail.update(camera(), 800, 80);
  const [name, mesh] = crowns[0], p = mesh.geometry.getAttribute('position');
  const a = new Vector3().fromBufferAttribute(p, mesh.geometry.index.getX(0)).applyMatrix4(mesh.matrixWorld);
  const b = new Vector3().fromBufferAttribute(p, mesh.geometry.index.getX(1)).applyMatrix4(mesh.matrixWorld);
  const c = new Vector3().fromBufferAttribute(p, mesh.geometry.index.getX(2)).applyMatrix4(mesh.matrixWorld);
  const center = a.clone().add(b).add(c).divideScalar(3);
  const normal = b.clone().sub(a).cross(c.clone().sub(a)).normalize();
  const ray = new Raycaster(center.clone().addScaledVector(normal, .1), normal.negate());
  const hit = ray.intersectObject(mesh, false)[0];
  assert.ok(hit); assert.equal(hit.object, mesh); assert.equal(hit.object.userData.cadName, name);
  const landscape = nodes.get('Landscape:trees');
  landscape.visible = false; assert.equal(isObjectVisible(hit.object), false);
  landscape.visible = true; assert.equal(isObjectVisible(hit.object), true);
});

test('LOD cleanup restores originals and disposes only owned proxies exactly once', () => {
  const originals = crowns.map(([, mesh]) => mesh.geometry), detail = createRiverTreeDetail(gltf.scene);
  detail.update(camera(), 800, 80);
  let proxyDisposals = 0, fullDisposals = 0;
  crowns.forEach(([, mesh]) => mesh.geometry.addEventListener('dispose', () => proxyDisposals++));
  const onFullDispose = () => fullDisposals++;
  originals.forEach(geometry => geometry.addEventListener('dispose', onFullDispose));
  detail.dispose(); detail.dispose();
  assert.equal(proxyDisposals, 14); assert.equal(fullDisposals, 0);
  crowns.forEach(([, mesh], i) => assert.equal(mesh.geometry, originals[i]));
  originals.forEach(geometry => geometry.removeEventListener('dispose', onFullDispose));
});

test('small or uncolored input is left as original detail rather than becoming an incomplete crown', () => {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute([0, 0, 0, 1, 0, 0, 0, 1, 0], 3));
  assert.equal(createCrownProxy(geometry), null);
  geometry.setAttribute('color', new Float32BufferAttribute([1, 0, 0, 0, 1, 0, 0, 0, 1], 3));
  assert.equal(createCrownProxy(geometry), null); geometry.dispose();
});

test('coarse geometry retains whole leaf patches and their original attributes', () => {
  const geometry = new BufferGeometry(), positions = [], normals = [], colors = [], indices = [];
  for (let leaf = 0; leaf < 32; leaf++) {
    for (let vertex = 0; vertex < 4; vertex++) {
      positions.push(leaf * 4 + vertex, vertex % 2, leaf % 3);
      normals.push(0, 1, 0); colors.push(leaf / 32, vertex / 4, .4);
    }
    indices.push(leaf * 4, leaf * 4 + 1, leaf * 4 + 2, leaf * 4, leaf * 4 + 2, leaf * 4 + 3);
  }
  geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new Float32BufferAttribute(normals, 3));
  geometry.setAttribute('color', new Float32BufferAttribute(colors, 3)); geometry.setIndex(indices);
  const proxy = createCrownProxy(geometry); assert.ok(proxy);
  const selected = new Map(), p = proxy.getAttribute('position'), c = proxy.getAttribute('color');
  for (let i = 0; i < p.count; i++) {
    const oldVertex = p.getX(i), leaf = Math.floor(oldVertex / 4);
    selected.set(leaf, (selected.get(leaf) ?? 0) + 1);
    assert.equal(c.getX(i), geometry.getAttribute('color').getX(oldVertex));
    assert.equal(c.getY(i), geometry.getAttribute('color').getY(oldVertex));
  }
  assert.ok(selected.size > 1 && selected.size < 16);
  for (const count of selected.values()) assert.equal(count, 4, 'all four vertices of a retained leaf survive');
  assert.equal(proxy.index.count, selected.size * 6, 'both original triangles survive together');
  geometry.dispose(); proxy.dispose();
});
