import { BufferAttribute, BufferGeometry, Mesh, Sphere } from 'three';
import type { Object3D, OrthographicCamera } from 'three';

export type TreeDetail = 'coarse' | 'detailed';

/** Retain complete disconnected leaf/petal patches from the current foliage
 * export. Whole patches preserve leaf edges, normals and linear vertex colors;
 * isolated triangles or closed hulls would change its appearance. */
export function createCrownProxy(source: BufferGeometry): BufferGeometry | null {
  const position = source.getAttribute('position'), normal = source.getAttribute('normal'), color = source.getAttribute('color');
  const index = source.index;
  if (!index || index.count % 3 || !position || !normal || !color || position.count < 64 ||
      position.itemSize !== 3 || normal.itemSize !== 3 || color.itemSize !== 3 ||
      position.count !== normal.count || position.count !== color.count) return null;
  const patches: { start: number; end: number; low: number; high: number }[] = [];
  let start = 0, low = 0, high = -1;
  for (let i = 0; i < index.count; i += 3) {
    const a = index.getX(i), b = index.getX(i + 1), c = index.getX(i + 2);
    const first = Math.min(a, b, c), last = Math.max(a, b, c);
    if (first < low || last >= position.count) return null;
    if (first > high) {
      // natural_trees_v1 stores each disconnected patch contiguously. A mesh
      // outside that bounded format keeps its full original geometry instead.
      if (first !== high + 1) return null;
      if (high >= 0) patches.push({ start, end: i, low, high });
      start = i; low = first;
    }
    high = Math.max(high, last);
  }
  if (high !== position.count - 1 || !patches.length) return null;
  patches.push({ start, end: index.count, low, high });
  const minimum = [Infinity, Infinity, Infinity], maximum = [-Infinity, -Infinity, -Infinity];
  const extremes = [0, 0, 0, 0, 0, 0];
  for (let i = 0; i < position.count; i++) {
    const values = [position.getX(i), position.getY(i), position.getZ(i)];
    for (let axis = 0; axis < 3; axis++) {
      const value = values[axis];
      if (!Number.isFinite(value)) return null;
      if (value < minimum[axis]) { minimum[axis] = value; extremes[axis] = i; }
      if (value > maximum[axis]) { maximum[axis] = value; extremes[axis + 3] = i; }
    }
  }
  // Keep extrema patches too, so bounds/planting footprints and zoom thresholds
  // agree with the full model. Remaining patches are a stable spatial sample
  // because the exporter already distributes foliage using each tree's seed.
  const selected = patches.filter((patch, i) => i % 4 === 0 || extremes.some(vertex => vertex >= patch.low && vertex <= patch.high));
  const vertexCount = selected.reduce((count, patch) => count + patch.high - patch.low + 1, 0);
  const indexCount = selected.reduce((count, patch) => count + patch.end - patch.start, 0);
  const positions = new Float32Array(vertexCount * 3), normals = new Float32Array(vertexCount * 3), colors = new Float32Array(vertexCount * 3);
  const indices = vertexCount <= 65535 ? new Uint16Array(indexCount) : new Uint32Array(indexCount);
  let targetVertex = 0, targetIndex = 0;
  for (const patch of selected) {
    const offset = targetVertex;
    for (let vertex = patch.low; vertex <= patch.high; vertex++) {
      const xyz = [position.getX(vertex), position.getY(vertex), position.getZ(vertex)];
      const n = [normal.getX(vertex), normal.getY(vertex), normal.getZ(vertex)];
      const rgb = [color.getX(vertex), color.getY(vertex), color.getZ(vertex)];
      if (![...n, ...rgb].every(Number.isFinite)) return null;
      positions.set(xyz, targetVertex * 3); normals.set(n, targetVertex * 3); colors.set(rgb, targetVertex * 3); targetVertex++;
    }
    for (let i = patch.start; i < patch.end; i++) indices[targetIndex++] = index.getX(i) - patch.low + offset;
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new BufferAttribute(normals, 3));
  geometry.setAttribute('color', new BufferAttribute(colors, 3));
  geometry.setIndex(new BufferAttribute(indices, 1));
  geometry.computeBoundingBox(); geometry.computeBoundingSphere();
  return geometry;
}

export function chooseTreeDetail(current: TreeDetail, diameterPixels: number, thresholdPixels: number): TreeDetail {
  if (thresholdPixels <= 0 || !Number.isFinite(diameterPixels)) return 'detailed';
  // Hysteresis prevents leaf silhouettes and cached shadows from chattering
  // while zoom damping settles close to a threshold.
  if (current === 'coarse') return diameterPixels >= thresholdPixels * 1.15 ? 'detailed' : 'coarse';
  return diameterPixels < thresholdPixels * .85 ? 'coarse' : 'detailed';
}

function triangleCount(geometry: BufferGeometry) {
  return (geometry.index?.count ?? geometry.getAttribute('position').count) / 3;
}

export function createRiverTreeDetail(root: Object3D) {
  const entries: { mesh: Mesh; full: BufferGeometry; proxy: BufferGeometry; sphere: Sphere; detail: TreeDetail }[] = [];
  let disposed = false;
  try {
    root.traverse(object => {
      const name = String(object.userData.cadName ?? '');
      if (!(object instanceof Mesh) || !name.startsWith('Landscape:trees:') || !name.endsWith(':crown')) return;
      const full = object.geometry, proxy = createCrownProxy(full);
      if (!proxy) return;
      full.computeBoundingSphere();
      entries.push({ mesh: object, full, proxy, sphere: full.boundingSphere!.clone(), detail: 'detailed' });
    });
  } catch (error) {
    entries.forEach(entry => entry.proxy.dispose());
    throw error;
  }
  const worldSphere = new Sphere();
  return {
    update(camera: OrthographicCamera, viewportHeight: number, thresholdPixels: number): boolean {
      if (disposed || !viewportHeight) return false;
      let changed = false;
      for (const entry of entries) {
        entry.mesh.updateWorldMatrix(true, false);
        worldSphere.copy(entry.sphere).applyMatrix4(entry.mesh.matrixWorld);
        // Orthographic zoom changes apparent size without moving the camera.
        // Measure the original crown, never the currently selected geometry.
        const pixels = 2 * worldSphere.radius * camera.zoom * viewportHeight / (camera.top - camera.bottom);
        const next = chooseTreeDetail(entry.detail, pixels, thresholdPixels);
        if (next === entry.detail) continue;
        entry.detail = next; entry.mesh.geometry = next === 'detailed' ? entry.full : entry.proxy;
        changed = true;
      }
      return changed;
    },
    stats() {
      return {
        crowns: entries.length, detailed: entries.filter(entry => entry.detail === 'detailed').length,
        coarse: entries.filter(entry => entry.detail === 'coarse').length,
        triangles: entries.reduce((total, entry) => total + triangleCount(entry.mesh.geometry), 0),
        fullTriangles: entries.reduce((total, entry) => total + triangleCount(entry.full), 0),
      };
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      // Caller subsequently disposes the model's original geometries/materials.
      for (const entry of entries) { entry.mesh.geometry = entry.full; entry.proxy.dispose(); }
      entries.length = 0;
    },
  };
}
