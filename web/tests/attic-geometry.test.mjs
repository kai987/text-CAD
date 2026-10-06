import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { Box3, Matrix3, Vector3 } from 'three';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { bindCadNodes, centerModelAtFloorDatum } from '../src/model-scene.ts';
import { createHorizontalCap } from '../src/section-caps.ts';
import { createWasmHorizontalCap, initializeSectionCapsWasm } from '../src/section-caps-wasm.ts';

const manifest = JSON.parse(await readFile(new URL('../../output/review/house_3d_assumptions_R01.json', import.meta.url), 'utf8'));
const attic = manifest.attic;
assert.ok(attic, 'saved house metadata records the attic proposal');
const a = attic.parameters, p = manifest.plan_parameters, g = manifest.geometry_parameters;
const slope = Math.tan(g.roof_pitch_degrees * Math.PI / 180);
const near = (actual, expected, tolerance = 2e-5) => assert.ok(Math.abs(actual - expected) <= tolerance,
  `${actual} differs from ${expected} by more than ${tolerance}`);
await initializeSectionCapsWasm(await readFile(new URL('../src/wasm/section_caps_bg.wasm', import.meta.url)));

async function loadHouse() {
  const gltf = await loadGlbGeometry(new URL('../../GLB/house_3d.glb', import.meta.url));
  gltf.scene.updateMatrixWorld(true);
  return { gltf, nodes: bindCadNodes(gltf) };
}

function boxInCadMillimetres(mesh) {
  const b = new Box3().setFromObject(mesh);
  return [b.min.x * 1000, -b.max.z * 1000, b.min.y * 1000,
    b.max.x * 1000, -b.min.z * 1000, b.max.y * 1000];
}

test('the R09 GLB includes named balcony geometry and stores the attic inside the coordinated roof', async () => {
  const { gltf, nodes } = await loadHouse();
  const meshes = gltf.parser.json.nodes.filter(node => node.mesh !== undefined);
  const added = meshes.filter(node => /^(?:attic|attic_access):/.test(node.name));
  const site = meshes.filter(node => /^(?:foundation|yard|fence):/.test(node.name));
  const structure = meshes.filter(node => node.name.startsWith('structure:'));
  const lighting = meshes.filter(node => node.name.startsWith('lighting:'));
  assert.equal(lighting.length, 32, 'R08 adds outdoor fixtures independently of the retained R03/attic geometry');
  assert.ok(meshes.some(node => node.name === 'balcony:slab'));
  assert.ok(meshes.some(node => node.name === 'balcony:drying_rail'));
  assert.equal(meshes.length, manifest.glb_export.named_mesh_nodes);
  assert.equal(added.filter(node => node.name.startsWith('attic:')).length, 31);
  assert.equal(added.filter(node => node.name.startsWith('attic_access:')).length, a.ladder_treads + 6);
  const floor = nodes.get('attic:floor_slab');
  assert.equal(nodes.get('roof:attic_ceiling_slab').parent, floor);
  assert.equal(nodes.get('attic:deck_finish').parent, floor);
  assert.notEqual(nodes.get('roof:attic_ceiling_slab').parent, nodes.get('roof'));
  for (const node of added.filter(node => node.name.startsWith('attic:'))) {
    const mesh = nodes.get(node.name);
    assert.ok(mesh?.isMesh, `${node.name} is a named selectable mesh`);
    const position = mesh.geometry.getAttribute('position');
    assert.ok(position.count > 3, `${node.name} contains real geometry`);
    for (let index = 0; index < position.count; index++) {
      const vertex = new Vector3().fromBufferAttribute(position, index).applyMatrix4(mesh.matrixWorld);
      assert.ok([vertex.x, vertex.y, vertex.z].every(Number.isFinite), `${node.name}: finite geometry`);
      const x = vertex.x * 1000, y = -vertex.z * 1000, z = vertex.y * 1000;
      assert.ok(x >= -.02 && x <= p.width + .02 && y >= -.02 && y <= p.depth + .02,
        `${node.name}: the attic stays within the existing plan outline`);
      assert.ok(z <= 2 * p.storey_height + Math.min(x, p.width - x) * slope + .02,
        `${node.name}: the attic never protrudes through the gable roof`);
    }
  }
});

