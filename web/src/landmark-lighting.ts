import { Color, Mesh } from 'three';
import type { Material, MeshStandardMaterial, Object3D } from 'three';
import { isObjectVisible } from './model-scene.ts';
import type { LandmarkGroupId, LandmarkId } from './landmark-copy';

type LightRole = 'warm-lens' | 'obstruction-lens' | 'lit-window' | 'unlit';
interface Finish {
  node: Mesh; material: MeshStandardMaterial; role: LightRole;
  originalColor: Color; originalIntensity: number;
}
export interface LandmarkLightingStats {
  mode: 'local-fixtures';
  warmFixtures: number; coolFixtures: number; obstructionFixtures: number; litWindows: number;
}
export interface LandmarkMaterialLighting {
  apply(night: boolean): LandmarkLightingStats;
  dispose(): void;
}

export interface LandmarkLocalLightSpec {
  kind: 'spot' | 'point'; channel: 'uplights' | 'entry' | 'decks';
  color: string; intensity: number; distance: number;
  position: readonly [number, number, number]; target?: readonly [number, number, number];
}

/** Metre-based display-light assumptions; CAD remains the source of visible fixtures. */
export function landmarkLocalLightLayout(id: LandmarkId): readonly LandmarkLocalLightSpec[] {
  if (id === 'tokyo-tower') {
    const lights: LandmarkLocalLightSpec[] = [];
    for (const x of [-1, 1]) for (const z of [-1, 1]) lights.push({
      kind: 'spot', channel: 'uplights', color: '#ffad65', intensity: 50000, distance: 220,
      position: [x * 33, 1.8, z * 33], target: [x * 24, 65, z * 24],
    });
    // R07 FootTown's front is GLB Z=22m; keep its display source outside.
    return [...lights, { kind: 'point', channel: 'entry', color: '#ffd2a0', intensity: 1000, distance: 32, position: [0, 4.5, 24] }];
  }
  const lights: LandmarkLocalLightSpec[] = [];
  // Alternate fixtures on the six-lamp CAD plaza ring share three real sources.
  for (const angle of [0, 2 * Math.PI / 3, 4 * Math.PI / 3]) lights.push({
    kind: 'spot', channel: 'uplights', color: '#9bdcff', intensity: 180000, distance: 480,
    position: [Math.cos(angle) * 45, 1.33, Math.sin(angle) * 45],
    target: [Math.cos(angle) * 12, 180, Math.sin(angle) * 12],
  });
  return [...lights,
    { kind: 'point', channel: 'entry', color: '#d5f2ff', intensity: 1000, distance: 40, position: [0, 4.5, 20.5] },
    { kind: 'point', channel: 'decks', color: '#b4e8ff', intensity: 2500, distance: 60, position: [0, 341, 21] },
    { kind: 'point', channel: 'decks', color: '#c7edff', intensity: 1800, distance: 45, position: [0, 447, 13] },
  ];
}

export function landmarkLocalLightVisibility(id: LandmarkId, night: boolean,
  visible: Readonly<Record<LandmarkGroupId, boolean>>, ready: boolean) {
  const active = ready && night;
  return { uplights: active && visible.base && visible.structure, entry: active && visible.base,
    decks: active && id === 'tokyo-skytree' && visible.decks };
}

/** Stable sparse window lighting is an appearance study, not occupancy data. */
export function landmarkLightRole(name: string, metadataRole?: unknown): LightRole {
  const lower = name.toLowerCase();
  const explicit = typeof metadataRole === 'string' ? metadataRole.toLowerCase() : '';
  if (explicit === 'obstruction_light_lens' || lower.includes('obstruction_light_lens')) return 'obstruction-lens';
  if (explicit === 'light_lens' || lower.includes('light_lens')) return 'warm-lens';
  if (explicit === 'glazing' || lower.includes('glazing')) {
    let hash = 0;
    for (const letter of lower) hash = (Math.imul(hash, 31) + letter.charCodeAt(0)) | 0;
    return (hash >>> 0) % 3 === 0 ? 'lit-window' : 'unlit';
  }
  return 'unlit';
}

/** Clone only local emissive finishes so one lit lens cannot light its frame. */
export function bindLandmarkMaterialLighting(root: Object3D, id: LandmarkId): LandmarkMaterialLighting {
  const finishes: Finish[] = [];
  const replacements: { node: Mesh; original: Material | Material[] }[] = [];
  const owned = new Set<MeshStandardMaterial>();
  let disposed = false;
  root.traverse(node => {
    if (!(node instanceof Mesh)) return;
    const name = String(node.userData.cadName ?? node.name);
    const role = landmarkLightRole(name, node.userData.landmarkRole);
    const materials: Material[] = Array.isArray(node.material) ? node.material : [node.material];
    if (role === 'unlit') return;
    const replacement = materials.map(item => {
      const original = item as MeshStandardMaterial;
      if (!original.isMeshStandardMaterial) return item;
      const material = original.clone(); owned.add(material);
      finishes.push({ node, material, role, originalColor: material.emissive.clone(), originalIntensity: material.emissiveIntensity });
      return material;
    });
    replacements.push({ node, original: node.material });
    node.material = Array.isArray(node.material) ? replacement : replacement[0];
  });
  return {
    apply(night) {
      const stats: LandmarkLightingStats = { mode: 'local-fixtures', warmFixtures: 0, coolFixtures: 0, obstructionFixtures: 0, litWindows: 0 };
      if (disposed) return stats;
      for (const finish of finishes) {
        const { material, role, node } = finish;
        if (!night || !isObjectVisible(node)) {
          material.emissive.copy(finish.originalColor); material.emissiveIntensity = finish.originalIntensity;
          continue;
        }
        if (role === 'obstruction-lens') {
          material.emissive.set('#ff3020'); material.emissiveIntensity = 2.5; stats.obstructionFixtures++;
        } else if (role === 'warm-lens') {
          material.emissive.set(id === 'tokyo-tower' ? '#ffb064' : '#b4e8ff'); material.emissiveIntensity = 1.7;
          if (id === 'tokyo-tower') stats.warmFixtures++; else stats.coolFixtures++;
        } else {
          material.emissive.set(id === 'tokyo-tower' ? '#ffd6a0' : '#c7edff'); material.emissiveIntensity = .22; stats.litWindows++;
        }
      }
      return stats;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      // Restore loaded materials before the viewer disposes the model itself.
      for (const { node, original } of replacements) node.material = original;
      for (const material of owned) material.dispose();
      finishes.length = 0; replacements.length = 0; owned.clear();
    },
  };
}
