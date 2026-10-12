import { createHash } from 'node:crypto';
import { EdgesGeometry, Mesh } from 'three';
import { loadGlbGeometry } from './glb-geometry.mjs';
import { createCadOutlineGeometry } from '../src/cad-outlines.ts';
import { encodeStaticOutlineCache, outlineKindForCadName, STATIC_OUTLINE_ANGLE } from '../src/static-outline-cache.ts';

export async function buildStaticOutlines(bytes) {
  const sourceSha256 = createHash('sha256').update(bytes).digest('hex');
  const gltf = await loadGlbGeometry(bytes);
  const entries = [];
  const byGeometry = new WeakMap();
  const geometries = new Set();
  const materials = new Set();
  gltf.scene.traverse(object => {
    if (!(object instanceof Mesh)) return;
    geometries.add(object.geometry);
    (Array.isArray(object.material) ? object.material : [object.material]).forEach(material => materials.add(material));
    const node = gltf.parser.associations.get(object)?.nodes;
    if (node === undefined) throw new Error('Static outline mesh has no original GLB node.');
    const name = gltf.parser.json.nodes[node]?.name ?? '';
    const kind = outlineKindForCadName(name);
    let outlines = byGeometry.get(object.geometry);
    if (!outlines) { outlines = new Map(); byGeometry.set(object.geometry, outlines); }
    let positions = outlines.get(kind);
    if (!positions) {
      const edges = kind === 'cad' ? createCadOutlineGeometry(object.geometry, STATIC_OUTLINE_ANGLE)
        : new EdgesGeometry(object.geometry, STATIC_OUTLINE_ANGLE);
      positions = new Float32Array(edges.getAttribute('position')?.array ?? []);
      edges.dispose(); outlines.set(kind, positions);
    }
    entries.push({ node, kind, positions });
  });
  geometries.forEach(geometry => geometry.dispose()); materials.forEach(material => material.dispose());
  return { bytes: Buffer.from(encodeStaticOutlineCache(sourceSha256, entries)), entries: entries.length };
}
