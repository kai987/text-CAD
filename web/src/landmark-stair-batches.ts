import { Material, Matrix4, Mesh } from 'three';
import type { BufferGeometry, Object3D } from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import type { LandmarkId } from './landmark-copy';

interface StairBatch {
  parent: Object3D; material: Material; finish: string; schema: string; sources: Mesh[];
}
export interface LandmarkStairBatches {
  readonly sourceMeshes: number;
  readonly drawBatches: number;
  dispose(): void;
}

/** Display batching preserves every tread vertex; named downloadable CAD stays untouched. */
export function batchLandmarkStairs(root: Object3D, id: LandmarkId): LandmarkStairBatches {
  const batches: StairBatch[] = [];
  const replacements: { batch: Mesh; sources: { node: Mesh; visible: boolean }[] }[] = [];
  let disposed = false;
  if (id === 'tokyo-tower') {
    root.updateWorldMatrix(true, true);
    root.traverse(node => {
      if (!(node instanceof Mesh) || !node.parent || Array.isArray(node.material)) return;
      const name = String(node.userData.cadName ?? node.name);
      if (node.userData.landmarkRole !== 'stair_tread' && !/(?:stair.*tread|tread_)/i.test(name)) return;
      // CAD exporters may give equal finishes unique material IDs/names. Match
      // the serialized render properties while keeping custom shader hooks out.
      if (node.material.onBeforeCompile !== Material.prototype.onBeforeCompile) return;
      const { uuid: _materialId, name: _materialName, ...definition } = node.material.toJSON();
      const finish = JSON.stringify(definition);
      const schema = `${node.geometry.index ? 'indexed' : 'plain'}:${Object.keys(node.geometry.attributes)
        .map(key => { const value = node.geometry.getAttribute(key); return `${key}/${value.itemSize}/${value.normalized}/${value.array.constructor.name}`; }).sort().join(',')}`;
      let group = batches.find(batch => batch.parent === node.parent && batch.finish === finish && batch.schema === schema);
      if (!group) { group = { parent: node.parent, material: node.material, finish, schema, sources: [] }; batches.push(group); }
      group.sources.push(node);
    });
    for (const group of batches) {
      if (group.sources.length < 2) continue;
      const inverse = new Matrix4().copy(group.parent.matrixWorld).invert();
      const inputs: BufferGeometry[] = group.sources.map(node => node.geometry.clone().applyMatrix4(new Matrix4().multiplyMatrices(inverse, node.matrixWorld)));
      let geometry: BufferGeometry | null;
      try { geometry = mergeGeometries(inputs, false); }
      finally { for (const input of inputs) input.dispose(); }
      if (!geometry) continue;
      geometry.computeBoundingBox(); geometry.computeBoundingSphere();
      const batch = new Mesh(geometry, group.material);
      batch.name = `${group.parent.name}:stair_tread_display_batch_${replacements.length + 1}`;
      batch.userData.landmarkRole = 'stair_tread_batch';
      batch.userData.sourceTreads = group.sources.length;
      const sources = group.sources.map(node => ({ node, visible: node.visible }));
      // Only originally visible tread sets may be combined. Hidden originals
      // remain hidden without being accidentally revealed by the display proxy.
      if (sources.some(source => !source.visible)) { geometry.dispose(); continue; }
      for (const source of sources) source.node.visible = false;
      group.parent.add(batch); replacements.push({ batch, sources });
    }
  }
  return {
    sourceMeshes: replacements.reduce((sum, item) => sum + item.sources.length, 0),
    drawBatches: replacements.length,
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const { batch, sources } of replacements) {
        batch.removeFromParent(); batch.geometry.dispose();
        for (const source of sources) source.node.visible = source.visible;
      }
      replacements.length = 0;
    },
  };
}
