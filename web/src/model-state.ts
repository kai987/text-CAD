export type ModelId = 'house' | 'apartment';
export type GroupId = 'F1' | 'F2' | 'stairs' | 'roof' | 'ceiling' | 'balcony';
export type FloorId = 'F1' | 'F2';
export type PartKind = 'floor_slab' | 'external_walls' | 'partition_walls' | 'doors' | 'windows' | 'storage_fixtures' | 'fixtures' | 'furniture';
export type PartId = `${FloorId}:${PartKind}`;
export type ModelPartId = PartId | GroupId;
export type PresetId = 'exterior' | 'first' | 'second' | 'interior';
export type PageId = '3d' | '1f' | '2f' | 'files';
export interface ModelSettings {
  visibility: Partial<Record<GroupId, boolean>>;
  partVisibility: Partial<Record<PartId, boolean>>;
  cutaway: boolean;
  heightMm: number;
}
interface ModelGroup { id: GroupId; label: string }
interface ModelPart { id: PartId; group: FloorId; label: string }
interface ViewPreset { id: PresetId; label: string; visibility: ModelSettings['visibility']; cutaway?: boolean }
export interface ModelLayout {
  id: ModelId;
  groups: ModelGroup[];
  parts: ModelPart[];
  presets: ViewPreset[];
  defaultPreset: PresetId;
  maxCutHeight: number;
  defaultCutHeight: number;
  pages: PageId[];
}

export const groups: ModelGroup[] = [
  { id: 'F1', label: '一层' }, { id: 'F2', label: '二层' },
  { id: 'stairs', label: '楼梯' }, { id: 'roof', label: '屋顶' },
];
const partKinds: { id: PartKind; label: string }[] = [
  { id: 'floor_slab', label: '楼板' }, { id: 'external_walls', label: '外墙' },
  { id: 'partition_walls', label: '内隔墙' }, { id: 'doors', label: '门' },
  { id: 'windows', label: '窗' }, { id: 'storage_fixtures', label: '收纳柜' },
  { id: 'fixtures', label: '厨卫设备' }, { id: 'furniture', label: '家具' },
];
export const parts: ModelPart[] = (['F1', 'F2'] as const)
  .flatMap(group => partKinds.map(kind => ({ id: `${group}:${kind.id}` as PartId, group, label: kind.label })));
export const presets: ViewPreset[] = [
  { id: 'exterior', label: '完整外观', visibility: { F1: true, F2: true, stairs: true, roof: true } },
  { id: 'first', label: '一层内部', visibility: { F1: true, F2: false, stairs: true, roof: false } },
  { id: 'second', label: '二层内部', visibility: { F1: false, F2: true, stairs: true, roof: false } },
];
export const modelLayouts: Record<ModelId, ModelLayout> = {
  house: { id: 'house', groups, parts, presets, defaultPreset: 'exterior', maxCutHeight: 8000, defaultCutHeight: 4200, pages: ['3d', '1f', '2f', 'files'] },
  apartment: {
    id: 'apartment',
    groups: [{ id: 'F1', label: '公寓室内' }, { id: 'ceiling', label: '顶板' }, { id: 'balcony', label: '阳台' }],
    parts: parts.filter(part => part.group === 'F1'),
    presets: [
      { id: 'exterior', label: '完整户型', visibility: { F1: true, ceiling: true, balcony: true } },
      { id: 'interior', label: '室内剖视', visibility: { F1: true, ceiling: false, balcony: true }, cutaway: true },
    ],
    defaultPreset: 'interior', maxCutHeight: 2800, defaultCutHeight: 1800, pages: ['3d', '1f', 'files'],
  },
};

