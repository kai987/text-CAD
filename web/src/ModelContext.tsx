import { createContext, useContext, useEffect, useMemo } from 'react';
import type { ReactNode } from 'react';
import { modelLayouts } from './model-state';
import type { ModelId, ModelLayout } from './model-state';
import { modelCopy } from './model-copy';
import type { Messages } from './localization';
import { useLanguage } from './LanguageContext';
import { house, downloadFiles } from './data';
import apartment from './apartment-data.json';
import housePreview from './plan-preview-metadata.json';
import apartmentPreview from './apartment-preview-metadata.json';
import { loadPlanVectors } from './plan-vectors';

interface ModelManifest {
  parameters: { width: number; depth: number; storey_height: number; clear_height?: number };
  drawingRevision: string;
  modelRevision: string;
  floors: { floor: number; rooms: { id: string; name: string; area: number; size: string }[] }[];
  areas?: { outline: number; interior: number; balcony: number };
}
interface ModelConfig {
  layout: ModelLayout;
  data: ModelManifest;
  glb: string;
  pdf: string;
  plans: Partial<Record<1 | 2, string>>;
  previews: { floor: number; path: string; fullViewBox: number[]; planViewBox: number[] }[];
  fallback: string;
  source: string;
  downloads: { id: keyof Messages['downloads']['files']; path: string; type: string }[];
}
export const models: Record<ModelId, ModelConfig> = {
  house: {
    layout: modelLayouts.house, data: house, glb: 'GLB/house_3d.glb',
    pdf: 'output/pdf/house_floor_plans_R02_JP.pdf',
    plans: { 1: 'DXF/001D0PL2-1FPLAN.DXF', 2: 'DXF/002D0PL2-2FPLAN.DXF' },
    previews: housePreview.floors, fallback: 'output/review/house_3d_iso.png',
    source: 'src/house_3d.py', downloads: [...downloadFiles],
  },
  apartment: {
    layout: modelLayouts.apartment, data: apartment, glb: 'GLB/apartment_2ldk.glb',
    pdf: 'output/pdf/apartment_2ldk_plan.pdf', plans: { 1: 'DXF/apartment_2ldk_plan.dxf' },
    previews: apartmentPreview.floors, fallback: 'output/review/apartment_2ldk_iso.png',
    source: 'src/apartment_2ldk.py',
    downloads: [
      { id: 'glb', path: 'GLB/apartment_2ldk.glb', type: 'GLB' },
      { id: 'step', path: 'STEP/apartment_2ldk.step', type: 'STEP' },
      { id: 'first', path: 'DXF/apartment_2ldk_plan.dxf', type: 'DXF' },
      { id: 'pdf', path: 'output/pdf/apartment_2ldk_plan.pdf', type: 'PDF' },
      { id: 'manifest', path: 'output/review/apartment_2ldk_manifest.json', type: 'JSON' },
    ],
  },
};
const ModelContext = createContext<(ModelConfig & { copy: Messages }) | null>(null);
export function ModelProvider({ id, children }: { id: ModelId; children: ReactNode }) {
  const { locale, copy } = useLanguage();
  const value = useMemo(() => ({ ...models[id], copy: modelCopy(copy, locale, id) }), [id, copy, locale]);
  useEffect(() => {
    // A missing floor must not prevent the other plans or the model from loading.
    void Promise.allSettled(models[id].previews.map(preview => loadPlanVectors(preview.path)));
  }, [id]);
  return <ModelContext.Provider value={value}>{children}</ModelContext.Provider>;
}
export function useModel() {
  const value = useContext(ModelContext);
  if (!value) throw new Error('ModelProvider is required.');
  return value;
}
