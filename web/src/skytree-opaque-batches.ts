import { Box3, BufferAttribute, InstancedMesh, Material, Matrix4, Mesh, MeshStandardMaterial, Object3D, SkinnedMesh, Vector3 } from 'three';
import type { BufferGeometry } from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export interface SkytreeOpaqueBatches {
  readonly sourceMeshes: number;
  readonly drawBatches: number;
  dispose(): void;
}
interface Bucket {
  parent: Object3D; group: 'structure' | 'core'; material: MeshStandardMaterial;
  finish: string; schema: string; band: number; renderState: string; sources: Mesh[];
}
interface Replacement { batch: Mesh; sources: { node: Mesh; visible: boolean }[] }

function visible(node: Object3D): boolean {
  for (let current: Object3D | null = node; current; current = current.parent) if (!current.visible) return false;
  return true;
}
function groupFor(node: Mesh): 'structure' | 'core' | null {
  const group = node.userData.landmarkGroup ?? String(node.userData.cadName ?? node.name).split(':')[0];
  return group === 'structure' || group === 'core' ? group : null;
}
function eligibleMaterial(node: Mesh): MeshStandardMaterial | null {
  if (Array.isArray(node.material) || !(node.material instanceof MeshStandardMaterial)) return null;
  const material = node.material;
  const role = String(node.userData.landmarkRole ?? '');
  const name = String(node.userData.cadName ?? node.name).toLowerCase();
  if (role === 'light_lens' || role === 'obstruction_light_lens' || role === 'glazing'
      || /(?:glazing|light_lens)/.test(name)) return null;
  if (!material.visible || material.transparent || material.opacity !== 1 || material.alphaTest !== 0 || material.alphaHash
      || material.emissiveMap || material.emissive.r !== 0 || material.emissive.g !== 0 || material.emissive.b !== 0
      || ('transmission' in material && material.transmission !== 0)) return null;
  if (material.onBeforeRender !== Material.prototype.onBeforeRender
      || material.onBeforeCompile !== Material.prototype.onBeforeCompile
      || material.customProgramCacheKey !== Material.prototype.customProgramCacheKey
      || node.onBeforeRender !== Object3D.prototype.onBeforeRender
      || node.onAfterRender !== Object3D.prototype.onAfterRender
      || node.customDepthMaterial || node.customDistanceMaterial) return null;
  return material;
}
function geometrySchema(geometry: BufferGeometry): string | null {
  if (!geometry.getAttribute('position')
      || Object.values(geometry.morphAttributes).some(values => values.length)) return null;
  const attributes = Object.keys(geometry.attributes).sort();
  for (const name of attributes) {
    const attribute = geometry.getAttribute(name);
    if (!(attribute instanceof BufferAttribute) || 'isInstancedBufferAttribute' in attribute) return null;
  }
  const total = geometry.index?.count ?? geometry.getAttribute('position').count;
  if (geometry.drawRange.start !== 0 || (geometry.drawRange.count !== Infinity && geometry.drawRange.count !== total)) return null;
  return `${geometry.index ? 'indexed' : 'plain'}:${attributes.map(name => {
    const attribute = geometry.getAttribute(name);
    return `${name}/${attribute.itemSize}/${attribute.normalized}/${attribute.array.constructor.name}`;
  }).join(',')}`;
}

/** Runtime display proxies only. Compute CAD bounds and camera regions before calling. */
export function batchSkytreeOpaque(root: Object3D, id: string): SkytreeOpaqueBatches {
  const buckets: Bucket[] = [], replacements: Replacement[] = [];
  let disposed = false;
  if (id === 'tokyo-skytree') {
    root.updateWorldMatrix(true, true);
    const finishes = new WeakMap<Material, string>();
    root.traverse(node => {
      if (!(node instanceof Mesh) || node instanceof InstancedMesh || node instanceof SkinnedMesh
          || !node.parent || node.children.length || !node.frustumCulled || !visible(node)) return;
      const group = groupFor(node), material = eligibleMaterial(node), schema = geometrySchema(node.geometry);
      if (!group || !material || !schema || node.matrixWorld.determinant() <= 0 || node.parent.matrixWorld.determinant() <= 0) return;
      // Parent-local baked vertices retain every source triangle. World-Y bands
      // keep local views from drawing an entire tower-sized combined mesh.
      const bounds = new Box3().setFromBufferAttribute(node.geometry.getAttribute('position') as BufferAttribute).applyMatrix4(node.matrixWorld);
      const band = Math.floor(bounds.getCenter(new Vector3()).y / 50);
      if (!Number.isFinite(band)) return;
      let finish = finishes.get(material);
      if (finish === undefined) {
        const { uuid: _uuid, name: _name, ...definition } = material.toJSON();
        finish = JSON.stringify(definition); finishes.set(material, finish);
      }
      const renderState = `${node.castShadow}/${node.receiveShadow}/${node.renderOrder}/${node.layers.mask}`;
      let bucket = buckets.find(value => value.parent === node.parent && value.group === group
        && value.finish === finish && value.schema === schema && value.band === band && value.renderState === renderState);
      if (!bucket) {
        bucket = { parent: node.parent, group, material, finish, schema, band, renderState, sources: [] };
        buckets.push(bucket);
      }
      bucket.sources.push(node);
    });
    for (const bucket of buckets) {
      if (bucket.sources.length < 2) continue;
      const inputs: BufferGeometry[] = [];
      let geometry: BufferGeometry | null = null;
      try {
        const inverse = new Matrix4().copy(bucket.parent.matrixWorld).invert();
        for (const node of bucket.sources) inputs.push(node.geometry.clone()
          .applyMatrix4(new Matrix4().multiplyMatrices(inverse, node.matrixWorld)));
        geometry = mergeGeometries(inputs, false);
      } catch { /* An optional display optimization may fall back to original meshes. */ }
      finally { for (const input of inputs) input.dispose(); }
      if (!geometry) continue;
      geometry.computeBoundingBox(); geometry.computeBoundingSphere();
      const batch = new Mesh(geometry, bucket.material), original = bucket.sources[0];
      batch.name = `${bucket.group}:opaque_display_batch_${replacements.length + 1}`;
      batch.userData = { cadName: batch.name, landmarkGroup: bucket.group,
        landmarkRole: 'opaque_display_batch', sourceMeshes: bucket.sources.length };
      batch.castShadow = original.castShadow; batch.receiveShadow = original.receiveShadow;
      batch.renderOrder = original.renderOrder; batch.layers.mask = original.layers.mask;
      const sources = bucket.sources.map(node => ({ node, visible: node.visible }));
      for (const source of sources) source.node.visible = false;
      bucket.parent.add(batch); replacements.push({ batch, sources });
    }
  }
  return {
    sourceMeshes: replacements.reduce((total, replacement) => total + replacement.sources.length, 0),
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
