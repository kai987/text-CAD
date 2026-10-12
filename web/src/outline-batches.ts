import { BufferAttribute, BufferGeometry, Group, LineSegments, Matrix4, Vector3 } from 'three';
import type { InterleavedBufferAttribute, LineBasicMaterial, Mesh, Object3D } from 'three';

export type OutlineStyle = 'standard' | 'detail';

export interface OutlineBatchStats {
  registeredMeshes: number;
  visibleMeshes: number;
  segments: number;
  drawCalls: number;
  rebuilds: number;
}

interface OutlineEntry { mesh: Mesh; geometry: BufferGeometry; style: OutlineStyle }
interface VisibleEntry extends OutlineEntry {
  position: BufferAttribute | InterleavedBufferAttribute;
  positionVersion: number;
  index: BufferAttribute | null;
  indexVersion: number;
  start: number;
  count: number;
  matrix: Matrix4;
}

function isVisible(object: Object3D) {
  for (let ancestor: Object3D | null = object; ancestor; ancestor = ancestor.parent) {
    if (!ancestor.visible) return false;
  }
  return true;
}

function attributeVersion(attribute: BufferAttribute | InterleavedBufferAttribute) {
  return 'data' in attribute ? attribute.data.version : attribute.version;
}

function unchanged(a: VisibleEntry[], b: VisibleEntry[]) {
  return a.length === b.length && a.every((previous, i) => {
    const next = b[i];
    return previous.mesh === next.mesh && previous.geometry === next.geometry && previous.style === next.style &&
      previous.position === next.position && previous.positionVersion === next.positionVersion &&
      previous.index === next.index && previous.indexVersion === next.indexVersion &&
      previous.start === next.start && previous.count === next.count && previous.matrix.equals(next.matrix);
  });
}

/** Merge display-only outlines without changing the named, pickable source meshes.
 *
 * Materials are two dedicated instances supplied by the viewer so its day/night
 * palette can update them as usual. This manager owns those instances and every
 * registered outline geometry, including replacements. It never owns mesh solids.
 * Call update() after visibility, transforms, registration or asynchronous results
 * change. Camera moves, selection and palette updates do not require vertex copies.
 * Global renderer clipping applies to the combined lines, including cap outlines.
 */
