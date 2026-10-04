import { useEffect, useRef, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { ChevronDown, ChevronRight, Scan } from 'lucide-react';
import { groups, groupVisibilityState, isolatePart, isPartVisible, parts, setGroupVisible, setPartVisible } from './model-state';
import type { FloorId, GroupId, ModelPartId, ModelSettings } from './model-state';

interface Props {
  settings: ModelSettings;
  setSettings: Dispatch<SetStateAction<ModelSettings>>;
  ready: boolean;
  selectedPart?: ModelPartId | null;
  onSelectPart?: (id: ModelPartId, fit?: boolean) => void;
}

interface GroupCheckboxProps {
  settings: ModelSettings;
  id: GroupId;
  label: string;
  ready: boolean;
  onChange: (checked: boolean) => void;
}

function GroupCheckbox({ settings, id, label, ready, onChange }: GroupCheckboxProps) {
  const ref = useRef<HTMLInputElement>(null);
  const state = groupVisibilityState(settings, id);
  useEffect(() => { if (ref.current) ref.current.indeterminate = state === 'some'; }, [state]);
  return <input ref={ref} className="tree-checkbox" type="checkbox" aria-label={`显示${label}`}
    checked={state === 'all'} disabled={!ready} onChange={event => onChange(event.target.checked)} />;
}

export default function PartTree({ settings, setSettings, ready, selectedPart, onSelectPart }: Props) {
  const [expanded, setExpanded] = useState<Record<FloorId, boolean>>({ F1: true, F2: false });
  useEffect(() => {
    const group = parts.find(part => part.id === selectedPart)?.group
      ?? (selectedPart === 'F1' || selectedPart === 'F2' ? selectedPart : undefined);
    if (group) setExpanded(s => s[group] ? s : { ...s, [group]: true });
  }, [selectedPart]);
  const isolate = (id: ModelPartId) => {
    setSettings(s => isolatePart(s, id));
    onSelectPart?.(id, true);
  };
  return <div className="part-tree">
    {groups.map(group => {
      const children = parts.filter(part => part.group === group.id);
      const floorId = group.id as FloorId;
      return <div key={group.id} className="part-group">
        <div className="part-group-row">
          {children.length > 0 ? <button type="button" className="part-expand"
            aria-label={`${expanded[floorId] ? '收起' : '展开'}${group.label}部件`}
            aria-expanded={expanded[floorId]} aria-controls={`parts-${group.id}`}
            onClick={() => setExpanded(s => ({ ...s, [floorId]: !s[floorId] }))}>
            {expanded[floorId] ? <ChevronDown size={16} aria-hidden="true" /> : <ChevronRight size={16} aria-hidden="true" />}
          </button> : <span className="part-expand" aria-hidden="true" />}
          <GroupCheckbox settings={settings} id={group.id} label={group.label} ready={ready}
            onChange={checked => setSettings(s => setGroupVisible(s, group.id, checked))} />
          <button type="button" className={selectedPart === group.id ? 'part-select selected' : 'part-select'}
            disabled={!ready} aria-label={`高亮${group.label}`} aria-pressed={selectedPart === group.id}
            onClick={() => onSelectPart?.(group.id)}><span>{group.label}</span><Scan size={13} aria-hidden="true" /></button>
          <button type="button" className="part-isolate" disabled={!ready}
            aria-label={`单独查看${group.label}`} onClick={() => isolate(group.id)}>单独</button>
        </div>
        {children.length > 0 && expanded[floorId] ? <div id={`parts-${group.id}`} className="part-children"
          role="group" aria-label={`${group.label}部件`}>
          {children.map(part => <div key={part.id} className="part-child-row">
            <input className="tree-checkbox" type="checkbox" aria-label={`显示${group.label}${part.label}`}
              checked={isPartVisible(settings, part.id)} disabled={!ready}
              onChange={event => setSettings(s => setPartVisible(s, part.id, event.target.checked))} />
            <button type="button" className={selectedPart === part.id ? 'part-select selected' : 'part-select'}
              disabled={!ready} aria-label={`高亮${group.label}${part.label}`} aria-pressed={selectedPart === part.id}
              onClick={() => onSelectPart?.(part.id)}><span>{part.label}</span><Scan size={13} aria-hidden="true" /></button>
            <button type="button" className="part-isolate" disabled={!ready}
              aria-label={`单独查看${group.label}${part.label}`} onClick={() => isolate(part.id)}>单独</button>
          </div>)}
        </div> : null}
      </div>;
    })}
    <p className="part-tree-help">展开楼层可查看分类；点击名称高亮，使用“单独”查看部件。顶部视图按钮可恢复显示。</p>
  </div>;
}
