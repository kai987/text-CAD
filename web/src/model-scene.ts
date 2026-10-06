import { Box3, Mesh, Vector3 } from 'three';
import type { Object3D } from 'three';
import type { GLTF } from 'three/addons/loaders/GLTFLoader.js';
import { modelLayouts } from './model-state.ts';
import type { ModelLayout, ModelPartId } from './model-state';

export interface ModelSelection { id: ModelPartId; name: string; label: string }

export function isObjectVisible(object: Object3D): boolean {
  for (let current: Object3D | null = object; current; current = current.parent) {
    if (!current.visible) return false;
  }
  return true;
}

// GLTFLoader sanitizes punctuation in names. Retain the original CAD names via node indices.
export function bindCadNodes(gltf: GLTF): Map<string, Object3D> {
  const objects = new Map<string, Object3D>();
  gltf.scene.traverse(object => {
    const index = gltf.parser.associations.get(object)?.nodes;
    const name: unknown = index === undefined ? undefined : gltf.parser.json.nodes[index]?.name;
    if (typeof name === 'string') {
      object.userData.cadName = name;
      objects.set(name, object);
    }
  });
  return objects;
}

/** Keep architectural heights relative to the original first-floor finished datum.
 * Site solids can extend below the floor and must not redefine the cut-plane origin.
 */
export function centerModelAtFloorDatum(root: Object3D, objects: ReadonlyMap<string, Object3D>): boolean {
  const floor = objects.get('F1:floor_slab');
  if (!(floor instanceof Mesh)) return false;
  root.updateWorldMatrix(true, true);
  const datum = new Box3().setFromObject(floor).max.y;
  const bounds = new Box3().setFromObject(root);
  if (bounds.isEmpty() || !Number.isFinite(datum)) return false;
  const center = bounds.getCenter(new Vector3());
  root.position.add(new Vector3(-center.x, -datum, -center.z));
  root.updateWorldMatrix(true, true);
  return true;
}

export function selectionFor(object: Object3D, layout: ModelLayout = modelLayouts.house): ModelSelection | null {
  const name = String(object.userData.cadName ?? object.name);
  for (let current: Object3D | null = object; current; current = current.parent) {
    const originalName = current.userData.cadName;
    const part = layout.parts.find(item => item.id === originalName);
    if (part) return { id: part.id, name, label: `${layout.groups.find(g => g.id === part.group)!.label} · ${part.label}` };
    const group = layout.groups.find(item => item.id === originalName);
    if (group) return { id: group.id, name, label: group.label };
  }
  return null;
}

export function visibleMeshes(object: Object3D): Mesh[] {
  const meshes: Mesh[] = [];
  object.traverse(child => { if (child instanceof Mesh && isObjectVisible(child)) meshes.push(child); });
  return meshes;
}
