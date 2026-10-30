export const riverQualities = ['auto', 'smooth', 'detailed'] as const;
export type RiverQuality = typeof riverQualities[number];
export const riverQualityStorageKey = 'text-cad.river-quality';

export interface RiverQualitySettings {
  pixelRatioCap: number;
  shadowMapSize: number;
  detailPixels: number;
}

export function isRiverQuality(value: unknown): value is RiverQuality {
  return value === 'auto' || value === 'smooth' || value === 'detailed';
}

export function readRiverQuality(storage: Pick<Storage, 'getItem'> | null | undefined): RiverQuality {
  try {
    const value = storage?.getItem(riverQualityStorageKey);
    return isRiverQuality(value) ? value : 'auto';
  } catch { return 'auto'; }
}

export function saveRiverQuality(storage: Pick<Storage, 'setItem'> | null | undefined, quality: RiverQuality): void {
  try { storage?.setItem(riverQualityStorageKey, quality); }
  catch { /* Quality switching stays available when storage is blocked or full. */ }
}

export function resolveRiverQuality(quality: RiverQuality, viewportWidth: number, coarsePointer: boolean): RiverQualitySettings {
  if (quality === 'detailed') return { pixelRatioCap: 2, shadowMapSize: 2048, detailPixels: 0 };
  if (quality === 'smooth') return { pixelRatioCap: 1, shadowMapSize: 1024, detailPixels: 140 };
  const compact = !Number.isFinite(viewportWidth) || viewportWidth <= 760 || coarsePointer;
  return compact
    ? { pixelRatioCap: 1.5, shadowMapSize: 1024, detailPixels: 110 }
    : { pixelRatioCap: 2, shadowMapSize: 2048, detailPixels: 80 };
}
