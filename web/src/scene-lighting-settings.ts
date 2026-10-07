import type { ModelSettings, SceneEnvironment } from './model-state';

export type SceneLightingSettings = Pick<ModelSettings, 'environment' | 'outdoorLights' | 'indoorLights'>;
export const sceneLightingStorageKey = 'text-cad.scene-lighting.v1';
const defaults: SceneLightingSettings = { environment: 'day', outdoorLights: true, indoorLights: true };

export function isSceneEnvironment(value: unknown): value is SceneEnvironment {
  return value === 'day' || value === 'night';
}

export function readSceneLighting(storage: Pick<Storage, 'getItem'>): SceneLightingSettings {
  try {
    const saved: unknown = JSON.parse(storage.getItem(sceneLightingStorageKey) ?? 'null');
    if (saved && typeof saved === 'object' && 'version' in saved && saved.version === 1 &&
      'environment' in saved && isSceneEnvironment(saved.environment) &&
      'outdoorLights' in saved && typeof saved.outdoorLights === 'boolean') {
      return { environment: saved.environment, outdoorLights: saved.outdoorLights, indoorLights: 'indoorLights' in saved && typeof saved.indoorLights === 'boolean' ? saved.indoorLights : true };
    }
  } catch { /* A blocked or malformed preference never prevents model loading. */ }
  return { ...defaults };
}

export function initialSceneLighting(query: string, storage?: Pick<Storage, 'getItem'>): SceneLightingSettings {
  const saved = storage ? readSceneLighting(storage) : { ...defaults };
  const params = new URLSearchParams(query);
  const environment = params.get('environment');
  const lights = params.get('lights');
  const indoor = params.get('indoorLights');
  return {
    environment: isSceneEnvironment(environment) ? environment : saved.environment,
    outdoorLights: lights === 'on' ? true : lights === 'off' ? false : saved.outdoorLights,
    indoorLights: indoor === 'on' ? true : indoor === 'off' ? false : saved.indoorLights,
  };
}

export function saveSceneLighting(storage: Pick<Storage, 'setItem'>, settings: SceneLightingSettings): void {
  try { storage.setItem(sceneLightingStorageKey, JSON.stringify({ version: 1, environment: settings.environment, outdoorLights: settings.outdoorLights, indoorLights: settings.indoorLights })); }
  catch { /* The in-memory control still works when storage is unavailable. */ }
}

export function sceneLightingUrl(current: string, settings: SceneLightingSettings): string {
  const url = new URL(current);
  url.searchParams.set('environment', settings.environment);
  url.searchParams.set('lights', settings.outdoorLights ? 'on' : 'off');
  url.searchParams.set('indoorLights', settings.indoorLights ? 'on' : 'off');
  return url.href;
}
