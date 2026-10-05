import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  Box3, BoxGeometry, BufferGeometry, ExtrudeGeometry, Float32BufferAttribute,
  InterleavedBuffer, InterleavedBufferAttribute, Matrix3, Mesh, Path, PlaneGeometry, Shape, Vector3,
} from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { bindCadNodes } from '../src/model-scene.ts';
import { createHorizontalCap } from '../src/section-caps.ts';
import { createWasmHorizontalCap, initializeSectionCapsWasm } from '../src/section-caps-wasm.ts';

// Initialize the same generated WASM that Vite serves, without browser fetch.
await initializeSectionCapsWasm(await readFile(new URL('../src/wasm/section_caps_bg.wasm', import.meta.url)));

const tolerance = 2e-5; // 0.02 mm; both wrappers return Float32 local coordinates.
const near = (actual, expected, limit = tolerance, message = '') => assert.ok(
  Math.abs(actual - expected) <= limit,
  `${message}: ${actual} differs from ${expected} by more than ${limit}`,
);

function inspect(mesh, geometry, height, name) {
  const positions = geometry.getAttribute('position'), normals = geometry.getAttribute('normal');
  assert.equal(positions.count % 3, 0, `${name}: triangles must be complete`);
  assert.equal(normals.count, positions.count, `${name}: every vertex needs a normal`);
  const normalMatrix = new Matrix3().getNormalMatrix(mesh.matrixWorld);
  const bounds = new Box3(), triangles = [];
  let area = 0;
  for (let i = 0; i < positions.count; i += 3) {
    const triangle = [0, 1, 2].map(offset => new Vector3()
      .fromBufferAttribute(positions, i + offset).applyMatrix4(mesh.matrixWorld));
    for (let offset = 0; offset < 3; offset++) {
      const vertex = triangle[offset];
      assert.ok([vertex.x, vertex.y, vertex.z].every(Number.isFinite), `${name}: finite positions`);
      near(vertex.y, height, tolerance, `${name}: world plane`);
      bounds.expandByPoint(vertex);
      const normal = new Vector3().fromBufferAttribute(normals, i + offset)
        .applyMatrix3(normalMatrix).normalize();
      near(normal.x, 0, 1e-6, `${name}: normal X`);
      near(normal.y, 1, 1e-6, `${name}: upward normal`);
      near(normal.z, 0, 1e-6, `${name}: normal Z`);
    }
    const cross = new Vector3().subVectors(triangle[1], triangle[0])
      .cross(new Vector3().subVectors(triangle[2], triangle[0]));
    assert.ok(cross.y > 0, `${name}: upward, nondegenerate triangle winding`);
    area += cross.y / 2;
    triangles.push(triangle);
  }
  return { area, bounds, triangles };
}

function contains(triangle, point) {
  const [a, b, c] = triangle;
  const cross = (p, q) => (q.x - p.x) * (point.z - p.z) - (q.z - p.z) * (point.x - p.x);
  const values = [cross(a, b), cross(b, c), cross(c, a)];
  // World X/Z triangles have negative signed area because their normal is +Y.
  return values.every(value => value <= 1e-8);
}

function covered(triangles, point) {
  return triangles.some(triangle => contains(triangle, point));
}

function checkParity(mesh, height, name) {
  const reference = createHorizontalCap(mesh, height), actual = createWasmHorizontalCap(mesh, height);
  try {
    assert.equal(actual === null, reference === null, `${name} at ${height}: cap/null parity`);
    if (!reference) return null;
    const expected = inspect(mesh, reference, height, `${name} TS`);
    const result = inspect(mesh, actual, height, `${name} WASM`);
    near(result.area, expected.area, Math.max(tolerance, expected.area * 1e-5), `${name}: area`);
    for (const side of ['min', 'max']) for (const axis of ['x', 'y', 'z']) {
      near(result.bounds[side][axis], expected.bounds[side][axis], tolerance, `${name}: ${side}.${axis}`);
    }
    // Triangulation may differ; compare its occupied region in both directions.
    for (const [source, target] of [[expected, result], [result, expected]]) {
      for (const triangle of source.triangles) {
        const center = triangle.reduce((sum, point) => sum.add(point), new Vector3()).divideScalar(3);
        assert.ok(covered(target.triangles, center), `${name}: corresponding triangle centroid coverage`);
      }
    }
    return result;
  } finally {
    reference?.dispose(); actual?.dispose();
  }
}