test('the saved floor and lining geometry agrees with the recorded storage area and clear heights', async () => {
  const { nodes } = await loadHouse();
  for (const [name, expected] of [['roof:attic_ceiling_slab', attic.slab_bounds_mm],
    ['attic:deck_finish', attic.deck_bounds_mm]]) {
    const actual = boxInCadMillimetres(nodes.get(name));
    actual.forEach((value, index) => near(value, expected[index], .02));
  }
  const deckTop = attic.deck_bounds_mm[5];
  const flat = nodes.get('attic:lining:flat_ceiling');
  assert.ok(flat?.isMesh, 'R06 has a real selectable flat ceiling, not only a clip plane');
  boxInCadMillimetres(flat).forEach((value, index) => near(value, attic.flat_ceiling_bounds_mm[index], .02));
  near(attic.slab_bounds_mm[5] - attic.slab_bounds_mm[2], 24);
  near(attic.flat_ceiling_bounds_mm[2] - deckTop, 1350);
  near(attic.clear_height_mm.maximum, 1350);
  near(attic.clear_height_mm.ridge, 1350);
  const computedEdgeHeight = 2 * p.storey_height + attic.deck_bounds_mm[0] * slope
    - a.lining_vertical_allowance - deckTop;
  near(computedEdgeHeight, attic.clear_height_mm.deck_edge, .02);
  // Reconstruct lower planes from all three physical ceiling meshes. Sample
  // the whole deck and entry against them, including both slope/flat joints.
  const surfaces = [];
  for (const name of ['attic:lining:west_slope', 'attic:lining:flat_ceiling', 'attic:lining:east_slope']) {
    const mesh = nodes.get(name), positions = mesh.geometry.getAttribute('position');
    const byX = new Map();
    for (let index = 0; index < positions.count; index++) {
      const vertex = new Vector3().fromBufferAttribute(positions, index).applyMatrix4(mesh.matrixWorld);
      const x = Math.round(vertex.x * 1000 * 100) / 100;
      byX.set(x, Math.min(byX.get(x) ?? Infinity, vertex.y * 1000));
    }
    const xs = [...byX.keys()].sort((left, right) => left - right);
    surfaces.push({ x1: xs[0], x2: xs.at(-1), z1: byX.get(xs[0]), z2: byX.get(xs.at(-1)) });
  }
  near(surfaces[0].x2, surfaces[1].x1, .02);
  near(surfaces[1].x2, surfaces[2].x1, .02);
  near(surfaces[0].z2, surfaces[1].z1, .02);
  near(surfaces[1].z2, surfaces[2].z1, .02);
  const lowerCeiling = x => {
    const applicable = surfaces.filter(surface => x >= surface.x1 - .02 && x <= surface.x2 + .02);
    assert.ok(applicable.length, `a real ceiling covers deck X=${x}`);
    return Math.min(...applicable.map(({ x1, x2, z1, z2 }) => z1 + (x - x1) * (z2 - z1) / (x2 - x1)));
  };
  for (let index = 0; index <= 100; index++) {
    const x = attic.deck_bounds_mm[0] + index / 100 * a.deck_width;
    const actualHeight = lowerCeiling(x) - deckTop;
    const expected = Math.min(2 * p.storey_height + Math.min(x, p.width - x) * slope
      - a.lining_vertical_allowance - deckTop, a.maximum_finished_clear_height);
    near(actualHeight, expected, .03);
    assert.ok(actualHeight <= 1350.03, 'the whole finished storage space is capped at1350 mm');
  }
  const upperEntry = attic.ladder.upper_landing_bounds_mm;
  const entryClearHeight = Math.min(lowerCeiling(upperEntry[0]), lowerCeiling(upperEntry[2])) - deckTop;
  near(entryClearHeight, attic.ladder.upper_landing_min_clear_height_mm, .02);
  assert.ok(entryClearHeight >= 1250 && entryClearHeight <= 1350.02, 'upper attic standing area retains at least 1250 mm demonstration headroom');
  assert.match(attic.statutory_area_status, /classification pending/,
    'finished height and geometric area are not presented as statutory approval');
  near(attic.storage_projection_area_m2,
    (a.deck_width * (p.depth - 2 * a.deck_end_inset) - a.hatch_length * a.hatch_width) / 1e6, 1e-6);
});

function inspectCap(mesh, geometry, height) {
  const position = geometry.getAttribute('position'), normal = geometry.getAttribute('normal');
  const normalMatrix = new Matrix3().getNormalMatrix(mesh.matrixWorld);
  assert.equal(position.count % 3, 0);
  assert.equal(normal.count, position.count);
  let area = 0;
  const triangles = [];
  for (let index = 0; index < position.count; index += 3) {
    const triangle = [0, 1, 2].map(offset => new Vector3()
      .fromBufferAttribute(position, index + offset).applyMatrix4(mesh.matrixWorld));
    for (let offset = 0; offset < 3; offset++) {
      near(triangle[offset].y, height, 1e-6);
      const worldNormal = new Vector3().fromBufferAttribute(normal, index + offset).applyMatrix3(normalMatrix).normalize();
      near(worldNormal.y, 1, 1e-6);
    }
    const cross = new Vector3().subVectors(triangle[1], triangle[0])
      .cross(new Vector3().subVectors(triangle[2], triangle[0]));
    assert.ok(cross.y > 0, 'every hatch section triangle faces upward and has positive area');
    area += cross.y / 2;
    triangles.push(triangle);
  }
  return { area, triangles };
}

