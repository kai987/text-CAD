import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { Box3, Matrix3, Vector3 } from 'three';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { bindCadNodes, centerModelAtFloorDatum } from '../src/model-scene.ts';
import { createHorizontalCap } from '../src/section-caps.ts';
import { createWasmHorizontalCap, initializeSectionCapsWasm } from '../src/section-caps-wasm.ts';

await initializeSectionCapsWasm(await readFile(new URL('../src/wasm/section_caps_bg.wasm', import.meta.url)));
const near = (actual, expected, tolerance = 2e-5) => assert.ok(Math.abs(actual - expected) <= tolerance,
  `${actual} differs from ${expected} by more than ${tolerance}`);
const backends = [['TS', createHorizontalCap], ['Rust/WASM', createWasmHorizontalCap]];

async function loadHouse() {
  const gltf = await loadGlbGeometry(new URL('../../GLB/house_3d.glb', import.meta.url));
  gltf.scene.updateMatrixWorld(true);
  const nodes = bindCadNodes(gltf);
  assert.equal(centerModelAtFloorDatum(gltf.scene, nodes), true);
  return { gltf, nodes };
}

function meshesIn(group) {
  assert.ok(group, 'the actual saved CAD group exists');
  const meshes = [];
  group.traverse(object => { if (object.isMesh) meshes.push(object); });
  assert.ok(meshes.length > 0, 'the group contains saved triangle geometry');
  return meshes;
}

function inspectCap(mesh, cap, height) {
  const position = cap.getAttribute('position'), normal = cap.getAttribute('normal');
  const normalMatrix = new Matrix3().getNormalMatrix(mesh.matrixWorld);
  assert.equal(position.count % 3, 0);
  assert.equal(normal.count, position.count);
  let area = 0;
  const triangles = [];
  for (let index = 0; index < position.count; index += 3) {
    const vertices = [0, 1, 2].map(offset => new Vector3()
      .fromBufferAttribute(position, index + offset).applyMatrix4(mesh.matrixWorld));
    for (let offset = 0; offset < 3; offset++) {
      near(vertices[offset].y, height, 1e-6);
      const upward = new Vector3().fromBufferAttribute(normal, index + offset).applyMatrix3(normalMatrix).normalize();
      near(upward.y, 1, 1e-6);
    }
    const cross = new Vector3().subVectors(vertices[1], vertices[0])
      .cross(new Vector3().subVectors(vertices[2], vertices[0]));
    assert.ok(cross.y > 0, 'a true saved cut triangle is nondegenerate and faces upwards');
    area += cross.y / 2;
    triangles.push(vertices);
  }
  return { area, triangles };
}

function covers(triangles, point) {
  return triangles.some(([a, b, c]) => [a, b, c].every((start, index, vertices) => {
    const end = vertices[(index + 1) % 3];
    return (end.x - start.x) * (point.z - start.z) - (end.z - start.z) * (point.x - start.x) <= 1e-8;
  }));
}

function groupCaps(group, create, height) {
  let area = 0;
  const triangles = [];
  for (const mesh of meshesIn(group)) {
    const cap = create(mesh, height);
    if (!cap) continue;
    try {
      const inspected = inspectCap(mesh, cap, height);
      area += inspected.area;
      triangles.push(...inspected.triangles);
    } finally { cap.dispose(); }
  }
  return { area, triangles };
}

test('deep site footings do not move architectural levels or cut planes in the saved GLB', async () => {
  const { gltf, nodes } = await loadHouse();
  const savedMeshes = gltf.parser.json.nodes.filter(node => node.mesh !== undefined);
  const siteMeshes = savedMeshes.filter(node => /^(?:foundation|yard|fence):/.test(node.name));
  assert.ok(siteMeshes.length > 113, 'R06 adds internal foundation support ribs');
  assert.ok(savedMeshes.some(node => node.name.startsWith('foundation:internal_supports:')), 'named internal supports exist');
  assert.ok(nodes.get('structure')?.children.length, 'structural proposal is distinct from the site');
  near(new Box3().setFromObject(gltf.scene).min.y, -.95);
  near(new Box3().setFromObject(nodes.get('F1:floor_slab')).max.y, 0);
  near(new Box3().setFromObject(nodes.get('F2:floor_slab')).max.y, 2.8);
  near(new Box3().setFromObject(nodes.get('attic:deck_finish')).max.y, 5.618);
  for (const height of [1.4, 4.2, 6.9]) {
    const name = height === 1.4 ? 'F1:wall_external_south'
      : height === 4.2 ? 'F2:wall_external_south' : 'attic:lining:west_slope';
    const mesh = nodes.get(name);
    assert.ok(mesh?.isMesh, `${name}: real saved part at the requested architectural cut height`);
    for (const [backend, create] of backends) {
      const cap = create(mesh, height);
      assert.ok(cap, `${backend}: the requested height intersects the correct floor's actual geometry`);
      try { inspectCap(mesh, cap, height); } finally { cap.dispose(); }
    }
  }
});

