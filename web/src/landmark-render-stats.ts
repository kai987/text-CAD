import { Mesh } from 'three';
import type { Object3D } from 'three';

/** Visible submissions before frustum culling; not measured GPU draw calls. */
export function landmarkVisibleGeometry(root: Object3D) {
  let meshes = 0, triangles = 0;
  root.traverseVisible(node => {
    if (!(node instanceof Mesh)) return;
    const materials = Array.isArray(node.material) ? node.material : [node.material];
    if (!materials.some(material => material.visible)) return;
    meshes++;
    const count = node.geometry.index?.count ?? node.geometry.getAttribute('position')?.count ?? 0;
    triangles += Math.floor(count / 3);
  });
  return { meshes, triangles };
}

/** Hidden source CAD meshes must not be intersected after display batching. */
export function landmarkPickableMeshes(root: Object3D): Mesh[] {
  const meshes: Mesh[] = [];
  root.traverseVisible(node => {
    if (node instanceof Mesh && (Array.isArray(node.material) ? node.material : [node.material]).some(material => material.visible)) meshes.push(node);
  });
  return meshes;
}