export function createOutlineBatches(parent: Object3D, materials: Record<OutlineStyle, LineBasicMaterial>) {
  const root = new Group();
  root.name = '__cad_outline_batches';
  const styles: OutlineStyle[] = ['standard', 'detail'];
  const lines = new Map(styles.map(style => {
    const line = new LineSegments(new BufferGeometry(), materials[style]);
    line.name = `__cad_outline_${style}`;
    line.visible = false;
    // Preserve the default depth, clipping and render order. Three sorts these
    // two transparent objects by batch bounds rather than old component bounds;
    // glass/outline ordering therefore also needs a rendered visual comparison.
    // Concatenation never deduplicates shared endpoints or changes an edge.
    root.add(line);
    return [style, line] as const;
  }));
  parent.add(root);
  const entries = new Map<Mesh, OutlineEntry>();
  const geometryReferences = new Map<BufferGeometry, number>();
  let previous: VisibleEntry[] = [];
  let disposed = false;
  let rebuilds = 0;
  let visibleMeshes = 0;
  let segments = 0;
  let drawCalls = 0;

  function retain(geometry: BufferGeometry) {
    geometryReferences.set(geometry, (geometryReferences.get(geometry) ?? 0) + 1);
  }
  function release(geometry: BufferGeometry) {
    const count = geometryReferences.get(geometry) ?? 0;
    if (count > 1) geometryReferences.set(geometry, count - 1);
    else { geometryReferences.delete(geometry); geometry.dispose(); }
  }
  function stats(): OutlineBatchStats {
    return { registeredMeshes: entries.size, visibleMeshes, segments, drawCalls, rebuilds };
  }
  function set(mesh: Mesh, geometry: BufferGeometry, style: OutlineStyle = 'standard') {
    if (disposed) { geometry.dispose(); return; }
    const old = entries.get(mesh);
    if (old?.geometry !== geometry) {
      retain(geometry);
      if (old) release(old.geometry);
    }
    entries.set(mesh, { mesh, geometry, style });
  }
  function remove(mesh: Mesh) {
    const old = entries.get(mesh);
    if (!old) return;
    entries.delete(mesh);
    release(old.geometry);
  }
  function update(): OutlineBatchStats {
    if (disposed) return stats();
    // A single world-matrix traversal covers the usual scene and all overlays.
    parent.updateWorldMatrix(true, true);
    const inverse = new Matrix4().copy(root.matrixWorld).invert();
    const next: VisibleEntry[] = [];
    for (const entry of entries.values()) {
      if (!isVisible(entry.mesh)) continue;
      // Registration before scene attachment is also supported. Detached sources
      // need their ancestor chain refreshed separately from the scene traversal.
      let attached = false;
      for (let object: Object3D | null = entry.mesh; object; object = object.parent) {
        if (object === parent) { attached = true; break; }
      }
      if (!attached) entry.mesh.updateWorldMatrix(true, false);
      const position = entry.geometry.getAttribute('position');
      if (!position) continue;
      const index = entry.geometry.getIndex();
      const available = index?.count ?? position.count;
      const start = Math.max(0, Math.min(available, Math.floor(entry.geometry.drawRange.start)));
      const remaining = Math.min(available - start, entry.geometry.drawRange.count);
      const count = Math.max(0, Math.floor(remaining / 2) * 2);
      if (!count) continue;
      next.push({ ...entry, position, positionVersion: attributeVersion(position), index,
        indexVersion: index?.version ?? 0, start, count,
        matrix: new Matrix4().multiplyMatrices(inverse, entry.mesh.matrixWorld) });
    }
    visibleMeshes = next.length;
    if (unchanged(previous, next)) return stats();
    segments = 0;
    drawCalls = 0;
    const point = new Vector3();
    for (const style of styles) {
      const sources = next.filter(entry => entry.style === style);
      const count = sources.reduce((sum, entry) => sum + entry.count, 0);
      const line = lines.get(style)!;
      segments += count / 2;
      if (count) drawCalls++;
      if (unchanged(previous.filter(entry => entry.style === style), sources)) continue;
      if (!count) {
        line.visible = false;
        // Release old GPU buffers when a whole style becomes hidden.
        if (line.geometry.getAttribute('position')) {
          const old = line.geometry;
          line.geometry = new BufferGeometry();
          old.dispose();
        }
        continue;
      }
      const combined = new Float32Array(count * 3);
      let offset = 0;
      for (const entry of sources) {
        for (let i = entry.start; i < entry.start + entry.count; i++) {
          point.fromBufferAttribute(entry.position, entry.index ? entry.index.getX(i) : i).applyMatrix4(entry.matrix);
          combined[offset++] = point.x;
          combined[offset++] = point.y;
          combined[offset++] = point.z;
        }
      }
      const geometry = new BufferGeometry();
      geometry.setAttribute('position', new BufferAttribute(combined, 3));
      geometry.computeBoundingBox(); geometry.computeBoundingSphere();
      const old = line.geometry;
      line.geometry = geometry;
      old.dispose();
      line.visible = true;
    }
    previous = next;
    rebuilds++;
    return stats();
  }
  function dispose() {
    if (disposed) return;
    disposed = true;
    root.removeFromParent();
    geometryReferences.forEach((_, geometry) => geometry.dispose());
    geometryReferences.clear(); entries.clear(); previous = [];
    lines.forEach(line => line.geometry.dispose());
    new Set(Object.values(materials)).forEach(material => material.dispose());
    visibleMeshes = 0; segments = 0; drawCalls = 0;
  }
  return { root, set, remove, update, dispose, stats };
}
