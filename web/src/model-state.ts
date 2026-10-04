export type GroupId = 'F1' | 'F2' | 'stairs' | 'roof';
export type FloorId = 'F1' | 'F2';
export type PartKind = 'floor_slab' | 'external_walls' | 'partition_walls' | 'doors' | 'windows' | 'storage_fixtures';
export type PartId = `${FloorId}:${PartKind}`;
export type ModelPartId = PartId | GroupId;
export type PresetId = 'exterior' | 'first' | 'second';
export type PageId = '3d' | '1f' | '2f' | 'files';
export interface ModelSettings {
  visibility: Record<GroupId, boolean>;
  partVisibility: Record<PartId, boolean>;
  cutaway: boolean;
  heightMm: number;
}

export const groups: { id: GroupId; label: string }[] = [
  { id: 'F1', label: '一层' }, { id: 'F2', label: '二层' },
  { id: 'stairs', label: '楼梯' }, { id: 'roof', label: '屋顶' },
];
const partKinds: { id: PartKind; label: string }[] = [
  { id: 'floor_slab', label: '楼板' },
  { id: 'external_walls', label: '外墙' },
  { id: 'partition_walls', label: '内隔墙' },
  { id: 'doors', label: '门' },
  { id: 'windows', label: '窗' },
  { id: 'storage_fixtures', label: '收纳柜' },
];
export const parts: { id: PartId; group: FloorId; label: string }[] = (['F1', 'F2'] as const)
  .flatMap(group => partKinds.map(kind => ({ id: `${group}:${kind.id}` as PartId, group, label: kind.label })));

function allPartVisibility(visible: boolean): Record<PartId, boolean> {
  return Object.fromEntries(parts.map(part => [part.id, visible])) as Record<PartId, boolean>;
}

export function isPartVisible(s: ModelSettings, id: PartId): boolean {
  const part = parts.find(part => part.id === id);
  return !!part && s.visibility[part.group] && s.partVisibility[id];
}

export function groupVisibilityState(s: ModelSettings, id: GroupId): 'all' | 'some' | 'none' {
  if (!s.visibility[id]) return 'none';
  const children = parts.filter(part => part.group === id);
  if (children.length === 0) return 'all';
  const count = children.filter(part => s.partVisibility[part.id]).length;
  return count === children.length ? 'all' : count === 0 ? 'none' : 'some';
}

export function setGroupVisible(s: ModelSettings, id: GroupId, visible: boolean): ModelSettings {
  const partVisibility = { ...s.partVisibility };
  if (visible) {
    for (const part of parts) if (part.group === id) partVisibility[part.id] = true;
  }
  return { ...s, visibility: { ...s.visibility, [id]: visible }, partVisibility };
}

export function setPartVisible(s: ModelSettings, id: PartId, visible: boolean): ModelSettings {
  const part = parts.find(part => part.id === id);
  if (!part) return s;
  return {
    ...s,
    visibility: { ...s.visibility, ...(visible ? { [part.group]: true } : {}) },
    partVisibility: { ...s.partVisibility, [id]: visible },
  };
}

export function isolatePart(s: ModelSettings, id: ModelPartId): ModelSettings {
  const part = parts.find(part => part.id === id);
  const group = part?.group ?? id as GroupId;
  if (!groups.some(item => item.id === group)) return s;
  const partVisibility = allPartVisibility(false);
  for (const item of parts) {
    if (part ? item.id === part.id : item.group === group) partVisibility[item.id] = true;
  }
  return {
    ...s,
    visibility: Object.fromEntries(groups.map(item => [item.id, item.id === group])) as Record<GroupId, boolean>,
    partVisibility,
    cutaway: false,
  };
}

export function anyVisible(s: ModelSettings): boolean {
  return groups.some(group => groupVisibilityState(s, group.id) !== 'none');
}
export const presets: { id: PresetId; label: string; visibility: Record<GroupId, boolean> }[] = [
  { id: 'exterior', label: '完整外观', visibility: { F1: true, F2: true, stairs: true, roof: true } },
  { id: 'first', label: '一层内部', visibility: { F1: true, F2: false, stairs: true, roof: false } },
  { id: 'second', label: '二层内部', visibility: { F1: false, F2: true, stairs: true, roof: false } },
];

export function settingsForPreset(id: PresetId): ModelSettings {
  const preset = presets.find(x => x.id === id);
  if (!preset) throw new Error(`Unknown view preset: ${id}`);
  return { visibility: { ...preset.visibility }, partVisibility: allPartVisibility(true), cutaway: false, heightMm: 4200 };
}
export function activePreset(s: ModelSettings): PresetId | undefined {
  if (s.cutaway || parts.some(part => !s.partVisibility[part.id])) return undefined;
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
