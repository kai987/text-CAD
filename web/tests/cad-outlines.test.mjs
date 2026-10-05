import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { BufferGeometry, Float32BufferAttribute, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createCadOutlineGeometry } from '../src/cad-outlines.ts';

function geometry(triangles, indexed = false) {
  const result = new BufferGeometry();
  const points = triangles.flat(2);
  result.setAttribute('position', new Float32BufferAttribute(points, 3));
  if (indexed) result.setIndex(Array.from({ length: points.length / 3 }, (_, i) => i));
  return result;
}

function segments(outline, matrix) {
  const position = outline.getAttribute('position');
  return Array.from({ length: position.count / 2 }, (_, i) => [0, 1].map(j => {
    const point = new Vector3().fromBufferAttribute(position, i * 2 + j);
    return matrix ? point.applyMatrix4(matrix) : point;
  }));
}

function covers(lines, coordinates, tolerance = 1e-6) {
  const point = new Vector3(...coordinates);
  return lines.some(([a, b]) => {
    const direction = b.clone().sub(a);
    const offset = point.clone().sub(a);
    const t = offset.dot(direction) / direction.lengthSq();
    return t >= -tolerance && t <= 1 + tolerance &&
      a.clone().addScaledVector(direction, t).distanceTo(point) <= tolerance;
  });
}

const upper = [[0, 0, 0], [4, 0, 0], [0, 2, 0]];
const splitLower = [
  [[2, 0, 0], [0, 0, 0], [0, -2, 0]],
  [[4, 0, 0], [2, 0, 0], [4, -2, 0]],
];

test('coplanar T-junctions disappear for indexed and non-indexed geometry without changing the source', () => {
  for (const indexed of [false, true]) {
    const source = geometry([upper, ...splitLower], indexed);
    const original = source.getAttribute('position').array.slice();
    const lines = segments(createCadOutlineGeometry(source));
    for (const x of [0.5, 1.5, 2.5, 3.5]) assert.equal(covers(lines, [x, 0, 0]), false);
    assert.equal(covers(lines, [0, 1, 0]), true, 'outside perimeter stays visible');
    assert.equal(covers(lines, [2, 1, 0]), true, 'sloping outside perimeter stays visible');
    assert.deepEqual(source.getAttribute('position').array, original);
    assert.equal(source.boundingBox, null, 'source caches are not mutated');
  }
});

test('partial coplanar overlaps cancel only their shared interval', () => {
  const source = geometry([upper, [[3, 0, 0], [1, 0, 0], [1, -2, 0]]]);
  const lines = segments(createCadOutlineGeometry(source));
  assert.equal(covers(lines, [0.5, 0, 0]), true);
  assert.equal(covers(lines, [2, 0, 0]), false);
  assert.equal(covers(lines, [3.5, 0, 0]), true);
});

test('split sharp creases and opposite face normals stay visible', () => {
  const fold = geometry([upper,
    [[2, 0, 0], [0, 0, 0], [0, 0, 2]],
    [[4, 0, 0], [2, 0, 0], [4, 0, 2]],
  ]);
  const foldLines = segments(createCadOutlineGeometry(fold));
  for (const x of [0.5, 1.5, 2.5, 3.5]) assert.equal(covers(foldLines, [x, 0, 0]), true);
  const opposite = segments(createCadOutlineGeometry(geometry([upper, [...upper].reverse()])));
  assert.equal(covers(opposite, [2, 0, 0]), true, 'signed normal dot product preserves a 180 degree fold');
});

test('nearby parallel and slightly non-parallel borders do not merge', () => {
  // Smaller than Three EdgesGeometry's 1e-4 position hash, larger than the
  // Float32-scale tolerance used here: these remain two separate boundaries.
  const offset = 0.00002;
  const nearParallel = geometry([upper, [[3, offset, 0], [1, offset, 0], [1, -2, 0]]]);
  const parallelLines = segments(createCadOutlineGeometry(nearParallel));
  assert.equal(covers(parallelLines, [2, 0, 0], 1e-8), true);
  assert.equal(covers(parallelLines, [2, offset, 0], 1e-8), true);
  const angled = geometry([upper, [[3, 0.00003, 0], [1, 0.00001, 0], [1, -2, 0]]]);
  const angledLines = segments(createCadOutlineGeometry(angled));
  assert.equal(covers(angledLines, [2, 0, 0], 1e-8), true);
  assert.equal(covers(angledLines, [2, 0.00002, 0], 1e-8), true);
});

test('open borders survive duplicate and degenerate triangles; non-manifold creases stay visible', () => {
  const duplicate = segments(createCadOutlineGeometry(geometry([upper, upper, [[0, 0, 0], [2, 0, 0], [4, 0, 0]]])));
  assert.equal(covers(duplicate, [2, 0, 0]), true);
  const crease = segments(createCadOutlineGeometry(geometry([upper, ...splitLower,
    [[4, 0, 0], [0, 0, 0], [0, 0, 2]],
  ])));
  assert.equal(covers(crease, [2, 0, 0]), true);
  const empty = new BufferGeometry();
  assert.equal(createCadOutlineGeometry(empty).getAttribute('position').count, 0);
  const invalid = geometry([upper, [[NaN, 0, 0], [1, 0, 0], [2, 0, 0]]]);
  assert.equal(covers(segments(createCadOutlineGeometry(invalid)), [2, 0, 0]), true, 'invalid triangles do not consume a valid border');
});

test('outline intervals do not depend on triangle processing order', () => {
  const canonical = source => segments(createCadOutlineGeometry(source)).map(line => line
    .map(point => point.toArray().map(value => Math.round(value * 1e6)).join(','))
    .sort().join(':')).sort();
  assert.deepEqual(canonical(geometry([upper, ...splitLower])), canonical(geometry([...splitLower].reverse().concat([upper]))));
});

test('actual house windows retain heads, jambs and outer corners while both floor seams disappear', async () => {
  const bytes = await readFile(new URL('../../GLB/house_3d.glb', import.meta.url));
  const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
  gltf.scene.updateMatrixWorld(true);
  const walls = new Map();
  gltf.scene.traverse(object => {
    const node = gltf.parser.associations.get(object)?.nodes;
    const name = gltf.parser.json.nodes[node]?.name;
    if (name === 'F1:wall_external_east' || name === 'F2:wall_external_east') walls.set(name, object);
  });
  assert.equal(walls.size, 2);
  for (const [name, wall] of walls) {
    const base = name.startsWith('F2:') ? 2.8 : 0;
    const lines = segments(createCadOutlineGeometry(wall.geometry), wall.matrixWorld);
    for (const x of [7.28, 7.10]) {
      assert.equal(covers(lines, [x, base + 2.1, -4.0]), false, `${name}: no window-to-window seam`);
      assert.equal(covers(lines, [x, base + 2.1, -2.355]), true, `${name}: small window head retained`);
      assert.equal(covers(lines, [x, base + 2.1, -6.5]), true, `${name}: larger window head retained`);
      assert.equal(covers(lines, [x, base + 1.8, -2.13]), true, `${name}: window jamb retained`);
      assert.equal(covers(lines, [x, base + 1.2, -0.18]), true, `${name}: outer corner retained`);
      assert.equal(covers(lines, [x, base + 1.2, -7.10]), true, `${name}: opposite corner retained`);
    }
  }
});
