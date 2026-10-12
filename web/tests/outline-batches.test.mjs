import test from 'node:test';
import assert from 'node:assert/strict';
import {
  BoxGeometry, BufferGeometry, EdgesGeometry, Float32BufferAttribute, Group,
  LineBasicMaterial, LineSegments, Matrix4, Mesh, MeshBasicMaterial, Scene, Vector3,
} from 'three';
import { createOutlineBatches } from '../src/outline-batches.ts';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';

function outline(points = [0, 0, 0, 1, 0, 0]) {
  return new BufferGeometry().setAttribute('position', new Float32BufferAttribute(points, 3));
}
function manager(scene = new Scene()) {
  const standard = new LineBasicMaterial({ color: '#35465a', transparent: true, opacity: 0.55 });
  const detail = new LineBasicMaterial({ color: '#35465a', transparent: true, opacity: 0.16 });
  return { scene, materials: { standard, detail }, batches: createOutlineBatches(scene, { standard, detail }) };
}
function mesh(parent, name = 'component') {
  const solid = new Mesh(new BoxGeometry(), new MeshBasicMaterial());
  solid.userData.cadName = name;
  parent.add(solid);
  return solid;
}
function linesFor(batches, style) {
  return batches.root.children.find(line => line.name === `__cad_outline_${style}`);
}
function worldPoints(geometry, transform = new Matrix4()) {
  const points = geometry.getAttribute('position');
  const index = geometry.getIndex();
  const start = geometry.drawRange.start;
  const count = Math.floor(Math.min((index?.count ?? points.count) - start, geometry.drawRange.count) / 2) * 2;
  const result = [];
  for (let i = start; i < start + count; i++) {
    result.push(...new Vector3().fromBufferAttribute(points, index ? index.getX(i) : i).applyMatrix4(transform).toArray());
  }
  return result;
}
function close(actual, expected, tolerance = 1e-5) {
  assert.equal(actual.length, expected.length);
  actual.forEach((value, index) => assert.ok(Math.abs(value - expected[index]) <= tolerance, `${index}: ${value} versus ${expected[index]}`));
}

test('two styles retain every endpoint, draw range, nested transform and duplicate segment without changing pickable meshes', () => {
  const { scene, materials, batches } = manager();
  scene.position.set(3, -2, 4);
  const floor = new Group(); scene.add(floor);
  floor.position.set(2, 3, 1); floor.rotation.y = 0.4; floor.scale.set(-2, 1.5, 0.7);
  const cabinet = mesh(floor, 'F1:furniture:cabinet');
  const wall = mesh(floor, 'F1:wall_partition'); wall.rotation.z = 0.2;
  const cabinetLines = outline([0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0]);
  const wallLines = outline([0, 0, 0, 1, 0, 0, 0, 2, 0, 1, 2, 0]);
  wallLines.setIndex([2, 3, 0, 1]); wallLines.setDrawRange(0, 2);
  const originalCabinetMaterial = cabinet.material;
  const originalPosition = cabinetLines.getAttribute('position').array.slice();
  batches.set(cabinet, cabinetLines, 'detail'); batches.set(wall, wallLines, 'standard');
  const stats = batches.update();
  assert.deepEqual(stats, { registeredMeshes: 2, visibleMeshes: 2, segments: 3, drawCalls: 2, rebuilds: 1 });
  for (const [style, solid, source] of [['detail', cabinet, cabinetLines], ['standard', wall, wallLines]]) {
    const line = linesFor(batches, style);
    assert.ok(line instanceof LineSegments);
    close(worldPoints(line.geometry, line.matrixWorld), worldPoints(source, solid.matrixWorld));
    assert.equal(line.material, materials[style]);
    assert.equal(line.renderOrder, 0); assert.equal(line.frustumCulled, true);
    assert.equal(line.material.depthTest, true); assert.equal(line.material.depthWrite, true);
    assert.equal(line.material.clippingPlanes, null, 'global renderer clipping remains available');
  }
  assert.equal(cabinet.userData.cadName, 'F1:furniture:cabinet');
  assert.equal(cabinet.material, originalCabinetMaterial);
  assert.equal(cabinet.parent, floor);
  assert.deepEqual(cabinet.children, [], 'selection and picking continue to operate on original solids');
  assert.deepEqual(cabinetLines.getAttribute('position').array, originalPosition);
  batches.dispose();
});

test('visibility inherits all parents and unchanged selection/palette/camera state does not rebuild buffers', () => {
  const { scene, materials, batches } = manager();
  const floor = new Group(), part = new Group(); scene.add(floor); floor.add(part);
  const a = mesh(part), b = mesh(floor);
  batches.set(a, outline()); batches.set(b, outline(), 'detail');
  batches.update();
  const standardGeometry = linesFor(batches, 'standard').geometry;
  a.material = a.material.clone(); a.material.color.set('#e7aa37');
  materials.standard.color.set('#ffffff'); materials.standard.opacity *= 0.48;
  assert.equal(batches.update().rebuilds, 1);
  assert.equal(linesFor(batches, 'standard').geometry, standardGeometry);
  part.visible = false;
  assert.equal(batches.update().visibleMeshes, 1);
  assert.equal(linesFor(batches, 'standard').visible, false);
  floor.visible = false;
  assert.deepEqual(batches.update(), { registeredMeshes: 2, visibleMeshes: 0, segments: 0, drawCalls: 0, rebuilds: 3 });
  floor.visible = true; part.visible = true; b.visible = false;
  assert.equal(batches.update().visibleMeshes, 1);
  assert.equal(linesFor(batches, 'standard').visible, true);
  assert.equal(linesFor(batches, 'detail').visible, false);
  batches.dispose();
});

