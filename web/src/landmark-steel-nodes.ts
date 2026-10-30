import { Box3, Mesh, Vector3 } from 'three';
import type { Object3D, OrthographicCamera } from 'three';
import { isObjectVisible } from './model-scene.ts';
import type { Locale } from './localization';

export type SteelMicroMode = 'auto' | 'on' | 'off';
export interface LandmarkSteelNode {
  id: string; names: Record<Locale, string>; anchor_mm: readonly [number, number, number];
  member_names: readonly string[]; part_names: readonly string[]; type: string;
  local_frame?: { normal: readonly [number, number, number] };
}
export interface LandmarkSteelDetails {
  readonly catalog: readonly LandmarkSteelNode[];
  bounds(id: string): Box3 | null;
  direction(id: string): Vector3;
  apply(camera: OrthographicCamera, mode: SteelMicroMode): { microMeshes: number; visibleMicroMeshes: number };
  dispose(): void;
}

/** Validate the exported catalog before it supplies UI text or CAD references. */
export function readLandmarkSteelNodes(value: unknown): readonly LandmarkSteelNode[] {
  if (!Array.isArray(value)) throw new Error('Missing steel-node catalog.');
  const ids = new Set<string>();
  return value.map(item => {
    if (!item || typeof item !== 'object' || typeof item.id !== 'string' || !/^TT-N\d{2}$/.test(item.id)
      || ids.has(item.id) || typeof item.type !== 'string' || !item.type.trim()
      || !['zh', 'ja', 'en'].every(locale => typeof item.names?.[locale] === 'string' && item.names[locale].trim())
      || !Array.isArray(item.anchor_mm) || item.anchor_mm.length !== 3 || !item.anchor_mm.every(Number.isFinite)
      || !['member_names', 'part_names'].every(key => Array.isArray(item[key]) && item[key].length > 0
        && item[key].every((name: unknown) => typeof name === 'string' && name.trim()))) {
      throw new Error('Invalid steel-node catalog.');
    }
    ids.add(item.id);
    const normal = item.local_frame?.normal;
    return { id: item.id, names: { zh: item.names.zh, ja: item.names.ja, en: item.names.en },
      anchor_mm: [...item.anchor_mm] as [number, number, number], type: item.type,
      ...(Array.isArray(normal) && normal.length === 3 && normal.every(Number.isFinite)
        ? { local_frame: { normal: [...normal] as [number, number, number] } } : {}),
      member_names: [...item.member_names], part_names: [...item.part_names] };
  });
}

/** Rivets keep their original named CAD meshes; only their display visibility changes. */
export function bindLandmarkSteelDetails(nodes: ReadonlyMap<string, Object3D>, catalog: readonly LandmarkSteelNode[], root?: Object3D): LandmarkSteelDetails {
  const regions = new Map<string, Mesh[]>();
  const micro: { node: Mesh; originalVisible: boolean; nodeId: string }[] = [];
  const seen = new Set<Mesh>();
  let disposed = false;
  for (const entry of catalog) {
    const parts = entry.part_names.map(name => nodes.get(name));
    if (parts.some(node => !(node instanceof Mesh)) || entry.member_names.some(name => !nodes.has(name))) {
      throw new Error(`Steel-node CAD references are incomplete: ${entry.id}`);
    }
    const meshes = parts as Mesh[];
    regions.set(entry.id, meshes);
    for (const node of meshes) {
      if (seen.has(node)) throw new Error(`Steel-node part is referenced more than once: ${entry.id}`);
      seen.add(node);
      if (node.userData.steelNodeId !== entry.id) throw new Error(`Steel-node CAD tag does not match: ${entry.id}`);
      // Explicit detail metadata excludes lamps, glazing and ordinary plates.
      if (node.userData.steelMicro === true && node.userData.steelDetailKind === 'rivet' && node.userData.landmarkRole === 'rivet_head') {
        micro.push({ node, originalVisible: node.visible, nodeId: entry.id });
      }
    }
  }
  function bounds(id: string) {
    if (disposed) return null;
    const parts = regions.get(id);
    if (!parts) return null;
    const region = new Box3();
    for (const node of parts) { node.updateWorldMatrix(true, false); region.expandByObject(node); }
    return region.isEmpty() ? null : region.expandByScalar(1);
  }
  const projected = new Vector3();
  return {
    catalog, bounds,
    direction(id) {
      const entry = catalog.find(entry => entry.id === id);
      if (entry?.type === 'base') {
        // Look inward/down from outside the tower footprint, rather than
        // following the sloping leg from an almost vertical camera position.
        const direction = new Vector3(entry.anchor_mm[0], 0, -entry.anchor_mm[1]);
        if (direction.lengthSq() < 1e-12) direction.set(1, 0, 0);
        direction.normalize().multiplyScalar(1.2).add(new Vector3(0, .7, 0)).normalize();
        if (root) { root.updateWorldMatrix(true, false); direction.transformDirection(root.matrixWorld); }
        return direction;
      }
      const normal = entry?.local_frame?.normal;
      const direction = normal ? new Vector3(normal[0], normal[2], -normal[1]) : new Vector3(1, .4, 1);
      if (root) { root.updateWorldMatrix(true, false); direction.transformDirection(root.matrixWorld); }
      return direction.add(new Vector3(.12, .2, .12)).normalize();
    },
    apply(camera, mode) {
      if (disposed) return { microMeshes: 0, visibleMicroMeshes: 0 };
      camera.updateMatrixWorld();
      const worldHeight = (camera.top - camera.bottom) / camera.zoom;
      const nearby = new Map<string, boolean>();
      if (mode === 'auto' && worldHeight <= 24) for (const entry of catalog) {
        const region = bounds(entry.id);
        if (!region) continue;
        region.getCenter(projected).project(camera);
        nearby.set(entry.id, Math.abs(projected.x) <= 1.2 && Math.abs(projected.y) <= 1.2 && projected.z >= -1 && projected.z <= 1);
      }
      let visibleMicroMeshes = 0;
      for (const item of micro) {
        item.node.visible = item.originalVisible && (mode === 'on' || mode === 'auto' && nearby.get(item.nodeId) === true);
        if (isObjectVisible(item.node)) visibleMicroMeshes++;
      }
      return { microMeshes: micro.length, visibleMicroMeshes };
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const item of micro) item.node.visible = item.originalVisible;
      micro.length = 0; regions.clear(); seen.clear();
    },
  };
}
