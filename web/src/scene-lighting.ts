import {
  AdditiveBlending, Color, DataTexture, Group, Mesh, Object3D, RGBAFormat,
  SpotLight, Sprite, SpriteMaterial, Vector3,
} from 'three';
import type { Material, MeshStandardMaterial, Scene } from 'three';
import type { ModelSettings } from './model-state';
import { isObjectVisible } from './model-scene.ts';

export const nightScenePalette = {
  background: '#071321', outline: '#56728c', sky: '#a4c7ee', ground: '#27374b', moon: '#bcd8ff',
} as const;

/** Visual parameters travel with the named CAD diffuser, in original GLB metres/Y-up.
 * Intensity and colour are presentation settings, not calculated luminaire photometry.
 */
export interface OutdoorLightSpec {
  id: string;
  category: 'wall' | 'path' | 'garden' | 'gate' | 'indoor';
  diffuser_label: string;
  light_position_glb_m: [number, number, number];
  target_glb_m: [number, number, number];
  color_hex: string;
  beam_angle_degrees: number;
  visual_intensity: number;
  visual_range_m: number;
}

export function outdoorLightSpec(value: unknown): OutdoorLightSpec | null {
  if (!value || typeof value !== 'object') return null;
  const spec = value as OutdoorLightSpec;
  const vector = (v: unknown): v is [number, number, number] => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);
  if (typeof spec.id !== 'string' || !['wall', 'path', 'garden', 'gate', 'indoor'].includes(spec.category)
    || typeof spec.diffuser_label !== 'string' || !spec.diffuser_label.endsWith(':diffuser')
    || !vector(spec.light_position_glb_m) || !vector(spec.target_glb_m)
    || !/^#[0-9a-f]{6}$/i.test(spec.color_hex)
    || !Number.isFinite(spec.beam_angle_degrees) || spec.beam_angle_degrees <= 0 || spec.beam_angle_degrees >= 180
    || !Number.isFinite(spec.visual_intensity) || spec.visual_intensity <= 0
    || !Number.isFinite(spec.visual_range_m) || spec.visual_range_m <= 0) return null;
  return spec;
}

export function outdoorLightEnabled(diffuser: Object3D, settings: ModelSettings, emitterHeight: number): boolean {
  return settings.environment === 'night' && settings.outdoorLights && isObjectVisible(diffuser)
    && (!settings.cutaway || emitterHeight <= settings.heightMm / 1000 - 0.00005);
}

function glowTexture() {
  const size = 32, data = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const radius = Math.hypot((x + 0.5 - size / 2) / (size / 2), (y + 0.5 - size / 2) / (size / 2));
    const offset = (y * size + x) * 4;
    data.set([255, 255, 255, Math.round(Math.max(0, 1 - radius) ** 3 * 255)], offset);
  }
  const texture = new DataTexture(data, size, size, RGBAFormat);
  texture.needsUpdate = true;
  return texture;
}

interface Fixture {
  spec: OutdoorLightSpec;
  diffuser: Mesh;
  original: Material | Material[];
  materials: MeshStandardMaterial[];
  light: SpotLight;
  glow: Sprite;
}

/** Effects are siblings of the CAD root, so they never affect picking, fit or section caps. */
export function createOutdoorLighting(scene: Scene, channel: 'outdoor' | 'indoor' = 'outdoor') {
  const effects = new Group(); effects.name = `${channel}-lighting-effects`; scene.add(effects);
  const texture = glowTexture();
  const glowMaterial = new SpriteMaterial({ map: texture, color: '#ffddb2', opacity: 0.35,
    transparent: true, blending: AdditiveBlending, depthWrite: false, depthTest: true });
  const fixtures: Fixture[] = [];
  let root: Object3D | undefined;
  let disposed = false;
  function register(model: Object3D) {
    if (disposed || root) return;
    root = model;
    model.traverse(object => {
      if (!(object instanceof Mesh)) return;
      const spec = outdoorLightSpec(object.userData[channel === 'indoor' ? 'indoorLight' : 'outdoorLight']);
      if (!spec) return;
      const original = object.material;
      // GLB materials may be shared; only this actual emitter should become emissive.
      const materials = (Array.isArray(original) ? original : [original]).map(material => material.clone() as MeshStandardMaterial);
      object.material = Array.isArray(original) ? materials : materials[0];
      const light = new SpotLight(spec.color_hex, 0, spec.visual_range_m,
        spec.beam_angle_degrees * Math.PI / 360, 0.72, 2);
      light.name = `illumination:${spec.id}`;
      // One small shadow map gives the entrance physical occlusion without seven extra CAD render passes.
      light.castShadow = spec.category === 'wall';
      light.shadow.mapSize.set(768, 768);
      light.shadow.camera.near = 0.05;
      light.shadow.camera.far = spec.visual_range_m;
      light.shadow.bias = -0.0002; light.shadow.normalBias = 0.008;
      const glow = new Sprite(glowMaterial);
      glow.name = `glow:${spec.id}`;
      glow.scale.setScalar(spec.category === 'garden' ? 0.14 : 0.22);
      glow.visible = false;
      effects.add(light, light.target, glow);
      fixtures.push({ spec, diffuser: object, original, materials, light, glow });
    });
  }
  function update(settings: ModelSettings) {
    if (!root || disposed) return { total: fixtures.length, active: 0, activeIds: [] as string[], shadowLights: 0 };
    root.updateWorldMatrix(true, true);
    const activeIds: string[] = [];
    let shadowLights = 0;
    for (const fixture of fixtures) {
      const { spec, light, glow, diffuser, materials } = fixture;
      light.position.copy(root.localToWorld(new Vector3(...spec.light_position_glb_m)));
      light.target.position.copy(root.localToWorld(new Vector3(...spec.target_glb_m)));
      glow.position.copy(light.position);
      const active = channel === 'outdoor' ? outdoorLightEnabled(diffuser, settings, light.position.y)
        : settings.indoorLights && isObjectVisible(diffuser) && (!settings.cutaway || light.position.y <= settings.heightMm / 1000 - 0.00005);
      // Keep the fixed light count to avoid recompiling every model material on each switch.
      light.intensity = active ? spec.visual_intensity : 0;
      glow.visible = active;
      for (const material of materials) if (material.emissive) {
        material.emissive.copy(active ? new Color(spec.color_hex) : new Color(0x000000));
        material.emissiveIntensity = active ? 2.5 : 0;
      }
      if (active) { activeIds.push(spec.id); if (light.castShadow) shadowLights++; }
    }
    return { total: fixtures.length, active: activeIds.length, activeIds, shadowLights };
  }
  function dispose() {
    if (disposed) return;
    disposed = true;
    for (const fixture of fixtures) {
      fixture.diffuser.material = fixture.original;
      fixture.materials.forEach(material => material.dispose());
      fixture.light.dispose();
    }
    effects.removeFromParent(); texture.dispose(); glowMaterial.dispose();
    fixtures.length = 0; root = undefined;
  }
  return { register, update, dispose };
}

export const createIndoorLighting = (scene: Scene) => createOutdoorLighting(scene, 'indoor');