function allPartVisibility(visible: boolean, layout: ModelLayout): ModelSettings['partVisibility'] {
  return Object.fromEntries(layout.parts.map(part => [part.id, visible]));
}
export function isPartVisible(s: ModelSettings, id: PartId, layout = modelLayouts.house): boolean {
  const part = layout.parts.find(part => part.id === id);
  return !!part && !!s.visibility[part.group] && !!s.partVisibility[id];
}
export function groupVisibilityState(s: ModelSettings, id: GroupId, layout = modelLayouts.house): 'all' | 'some' | 'none' {
  if (!s.visibility[id] || !layout.groups.some(group => group.id === id)) return 'none';
  const children = layout.parts.filter(part => part.group === id);
  if (children.length === 0) return 'all';
  const count = children.filter(part => s.partVisibility[part.id]).length;
  return count === children.length ? 'all' : count === 0 ? 'none' : 'some';
}
export function setGroupVisible(s: ModelSettings, id: GroupId, visible: boolean, layout = modelLayouts.house): ModelSettings {
  if (!layout.groups.some(group => group.id === id)) return s;
  const partVisibility = { ...s.partVisibility };
  if (visible) for (const part of layout.parts) if (part.group === id) partVisibility[part.id] = true;
  return { ...s, visibility: { ...s.visibility, [id]: visible }, partVisibility };
}
export function setPartVisible(s: ModelSettings, id: PartId, visible: boolean, layout = modelLayouts.house): ModelSettings {
  const part = layout.parts.find(part => part.id === id);
  if (!part) return s;
  return {
    ...s, visibility: { ...s.visibility, ...(visible ? { [part.group]: true } : {}) },
    partVisibility: { ...s.partVisibility, [id]: visible },
  };
}
export function isolatePart(s: ModelSettings, id: ModelPartId, layout = modelLayouts.house): ModelSettings {
  const part = layout.parts.find(part => part.id === id);
  const group = part?.group ?? id as GroupId;
  if (!layout.groups.some(item => item.id === group)) return s;
  const partVisibility = allPartVisibility(false, layout);
  for (const item of layout.parts) if (part ? item.id === part.id : item.group === group) partVisibility[item.id] = true;
  return {
    ...s, visibility: Object.fromEntries(layout.groups.map(item => [item.id, item.id === group])),
    partVisibility, cutaway: false,
  };
}
export function anyVisible(s: ModelSettings, layout = modelLayouts.house): boolean {
  return layout.groups.some(group => groupVisibilityState(s, group.id, layout) !== 'none');
}
export function furnitureVisibilityState(s: ModelSettings, layout = modelLayouts.house): 'all' | 'some' | 'none' {
  const furniture = layout.parts.filter(part => part.id.endsWith(':furniture'));
  const count = furniture.filter(part => s.partVisibility[part.id]).length;
  return count === 0 ? 'none' : count === furniture.length ? 'all' : 'some';
}
export function setFurnitureVisible(s: ModelSettings, visible: boolean, layout = modelLayouts.house): ModelSettings {
  const partVisibility = { ...s.partVisibility };
  for (const part of layout.parts) if (part.id.endsWith(':furniture')) partVisibility[part.id] = visible;
  // Do not reveal a hidden storey, change the cut plane or move the camera.
  return { ...s, partVisibility };
}
export function settingsForPreset(id: PresetId, layout = modelLayouts.house, previous?: ModelSettings): ModelSettings {
  const preset = layout.presets.find(x => x.id === id);
  if (!preset) throw new Error(`Unknown view preset: ${id}`);
  const partVisibility = allPartVisibility(true, layout);
  if (previous) for (const part of layout.parts) {
    if (part.id.endsWith(':furniture')) partVisibility[part.id] = previous.partVisibility[part.id] ?? true;
  }
  return { visibility: { ...preset.visibility }, partVisibility, cutaway: preset.cutaway ?? false, heightMm: layout.defaultCutHeight };
}
export function activePreset(s: ModelSettings, layout = modelLayouts.house): PresetId | undefined {
  if (layout.parts.some(part => !part.id.endsWith(':furniture') && !s.partVisibility[part.id])) return undefined;
  return layout.presets.find(p => (p.cutaway ?? false) === s.cutaway &&
    layout.groups.every(g => p.visibility[g.id] === s.visibility[g.id]))?.id;
}
export function clampCutHeight(value: number, layout = modelLayouts.house): number {
  return Number.isFinite(value) ? Math.max(0, Math.min(layout.maxCutHeight, value)) : layout.defaultCutHeight;
}
export function initialModel(query: string): ModelId {
  const params = new URLSearchParams(query);
  return params.get('model') === 'apartment' || /apartment_2ldk/.test(params.get('file') ?? '') ? 'apartment' : 'house';
}
export function initialPreset(query: string, layout = modelLayouts.house): PresetId {
  return layout.presets.find(preset => preset.id === new URLSearchParams(query).get('mode'))?.id ?? layout.defaultPreset;
}
export function initialPage(query: string, layout = modelLayouts.house): PageId {
  const p = new URLSearchParams(query);
  const view = p.get('view') as PageId | null;
  if (view && layout.pages.includes(view)) return view;
  if (view === '2f' && layout.id === 'apartment') return '1f';
  const file = p.get('file') ?? '';
  if (/1FPLAN|house_1f_plan|apartment_2ldk_plan/.test(file)) return '1f';
  if (/2FPLAN|house_2f_plan/.test(file) && layout.pages.includes('2f')) return '2f';
  return '3d';
}

export function modelUrl(current: string, page: PageId, model: ModelId): string {
  const url = new URL(current);
  const section = url.searchParams.get('section');
  url.search = '';
  url.searchParams.set('view', modelLayouts[model].pages.includes(page) ? page : '1f');
  if (model === 'apartment') url.searchParams.set('model', model);
  if (section === 'wasm') url.searchParams.set('section', section);
  return url.href;
}