async function house() {
  const bytes = await readFile(new URL('../../GLB/house_3d.glb', import.meta.url));
  const gltf = await new GLTFLoader().parseAsync(
    bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '',
  );
  const bounds = new Box3().setFromObject(gltf.scene), center = bounds.getCenter(new Vector3());
  const offset = -bounds.min.y;
  gltf.scene.position.set(-center.x, offset, -center.z); gltf.scene.updateMatrixWorld(true);
  return { nodes: bindCadNodes(gltf), scene: gltf.scene, offset };
}

test('WASM matches all actual CAD meshes at practical heights and exact vertex levels', async () => {
  const { nodes, offset } = await house();
  const meshes = [...nodes].filter(([, object]) => object.isMesh);
  assert.ok(meshes.length > 100, 'the full named house must be used');
  let capped = 0, checks = 0;
  for (const [name, mesh] of meshes) {
    const heights = new Set([1.2, 2.7, 4.2, 5.6].map(height => height + offset));
    const positions = mesh.geometry.getAttribute('position');
    for (let i = 0; i < positions.count; i++) {
      heights.add(new Vector3().fromBufferAttribute(positions, i).applyMatrix4(mesh.matrixWorld).y);
    }
    for (const height of heights) {
      if (checkParity(mesh, height, name)) capped++;
      checks++;
    }
  }
  assert.ok(capped > 50, 'comparisons must include actual nonempty sections');
  assert.ok(checks > meshes.length * 4, 'comparisons must include exact vertex heights');
});

test('WASM cabinet caps and slab stair opening retain their actual areas and hole coverage', async () => {
  const { nodes, offset } = await house();
  const cabinets = [...nodes].filter(([name, object]) => /^F2:storage_\d+$/.test(name) && object.isMesh);
  assert.equal(cabinets.length, 4);
  for (const [name, mesh] of cabinets) {
    const cap = checkParity(mesh, 4.2 + offset, name);
    assert.ok(cap);
    const bounds = new Box3().setFromObject(mesh);
    near(cap.area, (bounds.max.x - bounds.min.x) * (bounds.max.z - bounds.min.z));
  }
  const mesh = nodes.get('F2:floor_slab'), height = 2.7 + offset;
  const cap = checkParity(mesh, height, 'F2:floor_slab');
  assert.ok(cap);
  near(cap.area, 7.28 * 7.28 - 1.9 * 2.72, 5e-5, 'slab minus stair opening');
});

test('WASM preserves nested holes and disconnected solid islands', () => {
  const ring = new Shape().moveTo(0, 0).lineTo(4, 0).lineTo(4, 3).lineTo(0, 3).closePath();
  ring.holes.push(new Path().moveTo(1, 1).lineTo(1, 2).lineTo(3, 2).lineTo(3, 1).closePath());
  const island = new Shape().moveTo(1.5, 1.25).lineTo(2.5, 1.25)
    .lineTo(2.5, 1.75).lineTo(1.5, 1.75).closePath();
  const mesh = new Mesh(new ExtrudeGeometry([ring, island], { depth: 2, bevelEnabled: false }));
  mesh.rotation.x = -Math.PI / 2;
  try {
    const cap = checkParity(mesh, 1, 'ring with island');
    assert.ok(cap); near(cap.area, 12 - 2 + 0.5);
    assert.equal(covered(cap.triangles, new Vector3(1.2, 1, -1.5)), false, 'empty hole remains empty');
    assert.equal(covered(cap.triangles, new Vector3(2, 1, -1.5)), true, 'nested island remains solid');
    assert.equal(covered(cap.triangles, new Vector3(0.5, 1, -1.5)), true, 'outer ring remains solid');
  } finally { mesh.geometry.dispose(); }
});

