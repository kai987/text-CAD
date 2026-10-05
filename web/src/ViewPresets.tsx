import type { Dispatch, SetStateAction } from 'react';
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
  return <div className="view-presets" style={{ gridTemplateColumns: `repeat(${layout.presets.length}, minmax(0, 1fr))` }} role="group" aria-label={copy.presets.region}>
    {layout.presets.map(p => <button key={p.id} type="button" disabled={!ready}
      className={active === p.id ? 'preset selected' : 'preset'}
      aria-pressed={active === p.id} onClick={() => {
        setSettings(settingsForPreset(p.id, layout)); onPreset(p.id);
      }}>{copy.presets[p.id]}</button>)}
  </div>;
}
