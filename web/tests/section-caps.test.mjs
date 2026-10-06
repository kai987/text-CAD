import test from 'node:test';
import assert from 'node:assert/strict';
import { Box3, BoxGeometry, ExtrudeGeometry, Matrix3, Mesh, Path, PlaneGeometry, Shape, Vector3 } from 'three';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { bindCadNodes } from '../src/model-scene.ts';
import { createHorizontalCap } from '../src/section-caps.ts';

const near = (actual, expected, tolerance = 2e-5) => assert.ok(Math.abs(actual - expected) <= tolerance,
  `${actual} differs from ${expected}`);
function inspectCap(mesh, geometry, height) {
  const positions = geometry.getAttribute('position'), normals = geometry.getAttribute('normal');
  const normalMatrix = new Matrix3().getNormalMatrix(mesh.matrixWorld);
  const triangles = [];
  let area = 0;
  for (let i = 0; i < positions.count; i += 3) {
    const triangle = [0, 1, 2].map(offset => new Vector3().fromBufferAttribute(positions, i + offset).applyMatrix4(mesh.matrixWorld));
    for (let j = 0; j < 3; j++) {
      near(triangle[j].y, height, 1e-6);
      const normal = new Vector3().fromBufferAttribute(normals, i + j).applyMatrix3(normalMatrix).normalize();
      near(normal.y, 1, 1e-6);
    }
    const cross = new Vector3().subVectors(triangle[1], triangle[0]).cross(new Vector3().subVectors(triangle[2], triangle[0]));
    assert.ok(cross.y > 0, 'all cap triangles must face upward');
    area += cross.y / 2; triangles.push(triangle);
  }
  return { area, triangles };
}
async function house() {
  const gltf = await loadGlbGeometry(new URL('../../GLB/house_3d.glb', import.meta.url));
  const bounds = new Box3().setFromObject(gltf.scene), center = bounds.getCenter(new Vector3());
  const offset = -bounds.min.y;
  gltf.scene.position.set(-center.x, offset, -center.z); gltf.scene.updateMatrixWorld(true);
  return { nodes: bindCadNodes(gltf), offset };
}
test('all actual second-floor cabinet sections at 4200 mm are closed and upward', async () => {
  const { nodes, offset } = await house();
  const cabinets = [...nodes].filter(([name, object]) => /^F2:storage_\d+$/.test(name) && object.isMesh);
  assert.equal(cabinets.length, 3);
  for (const [name, mesh] of cabinets) {
    const height = 4.2 + offset, cap = createHorizontalCap(mesh, height);
    assert.ok(cap, `${name} must have a cap`);
    const bounds = new Box3().setFromObject(mesh);
    const { area } = inspectCap(mesh, cap, height);
    near(area, (bounds.max.x - bounds.min.x) * (bounds.max.z - bounds.min.z));
    assert.equal(createHorizontalCap(mesh, bounds.min.y), null);
    assert.equal(createHorizontalCap(mesh, bounds.max.y), null);
    assert.equal(createHorizontalCap(mesh, bounds.max.y + 1), null);
    cap.dispose();
  }
});
test('actual second-floor slab retains the stair opening in its section', async () => {
  const { nodes, offset } = await house();
  const mesh = nodes.get('F2:floor_slab'), height = 2.7 + offset;
  const cap = createHorizontalCap(mesh, height);
  assert.ok(cap);
  // R09 outline 8190 x 7280 mm minus a 22 mm siding/gap setback on each side;
  // the approved 1900 x 2720 mm stair opening and room boundaries are unchanged.
  near(inspectCap(mesh, cap, height).area, 8.146 * 7.236 - 1.9 * 2.72);
  cap.dispose();
});
test('nested contours preserve holes and disconnected solid islands', () => {
  const ring = new Shape().moveTo(0, 0).lineTo(4, 0).lineTo(4, 3).lineTo(0, 3).closePath();
  const hole = new Path().moveTo(1, 1).lineTo(1, 2).lineTo(3, 2).lineTo(3, 1).closePath();
  ring.holes.push(hole);
  const island = new Shape().moveTo(1.5, 1.25).lineTo(2.5, 1.25).lineTo(2.5, 1.75).lineTo(1.5, 1.75).closePath();
  const mesh = new Mesh(new ExtrudeGeometry([ring, island], { depth: 2, bevelEnabled: false }));
  mesh.rotation.x = -Math.PI / 2;
  const cap = createHorizontalCap(mesh, 1);
  assert.ok(cap);
  const result = inspectCap(mesh, cap, 1);
  near(result.area, 12 - 2 + 0.5);
  for (const triangle of result.triangles) {
    const center = triangle.reduce((sum, point) => sum.add(point), new Vector3()).divideScalar(3);
    const inHole = center.x > 1 && center.x < 3 && center.z < -1 && center.z > -2;
    const inIsland = center.x >= 1.5 && center.x <= 2.5 && center.z <= -1.25 && center.z >= -1.75;
    assert.ok(!inHole || inIsland, 'triangulation must not fill the empty hole');
  }
  cap.dispose(); mesh.geometry.dispose();
});
test('tangent planes and out-of-range cuts produce no degenerate cap', () => {
  const mesh = new Mesh(new BoxGeometry(2, 2, 2));
  for (const height of [-2, -1, 1, 2, NaN]) assert.equal(createHorizontalCap(mesh, height), null);
  const cap = createHorizontalCap(mesh, 0);
  assert.ok(cap); near(inspectCap(mesh, cap, 0).area, 4);
  cap.dispose(); mesh.geometry.dispose();
});
test('translated, rotated and nonuniformly scaled meshes keep the cap on the world plane with world-up normals', () => {
  const mesh = new Mesh(new BoxGeometry(2, 2, 2));
  mesh.position.set(4, 3, -2); mesh.rotation.set(0.3, 0.2, 0.4); mesh.scale.set(1.4, 0.8, 1.1);
  const cap = createHorizontalCap(mesh, 3);
  assert.ok(cap);
  assert.ok(inspectCap(mesh, cap, 3).area > 0);
  cap.dispose(); mesh.geometry.dispose();
});
test('a plane through exact mesh vertex levels remains stable, while an open surface has no invented cap', () => {
  const mesh = new Mesh(new BoxGeometry(2, 2, 2));
  mesh.rotation.z = Math.PI / 4;
  const cap = createHorizontalCap(mesh, 0);
  assert.ok(cap); near(inspectCap(mesh, cap, 0).area, 4 * Math.sqrt(2), 4e-5);
  const open = new Mesh(new PlaneGeometry(2, 2));
  assert.equal(createHorizontalCap(open, 0), null);
  cap.dispose(); mesh.geometry.dispose(); open.geometry.dispose();
});
