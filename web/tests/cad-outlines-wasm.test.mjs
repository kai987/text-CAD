import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  BufferAttribute, BufferGeometry, Float32BufferAttribute, InterleavedBuffer,
  InterleavedBufferAttribute, Vector3,
} from 'three';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { createCadOutlineGeometry } from '../src/cad-outlines.ts';
import { createWasmCadOutlineGeometry, initializeSectionCapsWasm } from '../src/section-caps-wasm.ts';
import { cad_outline } from '../src/wasm/section_caps.js';

await initializeSectionCapsWasm(await readFile(new URL('../src/wasm/section_caps_bg.wasm', import.meta.url)));

const upper = [[0, 0, 0], [4, 0, 0], [0, 2, 0]];
const lower = [
  [[2, 0, 0], [0, 0, 0], [0, -2, 0]],
  [[4, 0, 0], [2, 0, 0], [4, -2, 0]],
];

function geometry(triangles, indexed = false) {
  const source = new BufferGeometry();
  source.setAttribute('position', new Float32BufferAttribute(triangles.flat(2), 3));
  if (indexed) source.setIndex(Array.from({ length: source.getAttribute('position').count }, (_, i) => i));
  return source;
}

function checkParity(source, threshold = 28, label = '') {
  const position = source.getAttribute('position');
  const original = position?.array?.slice();
  const reference = createCadOutlineGeometry(source, threshold);
  const actual = createWasmCadOutlineGeometry(source, threshold);
  try {
    const expected = reference.getAttribute('position').array;
    const result = actual.getAttribute('position').array;
    assert.equal(result.length, expected.length, `${label}: same segment count`);
    for (let i = 0; i < result.length; i++) {
      assert.ok(Number.isFinite(result[i]), `${label}: finite output at ${i}`);
      assert.ok(Math.abs(result[i] - expected[i]) <= 2e-6,
        `${label}: same endpoint order at ${i}: ${result[i]} versus ${expected[i]}`);
    }
    if (original) assert.deepEqual(position.array, original, `${label}: source arrays remain attached and unchanged`);
    return result.slice();
  } finally {
    actual.dispose(); reference.dispose();
  }
}

function covers(output, coordinates, tolerance = 1e-6) {
  const point = new Vector3(...coordinates);
  for (let i = 0; i < output.length; i += 6) {
    const a = new Vector3().fromArray(output, i), b = new Vector3().fromArray(output, i + 3);
    const delta = b.sub(a), t = point.clone().sub(a).dot(delta) / delta.lengthSq();
    if (t >= -tolerance && t <= 1 + tolerance &&
        a.addScaledVector(delta, t).distanceTo(point) <= tolerance) return true;
  }
  return false;
}

test('Rust outline removes split and partial coplanar seams, retaining actual borders', () => {
  for (const indexed of [false, true]) {
    const source = geometry([upper, ...lower], indexed);
    const result = checkParity(source, 28, `split indexed=${indexed}`);
    for (const x of [0.5, 1.5, 2.5, 3.5]) assert.equal(covers(result, [x, 0, 0]), false);
    assert.equal(covers(result, [0, 1, 0]), true);
    assert.equal(source.boundingBox, null);
    const partial = checkParity(geometry([upper, [[3, 0, 0], [1, 0, 0], [1, -2, 0]]], indexed));
    assert.equal(covers(partial, [0.5, 0, 0]), true);
    assert.equal(covers(partial, [2, 0, 0]), false);
    assert.equal(covers(partial, [3.5, 0, 0]), true);
  }
});

test('Rust outline preserves signed sharp creases, nonmanifold creases and custom thresholds', () => {
  const fold = geometry([upper, [[4, 0, 0], [0, 0, 0], [0, 0, 2]]]);
  for (const threshold of [0, 28, 89, 91, 180, NaN, Infinity]) checkParity(fold, threshold, `threshold=${threshold}`);
  assert.equal(covers(checkParity(fold, 28), [2, 0, 0]), true);
  assert.equal(covers(checkParity(fold, 91), [2, 0, 0]), false);
  assert.equal(covers(checkParity(geometry([upper, [...upper].reverse()])), [2, 0, 0]), true);
  assert.equal(covers(checkParity(geometry([
    upper, ...lower, [[4, 0, 0], [0, 0, 0], [0, 0, 2]],
  ])), [2, 0, 0]), true);
});

