import { useEffect, useRef, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { ChevronDown, ChevronRight, Scan } from 'lucide-react';
import { groupVisibilityState, isolatePart, isPartVisible, setGroupVisible, setPartVisible } from './model-state';
import type { FloorId, GroupId, ModelPartId, ModelSettings, PartKind } from './model-state';
import { useModel } from './ModelContext';
import { format } from './localization';

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
  const { copy, layout } = useModel();
  const ref = useRef<HTMLInputElement>(null);
  const state = groupVisibilityState(settings, id, layout);
  useEffect(() => { if (ref.current) ref.current.indeterminate = state === 'some'; }, [state]);
  return <input ref={ref} className="tree-checkbox" type="checkbox" aria-label={format(copy.tree.show, { label })}
    checked={state === 'all'} disabled={!ready} onChange={event => onChange(event.target.checked)} />;
}

export default function PartTree({ settings, setSettings, ready, selectedPart, onSelectPart }: Props) {
  const { copy, layout } = useModel();
  const [expanded, setExpanded] = useState<Record<FloorId, boolean>>({ F1: true, F2: false, attic: false });
  useEffect(() => {
    const group = layout.parts.find(part => part.id === selectedPart)?.group
      ?? (selectedPart === 'F1' || selectedPart === 'F2' || selectedPart === 'attic' ? selectedPart : undefined);
    if (group) setExpanded(s => s[group] ? s : { ...s, [group]: true });
  }, [selectedPart, layout]);
  const isolate = (id: ModelPartId) => {
    setSettings(s => isolatePart(s, id, layout));
    onSelectPart?.(id, true);
  };
  return <div className="part-tree">
    {layout.groups.map(group => {
      const label = copy.groups[group.id];
      const children = layout.parts.filter(part => part.group === group.id);
      const floorId = group.id as FloorId;
      return <div key={group.id} className="part-group">
        <div className="part-group-row">
          {children.length > 0 ? <button type="button" className="part-expand"
            aria-label={format(expanded[floorId] ? copy.tree.collapse : copy.tree.expand, { label })}
            aria-expanded={expanded[floorId]} aria-controls={`parts-${group.id}`}
            onClick={() => setExpanded(s => ({ ...s, [floorId]: !s[floorId] }))}>
            {expanded[floorId] ? <ChevronDown size={16} aria-hidden="true" /> : <ChevronRight size={16} aria-hidden="true" />}
          </button> : <span className="part-expand" aria-hidden="true" />}
          <GroupCheckbox settings={settings} id={group.id} label={label} ready={ready}
            onChange={checked => setSettings(s => setGroupVisible(s, group.id, checked, layout))} />
          <button type="button" className={selectedPart === group.id ? 'part-select selected' : 'part-select'}
            disabled={!ready} aria-label={format(copy.tree.highlight, { label })} aria-pressed={selectedPart === group.id}
            onClick={() => onSelectPart?.(group.id)}><span>{label}</span><Scan size={13} aria-hidden="true" /></button>
          <button type="button" className="part-isolate" disabled={!ready}
            aria-label={format(copy.tree.isolate, { label })} onClick={() => isolate(group.id)}>{copy.tree.alone}</button>
        </div>
        {children.length > 0 && expanded[floorId] ? <div id={`parts-${group.id}`} className="part-children"
          role="group" aria-label={format(copy.tree.region, { label })}>
          {children.map(part => {
            const partLabel = copy.partKinds[part.id.split(':')[1] as PartKind];
            const fullLabel = `${label} · ${partLabel}`;
            return <div key={part.id} className="part-child-row">
            <input className="tree-checkbox" type="checkbox" aria-label={format(copy.tree.show, { label: fullLabel })}
              checked={isPartVisible(settings, part.id, layout)} disabled={!ready}
              onChange={event => setSettings(s => setPartVisible(s, part.id, event.target.checked, layout))} />
            <button type="button" className={selectedPart === part.id ? 'part-select selected' : 'part-select'}
              disabled={!ready} aria-label={format(copy.tree.highlight, { label: fullLabel })} aria-pressed={selectedPart === part.id}
              onClick={() => onSelectPart?.(part.id)}><span>{partLabel}</span><Scan size={13} aria-hidden="true" /></button>
            <button type="button" className="part-isolate" disabled={!ready}
              aria-label={format(copy.tree.isolate, { label: fullLabel })} onClick={() => isolate(part.id)}>{copy.tree.alone}</button>
          </div>; })}
        </div> : null}
      </div>;
    })}
    <p className="part-tree-help">{copy.tree.help}</p>
  </div>;
}
