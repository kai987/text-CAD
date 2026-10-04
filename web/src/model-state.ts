export type GroupId = 'F1' | 'F2' | 'stairs' | 'roof';
export type PresetId = 'exterior' | 'first' | 'second';
export type PageId = '3d' | '1f' | '2f' | 'files';
export interface ModelSettings {
  visibility: Record<GroupId, boolean>;
  cutaway: boolean;
  heightMm: number;
}

export const groups: { id: GroupId; label: string }[] = [
  { id: 'F1', label: '一层' }, { id: 'F2', label: '二层' },
  { id: 'stairs', label: '楼梯' }, { id: 'roof', label: '屋顶' },
];
export const presets: { id: PresetId; label: string; visibility: Record<GroupId, boolean> }[] = [
  { id: 'exterior', label: '完整外观', visibility: { F1: true, F2: true, stairs: true, roof: true } },
  { id: 'first', label: '一层内部', visibility: { F1: true, F2: false, stairs: true, roof: false } },
  { id: 'second', label: '二层内部', visibility: { F1: false, F2: true, stairs: true, roof: false } },
];

export function settingsForPreset(id: PresetId): ModelSettings {
  const preset = presets.find(x => x.id === id);
  if (!preset) throw new Error(`Unknown view preset: ${id}`);
  return { visibility: { ...preset.visibility }, cutaway: false, heightMm: 4200 };
}
export function activePreset(s: ModelSettings): PresetId | undefined {
  if (s.cutaway) return undefined;
  return presets.find(p => groups.every(g => p.visibility[g.id] === s.visibility[g.id]))?.id;
}
export function clampCutHeight(value: number): number {
  return Number.isFinite(value) ? Math.max(0, Math.min(8000, value)) : 4200;
}
export function initialPage(query: string): PageId {
  const p = new URLSearchParams(query);
  const view = p.get('view');
  if (view === '3d' || view === '1f' || view === '2f' || view === 'files') return view;
  const file = p.get('file') ?? '';
  if (/1FPLAN|house_1f_plan/.test(file)) return '1f';
  if (/2FPLAN|house_2f_plan/.test(file)) return '2f';
  return '3d';
}