test('WASM respects translated, rotated, nonuniform and reflected world transforms', () => {
  for (const scaleX of [1.4, -1.4]) {
    const mesh = new Mesh(new BoxGeometry(2, 2, 2));
    mesh.position.set(4, 3, -2); mesh.rotation.set(0.3, 0.2, 0.4); mesh.scale.set(scaleX, 0.8, 1.1);
    try { assert.ok(checkParity(mesh, 3, `transformed box scale ${scaleX}`)); }
    finally { mesh.geometry.dispose(); }
  }
  const vertexMesh = new Mesh(new BoxGeometry(2, 2, 2));
  vertexMesh.rotation.z = Math.PI / 4;
  try {
    const cap = checkParity(vertexMesh, 0, 'rotated box exact vertex level');
    assert.ok(cap); near(cap.area, 4 * Math.sqrt(2), 4e-5);
  } finally { vertexMesh.geometry.dispose(); }
});

test('WASM supports non-indexed geometry and invalidates packed positions when an attribute changes', () => {
  const source = new BoxGeometry(2, 2, 2), mesh = new Mesh(source.toNonIndexed());
  source.dispose();
  try {
    const before = checkParity(mesh, 0, 'non-indexed box');
    assert.ok(before); near(before.area, 4);
    // BufferGeometry.scale increments position.version via needsUpdate. A cached
    // packed WASM input must observe the edit rather than keep the initial box.
    mesh.geometry.scale(1.5, 1, 0.75);
    const after = checkParity(mesh, 0, 'edited non-indexed box');
    assert.ok(after); near(after.area, 4.5);
  } finally { mesh.geometry.dispose(); }
});

test('WASM supports interleaved positions and observes their underlying buffer version', () => {
  const geometry = new BoxGeometry(2, 2, 2), original = geometry.getAttribute('position');
  const data = new Float32Array(original.count * 4);
  for (let i = 0; i < original.count; i++) {
    data.set([123, original.getX(i), original.getY(i), original.getZ(i)], i * 4);
  }
  geometry.setAttribute('position', new InterleavedBufferAttribute(new InterleavedBuffer(data, 4), 3, 1));
  const mesh = new Mesh(geometry);
  try {
    const before = checkParity(mesh, 0, 'interleaved box');
    assert.ok(before); near(before.area, 4);
    geometry.scale(1.5, 1, 0.5);
    const after = checkParity(mesh, 0, 'edited interleaved box');
    assert.ok(after); near(after.area, 3);
  } finally { geometry.dispose(); }
});

test('WASM does not invent caps at tangencies, invalid heights, empty, open or singular meshes', () => {
  const mesh = new Mesh(new BoxGeometry(2, 2, 2));
  const plane = new Mesh(new PlaneGeometry(2, 2)), empty = new Mesh(new BufferGeometry());
  try {
    for (const height of [-2, -1, 1, 2, NaN, Infinity, -Infinity]) {
      assert.equal(checkParity(mesh, height, 'invalid or tangent box section'), null);
    }
    assert.ok(checkParity(mesh, 0, 'box middle section'));
    assert.equal(checkParity(plane, 0, 'open plane'), null);
    assert.equal(checkParity(empty, 0, 'empty mesh'), null);
    mesh.scale.y = 0;
    assert.equal(checkParity(mesh, 0, 'singular mesh'), null);
  } finally { mesh.geometry.dispose(); plane.geometry.dispose(); empty.geometry.dispose(); }
});

test('WASM rejects nonfinite mesh coordinates without producing invalid output', () => {
  const mesh = new Mesh(new BoxGeometry(2, 2, 2));
  const positions = mesh.geometry.getAttribute('position');
  for (let i = 0; i < positions.count; i++) positions.setY(i, NaN);
  positions.needsUpdate = true;
  try { assert.equal(checkParity(mesh, 0, 'nonfinite positions'), null); }
  finally { mesh.geometry.dispose(); }
});

test('WASM rejects malformed indices before integer coercion can hide an invalid value', () => {
  const geometry = new BoxGeometry(2, 2, 2), mesh = new Mesh(geometry);
  const original = Array.from(geometry.index.array);
  assert.equal(original[0], 0, 'fractional first index must otherwise truncate to the original index');
  try {
    for (const value of [0.5, -0.5, -1, geometry.getAttribute('position').count, NaN]) {
      const index = new Float32BufferAttribute(original, 1);
      index.setX(0, value); geometry.setIndex(index);
      // The original TS function assumes a well-formed index and can throw;
      // this assertion is a WASM adapter safety contract rather than oracle parity.
      assert.equal(createWasmHorizontalCap(mesh, 0), null, `invalid index ${value} must be rejected`);
    }
  } finally { geometry.dispose(); }
});