test('late outlines, moved solids, section caps and structural overlays update only on explicit state changes', () => {
  const { scene, batches } = manager();
  const base = new Group(), variant = new Group(); scene.add(base, variant);
  const foundation = mesh(base), frame = mesh(variant);
  const cap = mesh(foundation, 'foundation_section_cap');
  variant.visible = false;
  batches.set(foundation, outline()); batches.set(frame, outline([0, 0, 0, 0, 2, 0])); batches.set(cap, outline());
  assert.equal(batches.update().visibleMeshes, 2);
  foundation.position.y = 2;
  const oldGeometry = linesFor(batches, 'standard').geometry;
  assert.equal(batches.update().rebuilds, 2);
  assert.notEqual(linesFor(batches, 'standard').geometry, oldGeometry);
  assert.equal(linesFor(batches, 'standard').geometry.getAttribute('position').getY(0), 2);
  batches.remove(cap); foundation.remove(cap);
  assert.equal(batches.update().visibleMeshes, 1);
  base.visible = false; variant.visible = true;
  assert.equal(batches.update().visibleMeshes, 1);
  assert.equal(linesFor(batches, 'standard').geometry.getAttribute('position').getY(1), 2);
  batches.set(frame, outline([0, 0, 0, 0, 3, 0]));
  assert.equal(batches.update().rebuilds, 5);
  assert.equal(linesFor(batches, 'standard').geometry.getAttribute('position').getY(1), 3);
  batches.dispose();
});

test('an asynchronous standard outline update preserves the unrelated furniture GPU buffer', () => {
  const { scene, batches } = manager();
  const wall = mesh(scene), furniture = mesh(scene);
  batches.set(furniture, outline(), 'detail'); batches.update();
  const furnitureBuffer = linesFor(batches, 'detail').geometry;
  batches.set(wall, outline(), 'standard'); batches.update();
  assert.equal(linesFor(batches, 'detail').geometry, furnitureBuffer);
  batches.remove(wall); batches.update();
  assert.equal(linesFor(batches, 'detail').geometry, furnitureBuffer);
  assert.equal(batches.stats().drawCalls, 1);
  batches.dispose();
});

test('changed attributes and shared outline ownership release replacements exactly once', () => {
  const { scene, materials, batches } = manager();
  const a = mesh(scene), b = mesh(scene);
  const shared = outline(); let sharedDisposals = 0;
  shared.addEventListener('dispose', () => sharedDisposals++);
  batches.set(a, shared); batches.set(b, shared); batches.update();
  shared.getAttribute('position').setX(1, 4); shared.getAttribute('position').needsUpdate = true;
  assert.equal(batches.update().rebuilds, 2);
  assert.equal(linesFor(batches, 'standard').geometry.getAttribute('position').getX(1), 4);
  batches.set(a, outline()); assert.equal(sharedDisposals, 0);
  batches.remove(b); assert.equal(sharedDisposals, 1);
  let materialDisposals = 0;
  Object.values(materials).forEach(material => material.addEventListener('dispose', () => materialDisposals++));
  batches.dispose(); batches.dispose();
  assert.equal(materialDisposals, 2); assert.equal(sharedDisposals, 1);
  assert.equal(batches.root.parent, null);
  assert.equal(a.parent, scene, 'disposing display batches does not remove source solids');
  const late = outline(); let lateDisposals = 0;
  late.addEventListener('dispose', () => lateDisposals++);
  batches.set(a, late); assert.equal(lateDisposals, 1, 'late worker results cannot retain disposed buffers');
});

test('same-color alpha blending is order-independent when line fragments pass the same depth test', () => {
  const blend = (background, alpha) => background.map((channel, i) => [0.2, 0.3, 0.4][i] * alpha + channel * (1 - alpha));
  close(blend(blend([0.9, 0.8, 0.7], 0.55), 0.16), blend(blend([0.9, 0.8, 0.7], 0.16), 0.55), 1e-12);
  // This verifies overlapping same-depth lines; differently ordered depth-writing
  // transparent objects still require a rendered visual comparison in the viewer.
});

test('actual house conventional edges keep every vertex in at most two display draws', async () => {
  const gltf = await loadGlbGeometry(new URL('../../GLB/house_3d.glb', import.meta.url));
  const { scene, batches } = manager(); scene.add(gltf.scene);
  scene.updateWorldMatrix(true, true);
  let count = 0, visibleCount = 0, vertices = 0;
  const expected = { standard: [], detail: [] };
  gltf.scene.traverse(object => {
    if (!(object instanceof Mesh)) return;
    const nodeIndex = gltf.parser.associations.get(object)?.nodes;
    const name = gltf.parser.json.nodes[nodeIndex]?.name ?? '';
    if (/:wall_(?:external|partition)_|^roof:.*gable_wall$|:cladding:/.test(name)) return;
    const geometry = new EdgesGeometry(object.geometry, 28);
    count++; vertices += geometry.getAttribute('position').count;
    if (geometry.getAttribute('position').count) visibleCount++;
    const style = /:furniture:|:fixture_/.test(name) ? 'detail' : 'standard';
    expected[style].push(...worldPoints(geometry, object.matrixWorld));
    batches.set(object, geometry, style);
  });
  const stats = batches.update();
  assert.ok(count > 1000, 'exercise the real many-component house');
  assert.equal(stats.registeredMeshes, count);
  assert.equal(stats.visibleMeshes, visibleCount);
  assert.equal(stats.segments * 2, vertices, 'every original edge endpoint is preserved, including duplicates');
  assert.equal(stats.drawCalls, 2);
  for (const style of ['standard', 'detail']) close(worldPoints(linesFor(batches, style).geometry), expected[style]);
  assert.equal(batches.update().rebuilds, 1, 'rendering/orbiting needs no fresh concatenation');
  batches.dispose();
});
