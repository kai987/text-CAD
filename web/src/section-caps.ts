import { BufferGeometry, Float32BufferAttribute, Matrix3, Matrix4, ShapeUtils, Vector2, Vector3 } from 'three';
import type { Mesh } from 'three';

// GLB coordinates are metres. Weld tessellation seams within two micrometres.
const WELD = 2e-6;
interface SectionPoint { x: number; z: number }

function area(points: SectionPoint[]): number {
  return points.reduce((sum, point, i) => {
    const next = points[(i + 1) % points.length];
    return sum + point.x * next.z - next.x * point.z;
  }, 0) / 2;
}

function contains(point: SectionPoint, loop: SectionPoint[]): boolean {
  let inside = false;
  for (let i = 0, j = loop.length - 1; i < loop.length; j = i++) {
    const a = loop[i], b = loop[j];
    if ((a.z > point.z) !== (b.z > point.z) &&
      point.x < (b.x - a.x) * (point.z - a.z) / (b.z - a.z) + a.x) inside = !inside;
  }
  return inside;
}

function simplify(loop: SectionPoint[]): SectionPoint[] {
  let points = loop;
  let changed = true;
  while (changed && points.length > 3) {
    changed = false;
    const next = points.filter((b, i) => {
      const a = points[(i + points.length - 1) % points.length], c = points[(i + 1) % points.length];
      const length = Math.hypot(c.x - a.x, c.z - a.z);
      const cross = (b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x);
      const between = (b.x - a.x) * (b.x - c.x) + (b.z - a.z) * (b.z - c.z) <= WELD * WELD;
      if (length > WELD && Math.abs(cross) <= WELD * length && between) { changed = true; return false; }
      return true;
    });
    // Retain the prior loop rather than creating a degenerate polygon.
    if (next.length < 3) break;
    points = next;
  }
  return points;
}

/**
 * Section a closed CAD mesh by a horizontal world-space plane.
 * Returns upward-facing triangles in mesh-local coordinates, including holes.
 * Tangencies, cuts outside the solid, and non-manifold/open contours return null.
 * At a vertex level, use the retained (lower) side's limiting cross-section.
 */
export function createHorizontalCap(mesh: Mesh, worldHeight: number): BufferGeometry | null {
  if (!Number.isFinite(worldHeight)) return null;
  mesh.updateWorldMatrix(true, false);
  if (mesh.matrixWorld.determinant() === 0) return null;
  const positions = mesh.geometry.getAttribute('position');
  if (!positions) return null;
  const vertices: Vector3[] = [];
  let minY = Infinity, maxY = -Infinity;
  for (let i = 0; i < positions.count; i++) {
    const point = new Vector3().fromBufferAttribute(positions, i).applyMatrix4(mesh.matrixWorld);
    vertices.push(point); minY = Math.min(minY, point.y); maxY = Math.max(maxY, point.y);
  }
  if (worldHeight <= minY + WELD || worldHeight >= maxY - WELD) return null;
  // Avoid ambiguous coincident triangle edges; output still lies on the requested plane.
  const sampleHeight = worldHeight - WELD * 4;
  const points: SectionPoint[] = [];
  const buckets = new Map<string, number[]>();
  const neighbors = new Map<number, Set<number>>();
  function weld(point: SectionPoint): number {
    const x = Math.floor(point.x / WELD), z = Math.floor(point.z / WELD);
    for (let dx = -1; dx <= 1; dx++) for (let dz = -1; dz <= 1; dz++) {
      for (const index of buckets.get(`${x + dx},${z + dz}`) ?? []) {
        if (Math.hypot(points[index].x - point.x, points[index].z - point.z) <= WELD) return index;
      }
    }
    const index = points.push(point) - 1, key = `${x},${z}`;
    buckets.set(key, [...buckets.get(key) ?? [], index]);
    return index;
  }
  const index = mesh.geometry.getIndex();
  const count = index?.count ?? positions.count;
  for (let i = 0; i + 2 < count; i += 3) {
    const triangle = [0, 1, 2].map(offset => vertices[index ? index.getX(i + offset) : i + offset]);
    const intersections: SectionPoint[] = [];
    for (let edge = 0; edge < 3; edge++) {
      const a = triangle[edge], b = triangle[(edge + 1) % 3];
      const da = a.y - sampleHeight, db = b.y - sampleHeight;
      if ((da > 0) === (db > 0)) continue;
      const t = da / (da - db);
      intersections.push({ x: a.x + (b.x - a.x) * t, z: a.z + (b.z - a.z) * t });
    }
    if (intersections.length !== 2) continue;
    const a = weld(intersections[0]), b = weld(intersections[1]);
    if (a === b) continue;
    if (!neighbors.has(a)) neighbors.set(a, new Set());
    if (!neighbors.has(b)) neighbors.set(b, new Set());
    neighbors.get(a)!.add(b); neighbors.get(b)!.add(a);
  }
  if (!neighbors.size || [...neighbors.values()].some(edges => edges.size !== 2)) return null;
  const visited = new Set<number>();
  const loops: SectionPoint[][] = [];
  for (const start of neighbors.keys()) {
    if (visited.has(start)) continue;
    const loop: SectionPoint[] = [];
    let previous = -1, current = start;
    do {
      if (visited.has(current)) return null;
      visited.add(current); loop.push(points[current]);
      const next = [...neighbors.get(current)!].find(neighbor => neighbor !== previous)!;
      previous = current; current = next;
    } while (current !== start);
    const simplified = simplify(loop);
    if (simplified.length >= 3 && Math.abs(area(simplified)) > WELD * WELD) loops.push(simplified);
  }
  if (!loops.length) return null;
  const areas = loops.map(loop => Math.abs(area(loop)));
  const parents = loops.map((loop, i) => {
    let parent = -1;
    for (let j = 0; j < loops.length; j++) {
      if (areas[j] > areas[i] && contains(loop[0], loops[j]) && (parent === -1 || areas[j] < areas[parent])) parent = j;
    }
    return parent;
  });
  function depth(i: number): number { return parents[i] === -1 ? 0 : depth(parents[i]) + 1; }
  const inverse = new Matrix4().copy(mesh.matrixWorld).invert();
  const normal = new Vector3(0, 1, 0).applyMatrix3(new Matrix3().setFromMatrix4(mesh.matrixWorld).transpose()).normalize();
  const output: number[] = [], normals: number[] = [];
  for (let i = 0; i < loops.length; i++) {
    if (depth(i) % 2 !== 0) continue;
    const holes = loops.filter((_, j) => parents[j] === i);
    const contour = loops[i].map(point => new Vector2(point.x, point.z));
    const holePoints = holes.map(loop => loop.map(point => new Vector2(point.x, point.z)));
    const flat = [loops[i], ...holes].flat();
    for (const triangle of ShapeUtils.triangulateShape(contour, holePoints)) {
      const [a, b, c] = triangle.map(index => flat[index]);
      const signed = (b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x);
      if (Math.abs(signed) <= WELD * WELD) continue;
      const ordered = signed > 0 ? [a, c, b] : [a, b, c];
      for (const point of ordered) {
        const local = new Vector3(point.x, worldHeight, point.z).applyMatrix4(inverse);
        output.push(local.x, local.y, local.z); normals.push(normal.x, normal.y, normal.z);
      }
    }
  }
  if (!output.length) return null;
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute(output, 3));
  geometry.setAttribute('normal', new Float32BufferAttribute(normals, 3));
  geometry.computeBoundingBox(); geometry.computeBoundingSphere();
  return geometry;
}
