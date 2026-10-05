import { Mesh } from 'three';
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
