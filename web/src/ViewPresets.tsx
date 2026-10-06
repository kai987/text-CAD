import type { CSSProperties, Dispatch, SetStateAction } from 'react';
import { activePreset, settingsForPreset } from './model-state';
import type { ModelSettings, PresetId } from './model-state';
import { useModel } from './ModelContext';

interface Props {
  settings: ModelSettings;
  setSettings: Dispatch<SetStateAction<ModelSettings>>;
  ready: boolean;
  onPreset: (id: PresetId) => void;
}

export default function ViewPresets({ settings, setSettings, ready, onPreset }: Props) {
  const { copy, layout } = useModel();
  const active = activePreset(settings, layout);
  return <>
    <div className={`view-presets${layout.presets.length === 4 ? ' four-presets' : ''}`}
      style={{ '--preset-columns': layout.presets.length } as CSSProperties} role="group" aria-label={copy.presets.region}>
      {layout.presets.map(p => <button key={p.id} type="button" disabled={!ready}
        className={active === p.id ? 'preset selected' : 'preset'}
        aria-pressed={active === p.id} onClick={() => {
          setSettings(previous => settingsForPreset(p.id, layout, previous)); onPreset(p.id);
        }}>{copy.presets[p.id]}</button>)}
    </div>
    {layout.id === 'house' && active === 'attic' ? <p className="attic-view-note">{copy.model.atticNote}</p> : null}
  </>;
}