function covered(triangles, point) {
  return triangles.some(triangle => {
    const [v0, v1, v2] = triangle;
    const cross = (start, end) => (end.x - start.x) * (point.z - start.z)
      - (end.z - start.z) * (point.x - start.x);
    return [cross(v0, v1), cross(v1, v2), cross(v2, v0)].every(value => value <= 1e-8);
  });
}

test('TS and Rust/WASM floor sections preserve the actual through-hatch after viewer centering', async () => {
  const { gltf, nodes } = await loadHouse();
  assert.equal(centerModelAtFloorDatum(gltf.scene, nodes), true);
  const floorOffset = gltf.scene.position.y;
  const hatch = attic.hatch_bounds_mm;
  const point = (x, y, height) => new Vector3(x / 1000 + gltf.scene.position.x,
    height, -y / 1000 + gltf.scene.position.z);
  for (const [name, planeMm, expectedArea] of [
    ['roof:attic_ceiling_slab', (attic.slab_bounds_mm[2] + attic.slab_bounds_mm[5]) / 2,
      ((attic.slab_bounds_mm[3] - attic.slab_bounds_mm[0]) * (attic.slab_bounds_mm[4] - attic.slab_bounds_mm[1])
        - a.hatch_length * a.hatch_width) / 1e6],
    ['attic:deck_finish', (attic.deck_bounds_mm[2] + attic.deck_bounds_mm[5]) / 2, attic.storage_projection_area_m2],
  ]) {
    const mesh = nodes.get(name), height = planeMm / 1000 + floorOffset;
    const actualAreas = [];
    for (const [backend, create] of [['TS', createHorizontalCap], ['WASM', createWasmHorizontalCap]]) {
      const geometry = create(mesh, height);
      assert.ok(geometry, `${backend}: ${name} has a nonempty cut surface`);
      try {
        const { area, triangles } = inspectCap(mesh, geometry, height);
        near(area, expectedArea);
        actualAreas.push(area);
        for (const ratioX of [.1, .5, .9]) for (const ratioY of [.1, .5, .9]) {
          assert.equal(covered(triangles, point(hatch[0] + ratioX * (hatch[3] - hatch[0]),
            hatch[1] + ratioY * (hatch[4] - hatch[1]), height)), false,
          `${backend}: ${name} must not seal the ladder opening at ${ratioX}, ${ratioY}`);
        }
        assert.ok(covered(triangles, point(hatch[0] - 200, (hatch[1] + hatch[4]) / 2, height)),
          `${backend}: adjacent floor remains solid`);
      } finally { geometry.dispose(); }
    }
    near(actualAreas[0], actualAreas[1]);
  }
});

test('the deployed access ladder joins the second-floor datum to the open east side of the attic', async () => {
  const { nodes } = await loadHouse();
  const left = boxInCadMillimetres(nodes.get('attic_access:left_stringer'));
  const right = boxInCadMillimetres(nodes.get('attic_access:right_stringer'));
  for (const bounds of [left, right]) {
    near(bounds[0], attic.ladder.foot_mm[0], .02);
    near(bounds[2], p.storey_height, .02);
    near(bounds[3], attic.hatch_bounds_mm[3], .02);
    near(bounds[5], attic.deck_bounds_mm[5], .02);
  }
  near(right[4] - left[1], a.ladder_width, .02);
  near(right[1] - left[4], a.ladder_width - 2 * a.ladder_stringer_width, .02);
  const treads = [...nodes].filter(([name, mesh]) => /^attic_access:tread_\d+$/.test(name) && mesh.isMesh);
  assert.equal(treads.length, attic.ladder.tread_count);
  for (let index = 1; index <= a.ladder_treads; index++) {
    const bounds = boxInCadMillimetres(nodes.get(`attic_access:tread_${String(index).padStart(2, '0')}`));
    near(bounds[5], p.storey_height + index * attic.ladder.riser_mm, .02);
    near(bounds[4] - bounds[1], a.ladder_width - 2 * a.ladder_stringer_width, .02);
  }
  assert.equal(nodes.has('attic:guardrail:east_rail'), false, 'the top entry side remains open');
  const hatch = attic.hatch_bounds_mm;
  for (const [name, mesh] of nodes) {
    if (!name.startsWith('attic:guardrail:') || !mesh.isMesh) continue;
    const bounds = boxInCadMillimetres(mesh);
    const overlapX = Math.min(bounds[3], hatch[3]) - Math.max(bounds[0], hatch[0]);
    const overlapY = Math.min(bounds[4], hatch[4]) - Math.max(bounds[1], hatch[1]);
    assert.ok(overlapX < .02 || overlapY < .02, `${name}: guardrails do not block the hatch footprint`);
  }
});