test('Rust tolerance preserves nearby distinct and angled edges at Float32 model precision', () => {
  for (const [left, right] of [[0.00002, 0.00002], [0.00001, 0.00003]]) {
    const result = checkParity(geometry([upper, [[3, right, 0], [1, left, 0], [1, -2, 0]]]));
    assert.equal(covers(result, [2, 0, 0], 1e-8), true);
    assert.equal(covers(result, [2, (left + right) / 2, 0], 1e-8), true);
  }
  for (const scale of [0.001, 1, 1000]) {
    const source = geometry([upper, ...lower].map(triangle => triangle.map(point => point.map(value => value * scale))));
    checkParity(source, 28, `scale=${scale}`);
  }
});

test('Rust duplicates, invalid triangles and incomplete tails preserve valid geometry', () => {
  const degenerate = [[0, 0, 0], [2, 0, 0], [4, 0, 0]];
  const invalid = [[NaN, 0, 0], [1, 0, 0], [2, 0, 0]];
  const result = checkParity(geometry([upper, upper, degenerate, invalid]));
  assert.equal(covers(result, [2, 0, 0]), true);
  checkParity(new BufferGeometry());
  const indexed = geometry([upper]);
  indexed.setIndex([0, 1, 2, 0, 100, 2]);
  assert.equal(covers(checkParity(indexed), [2, 0, 0]), true);
  for (const invalidIndex of [-1, 0.5, NaN, Infinity]) {
    indexed.setIndex(new BufferAttribute(new Float64Array([0, 1, 2, 0, invalidIndex, 2]), 1));
    checkParity(indexed, 28, `invalid index=${invalidIndex}`);
  }
  const trailing = geometry([upper]);
  trailing.setAttribute('position', new BufferAttribute(new Float64Array([...upper.flat(), 10]), 3));
  checkParity(trailing, 28, 'incomplete vertex tail');
  indexed.setIndex([]);
  assert.equal(checkParity(indexed).length, 0, 'empty explicit index remains empty');
  assert.equal(cad_outline(new Float64Array(), new Uint32Array([0, 1, 2]), 28).length, 0);
});

test('Rust wrapper handles interleaved attributes and invalidates cached position and index copies', () => {
  const source = geometry([upper, ...lower], true);
  const before = checkParity(source);
  const position = source.getAttribute('position');
  position.setY(3, 0.00002); position.needsUpdate = true;
  const after = checkParity(source);
  assert.notDeepEqual(after, before, 'position updates rebuild the cached numeric input');
  source.getIndex().setX(3, 0); source.getIndex().needsUpdate = true;
  checkParity(source, 28, 'index version update');
  source.setAttribute('position', new Float32BufferAttribute(upper.flat(), 3));
  source.setIndex([0, 1, 2]);
  checkParity(source, 28, 'attribute replacement');
  const values = new Float32Array([upper, ...lower].flat(1).flatMap(point => [99, ...point, 88]));
  const interleaved = new InterleavedBuffer(values, 5);
  const geometryWithStride = new BufferGeometry().setAttribute('position', new InterleavedBufferAttribute(interleaved, 3, 1));
  checkParity(geometryWithStride, 28, 'interleaved stride');
  geometryWithStride.getAttribute('position').setY(3, 0.00002); interleaved.needsUpdate = true;
  checkParity(geometryWithStride, 28, 'interleaved version update');
});

test('Rust and TypeScript outlines match the actual house, apartment, W/S/RC architectural meshes', async () => {
  let checks = 0;
  for (const filename of ['house_3d.glb', 'apartment_2ldk.glb', 'structure_W.glb', 'structure_S.glb', 'structure_RC.glb']) {
    const gltf = await loadGlbGeometry(new URL(`../../GLB/${filename}`, import.meta.url));
    gltf.scene.traverse(object => {
      if (!object.isMesh) return;
      const node = gltf.parser.associations.get(object)?.nodes;
      const name = gltf.parser.json.nodes[node]?.name ?? object.name;
      if (!/(?:wall_|cladding:|wall:|shear_wall:)/.test(name)) return;
      checkParity(object.geometry, 28, `${filename}:${name}`);
      checks++;
    });
  }
  assert.ok(checks > 50, `actual architectural mesh checks=${checks}`);
});