test('saved main and entrance rafts remain distinct and TS/WASM sections agree underground', async () => {
  const { nodes } = await loadHouse();
  const raft = nodes.get('foundation:raft');
  assert.equal(meshesIn(raft).length, 2);
  for (const [backend, create] of backends) {
    const cap = groupCaps(raft, create, -.725);
    near(cap.area, 8.19 * 7.28 + 1.5 * 1.9);
    assert.ok(cap.triangles.length > 0, `${backend}: physical raft has an underground section`);
    assert.equal(groupCaps(raft, create, -.5).triangles.length, 0,
      `${backend}: hidden foundation cannot invent a cut surface above its actual top`);
  }
});

test('fence footing cavities stay open around real embedded posts in both section engines', async () => {
  const { nodes } = await loadHouse();
  const footings = meshesIn(nodes.get('fence:footings'));
  const posts = meshesIn(nodes.get('fence:posts'));
  assert.equal(footings.length, 31);
  assert.equal(posts.length, 31);
  // Sample a corner, middle and final footing using their true exported bounds.
  for (const index of [0, Math.floor(footings.length / 2), footings.length - 1]) {
    const footing = footings[index], box = new Box3().setFromObject(footing), center = box.getCenter(new Vector3());
    const post = posts.find(part => {
      const candidate = new Box3().setFromObject(part).getCenter(new Vector3());
      return Math.abs(candidate.x - center.x) < 1e-5 && Math.abs(candidate.z - center.z) < 1e-5;
    });
    assert.ok(post, 'an independently named actual post aligns with each cut footing cavity');
    const height = -.65, point = new Vector3(center.x, height, center.z);
    for (const [backend, create] of backends) {
      const cap = create(footing, height), postCap = create(post, height);
      assert.ok(cap && postCap, `${backend}: both real solids intersect the embedded-post level`);
      try {
        const inspected = inspectCap(footing, cap, height), postInspected = inspectCap(post, postCap, height);
        near(inspected.area, .3 * .3 - .05 * .05);
        near(postInspected.area, .05 * .05);
        assert.equal(covers(inspected.triangles, point), false, `${backend}: footing does not seal or overlap the post cavity`);
        assert.equal(covers(postInspected.triangles, point), true, `${backend}: post occupies its true separate cavity`);
      } finally { cap.dispose(); postCap.dispose(); }
    }
  }
});

test('soil and separate finishes preserve real foundation and post exclusions in both cut engines', async () => {
  const { gltf, nodes } = await loadHouse();
  const point = (x, y, height) => new Vector3(x / 1000 + gltf.scene.position.x,
    height, -y / 1000 + gltf.scene.position.z);
  const firstFooting = new Box3().setFromObject(meshesIn(nodes.get('fence:footings'))[0]);
  const footingCenter = firstFooting.getCenter(new Vector3());
  for (const [backend, create] of backends) {
    const soil = groupCaps(nodes.get('yard:soil'), create, -.6);
    near(soil.area, 114.2975, 2e-4);
    for (const [x, y, name] of [[3640, 3640, 'house raft'], [6760, -950, 'entrance footing']]) {
      assert.equal(covers(soil.triangles, point(x, y, -.6)), false,
        `${backend}: soil must not fill the ${name} exclusion`);
    }
    assert.equal(covers(soil.triangles, new Vector3(footingCenter.x, -.6, footingCenter.z)), false,
      `${backend}: soil retains the full 300 mm footing hole`);
    assert.equal(covers(soil.triangles, point(6760, -4000, -.6)), true,
      `${backend}: the actual footpath has supporting soil beneath its paving`);
    const finishParts = ['yard:ground_surfaces:gravel', 'yard:entrance_path:paving', 'yard:parking:paving',
      ...['front', 'north', 'east', 'west'].map(name => `yard:planting:lawn_${name}`)];
    let finishArea = 0;
    const finishTriangles = [];
    for (const name of finishParts) {
      const cap = create(nodes.get(name), -.525);
      assert.ok(cap, `${backend}: ${name} has an actual cut finish`);
      try {
        const inspected = inspectCap(nodes.get(name), cap, -.525);
        finishArea += inspected.area;
        finishTriangles.push(...inspected.triangles);
      } finally { cap.dispose(); }
    }
    near(finishArea, 117.01, 2e-4);
    assert.equal(covers(finishTriangles, new Vector3(footingCenter.x, -.525, footingCenter.z)), false,
      `${backend}: the smaller 50 mm finish hole still leaves its post open`);
    assert.equal(covers(finishTriangles, new Vector3(footingCenter.x + .09, -.525, footingCenter.z)), true,
      `${backend}: finish covers concrete beside the post instead of repeating the wider soil hole`);
    assert.equal(covers(finishTriangles, point(3640, 3640, -.525)), false,
      `${backend}: finish cannot fill the retained building foundation`);
  }
});
