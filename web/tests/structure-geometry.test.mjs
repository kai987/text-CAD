import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { Box3, Vector3 } from 'three';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { bindCadNodes, selectionFor } from '../src/model-scene.ts';
import { createHorizontalCap } from '../src/section-caps.ts';
import { createWasmHorizontalCap, initializeSectionCapsWasm } from '../src/section-caps-wasm.ts';

const manifest = JSON.parse(await readFile(new URL('../../output/review/house_3d_assumptions_R01.json', import.meta.url), 'utf8'));
await initializeSectionCapsWasm(await readFile(new URL('../src/wasm/section_caps_bg.wasm', import.meta.url)));
const near = (actual, expected, tolerance = 2e-5) => assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} differs from ${expected}`);
async function house() {
  const gltf = await loadGlbGeometry(new URL('../../GLB/house_3d.glb', import.meta.url));
  gltf.scene.updateMatrixWorld(true);
  return bindCadNodes(gltf);
}
function inspect(mesh, geometry, height) {
  let area = 0;
  const bounds = new Box3(), triangles = [];
  const position = geometry.getAttribute('position');
  for (let i = 0; i < position.count; i += 3) {
    const triangle = [0, 1, 2].map(offset => new Vector3().fromBufferAttribute(position, i + offset).applyMatrix4(mesh.matrixWorld));
    for (const vertex of triangle) { near(vertex.y, height); bounds.expandByPoint(vertex); }
    const normal = new Vector3().subVectors(triangle[1], triangle[0]).cross(new Vector3().subVectors(triangle[2], triangle[0]));
    assert.ok(normal.y > 0, 'sections of thin members have nondegenerate upward faces');
    area += normal.y / 2; triangles.push(triangle);
  }
  return { area, bounds, triangles };
}

test('R06 saved structural scheme retains pending capacity and perimeter supports', async () => {
  assert.match(manifest.structure.status, /not_engineered/);
  assert.equal(manifest.structure.capacity_results, null);
  assert.equal(manifest.structure.statutory_compliance_result, null);
  const nodes = await house();
  const plinth = nodes.get('foundation:existing_plinth');
  assert.equal(plinth.children.length, 4);
  for (const mesh of plinth.children) {
    assert.equal(selectionFor(mesh).id, 'foundation:existing_plinth');
    const bounds = new Box3().setFromObject(mesh);
    near(bounds.min.y, -.5); near(bounds.max.y, -.2);
  }
});

test('thin bearing-wall candidates, joists and roof members preserve TS/WASM cap parity', async () => {
  const nodes = await house();
  const members = [...nodes].filter(([name, mesh]) => name.startsWith('structure:') && mesh.isMesh);
  assert.ok(members.length > 100, 'exercise all named structural proposal solids');
  let caps = 0;
  for (const [name, mesh] of members) {
    const bounds = new Box3().setFromObject(mesh);
    const heights = new Set([1.4, 4.2, 5.5, 6.9, bounds.min.y, bounds.max.y, (bounds.min.y + bounds.max.y) / 2]);
    for (const height of heights) {
      const ts = createHorizontalCap(mesh, height), wasm = createWasmHorizontalCap(mesh, height);
      try {
        assert.equal(ts === null, wasm === null, `${name} at ${height}: cap presence`);
        if (!ts) continue;
        const expected = inspect(mesh, ts, height), actual = inspect(mesh, wasm, height);
        near(actual.area, expected.area);
        for (const side of ['min', 'max']) for (const axis of ['x', 'y', 'z']) near(actual.bounds[side][axis], expected.bounds[side][axis]);
        caps++;
      } finally { ts?.dispose(); wasm?.dispose(); }
    }
  }
  assert.ok(caps > 100, 'real sections must include beams, columns, wall candidates and roof members');
});

test('the actual attic frame keeps the hatch void open in both section engines', async () => {
  const nodes = await house();
  const d = manifest.structure.dimensions, hatch = manifest.attic.hatch_bounds_mm;
  const height = (d.attic_joist_bottom_z + d.attic_joist_top_z) / 2000;
  const point = { x: (hatch[0] + hatch[3]) / 2000, z: -(hatch[1] + hatch[4]) / 2000 };
  const contains = triangle => {
    const signed = triangle.map((a, i) => {
      const b = triangle[(i + 1) % 3];
      return (b.x - a.x) * (point.z - a.z) - (b.z - a.z) * (point.x - a.x);
    });
    return signed.every(value => value <= 1e-9);
  };
  for (const create of [createHorizontalCap, createWasmHorizontalCap]) {
    let count = 0;
    for (const group of ['structure:attic_joists', 'structure:attic_headers']) {
      for (const mesh of nodes.get(group).children) {
        const cap = create(mesh, height);
        if (!cap) continue;
        try {
          const section = inspect(mesh, cap, height);
          assert.ok(section.triangles.every(triangle => !contains(triangle)), 'members and caps do not fill the clear hatch');
          count++;
        } finally { cap.dispose(); }
      }
    }
    assert.ok(count > 10, 'actual joist and header solids are intersected');
  }
});
